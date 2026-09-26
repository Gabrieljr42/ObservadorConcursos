"""Conservative canonical resolution; publication remains in the existing ledger."""
import re
import unicodedata
from sqlalchemy import select
from app.models import Concurso, Source
from app.tenderproof.publication_models import CanonicalIdentity

REQUIRED = ('titulo', 'orgao', 'edital_numero')


def norm(value):
    return ' '.join(str(value or '').casefold().split())


def explicit_modality(title):
    """Distinguish explicit selection families; absence/ambiguity proves nothing."""
    text = unicodedata.normalize('NFKD', norm(title)).encode('ascii', 'ignore').decode()
    families = [name for name, pattern in (
        ('concurso_publico', r'\bconcurso publico\b'),
        ('processo_seletivo', r'\bprocesso seletivo\b'),
    ) if re.search(pattern, text)]
    return families[0] if len(families) == 1 else None


def distinct_modalities(left, right):
    a, b = explicit_modality(left), explicit_modality(right)
    return bool(a and b and a != b)


def context(db, run, source_id=None):
    from app.tenderproof.publication import _error
    candidate = next((c for c in run.candidates if c.candidate_id == run.selected_candidate_id), None)
    sources = list(db.scalars(select(Source).where(Source.source_type == run.source)))
    if source_id is not None:
        sources = [s for s in sources if s.id == source_id]
    if not candidate or not candidate.external_id or len(sources) != 1:
        _error(422, 'TenderProof: candidato ou fonte ambígua; informe source_id correspondente')
    source = sources[0]
    values = {f.field_name: f.value for f in run.fields if f.field_name in REQUIRED}
    proxy = Concurso(source_id=source.id, external_id=candidate.external_id, banca=source.name,
                     link_pagina=candidate.detail_url_observed, **values)
    # Do not grant IMESO bucket fallback without a pre-existing canonical URL.
    return candidate, source, proxy


def keys(source, candidate, eligible, *, separate_modality=False):
    from app.tenderproof.publication import _hash
    result = [(_hash(['source_external', source.id, candidate.external_id]), 'source_external')]
    if eligible.get('orgao') and eligible.get('edital_numero'):
        parts = ['organization_notice', norm(eligible['orgao']), norm(eligible['edital_numero'])]
        reason = 'organization_notice'
        if separate_modality:
            # Keep the original identity claim intact. A second, explicitly
            # distinct family gets a scoped claim only after that claim exists.
            parts += [explicit_modality(eligible.get('titulo'))]
            reason = 'organization_notice_modality'
        result.append((_hash(parts), reason))
    return result


def resolve(db, run, store, target_id=None, source_id=None):
    from app.tenderproof.publication import _error, _revalidate, _same_url
    candidate, source, proxy = context(db, run, source_id)
    # Exact legacy target follows its historical validation rules.
    target = db.get(Concurso, target_id, populate_existing=True) if target_id else None
    if target_id and not target:
        _error(404, 'TenderProof: concurso alvo não encontrado')
    exact = list(db.scalars(select(Concurso).where(Concurso.source_id == source.id, Concurso.external_id == candidate.external_id).execution_options(populate_existing=True)))
    if len(exact) > 1:
        _error(409, 'TenderProof: identificador externo reutilizado ou duplicado; revisão de identidade necessária')
    if not target and exact:
        target = exact[0]
    direct = bool(target and target.source_id == source.id and target.external_id == candidate.external_id and _same_url(target.link_pagina, candidate.detail_url_observed))
    if target and exact and exact[0].id != target.id:
        _error(422, 'TenderProof: origem já identifica outro concurso; associação recusada')
    if target and target.source_id == source.id and not direct:
        _error(422, 'TenderProof: identificador ou URL incompatível; revisão de identidade necessária')
    eligible, blocked = _revalidate(run, target if direct else proxy, source, store)
    if target and (target.raw_data or {}).get('tenderproof', {}).get('amendments'):
        from app.models import ConcursoVersion
        from app.tenderproof.amendment import _same_value
        protected = set()
        for version in db.scalars(select(ConcursoVersion).where(
            ConcursoVersion.concurso_id == target.id, ConcursoVersion.change_type == 'amendment')):
            protected.update((version.changed_fields or {}).keys())
        for name in protected.intersection(eligible):
            if not _same_value(name, eligible[name], getattr(target, name)):
                eligible.pop(name)
                blocked[name] = 'Campo alterado por retificação aplicada; mudança exige nova revisão dos efeitos documentais'
    if direct and all(eligible.get(k) and getattr(target, k) and norm(eligible[k]) != norm(getattr(target, k)) for k in ('orgao', 'edital_numero')):
        _error(422, 'TenderProof: órgão e edital divergentes; possível reutilização de identificador')
    identity_keys = keys(source, candidate, eligible)
    if len(identity_keys) > 1:
        original = db.get(CanonicalIdentity, identity_keys[1][0])
        original_target = db.get(Concurso, original.concurso_id, populate_existing=True) if original else None
        if original_target and distinct_modalities(original_target.titulo, eligible.get('titulo')):
            identity_keys = keys(source, candidate, eligible, separate_modality=True)
    linked_ids = {row.concurso_id for key, _ in identity_keys if (row := db.get(CanonicalIdentity, key))}
    matches = list(db.scalars(select(Concurso).where(Concurso.orgao.is_not(None), Concurso.edital_numero.is_not(None))))
    possible = [c for c in matches if eligible.get('orgao') and eligible.get('edital_numero')
                and norm(c.orgao) == norm(eligible['orgao']) and norm(c.edital_numero) == norm(eligible['edital_numero'])
                and not distinct_modalities(c.titulo, eligible.get('titulo'))]
    if linked_ids and (not target or linked_ids != {target.id}):
        # A previously reviewed source association can be reused, a fingerprint alone cannot.
        external = db.get(CanonicalIdentity, identity_keys[0][0])
        if not target and external and linked_ids == {external.concurso_id}:
            target = db.get(Concurso, external.concurso_id)
        else:
            _error(409, 'TenderProof: possível concurso já cadastrado; selecione o alvo e revise a associação')
    if not target and possible:
        _error(409, 'TenderProof: órgão e edital já existem; selecione concurso_id para revisão, sem fusão automática')
    if target and distinct_modalities(target.titulo, eligible.get('titulo')):
        _error(422, 'TenderProof: modalidades distintas de seleção; associação recusada mesmo com órgão e edital iguais')
    if target and not direct:
        if not all(eligible.get(k) for k in ('orgao', 'edital_numero')) or any(norm(getattr(target, k)) != norm(eligible[k]) for k in ('orgao', 'edital_numero')):
            _error(422, 'TenderProof: associação exige órgão e número do edital comprovados e correspondentes')
    if not target and not all(eligible.get(k) for k in REQUIRED):
        _error(422, 'TenderProof: criação exige título, órgão e número do edital com evidência reproduzida')
    identity = {'source_id': source.id, 'external_id': candidate.external_id, 'detail_url': candidate.detail_url_observed,
                'reason': 'source_external_url' if direct else ('reviewed_organization_notice' if target else 'new_verified_identity'),
                'keys': [list(item) for item in identity_keys]}
    return target, source, proxy, eligible, blocked, identity


def bind(db, contest, identity, proposal):
    from app.tenderproof.publication import _error
    for key, reason in identity['keys']:
        existing = db.get(CanonicalIdentity, key)
        if existing and existing.concurso_id != contest.id:
            _error(409, 'TenderProof: identidade já associada a outro concurso; recomparação necessária')
        if not existing:
            db.add(CanonicalIdentity(key=key, concurso_id=contest.id, reason=reason, evidence=identity | {"proposal_id": proposal.id, "approved_by": proposal.approved_by,
                "document_sha256": proposal.payload["run"]["artifact"]["sha256"]}))
    db.flush()

