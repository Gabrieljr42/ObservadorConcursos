import hashlib
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from app.tenderproof.contracts import Artifact, DocumentCandidate, SupplementaryDocument, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.fumarc_adapter import FumarcAdapter
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.supplementary_fields import supplement_fields

HEADER = 'CONSELHO REGIONAL DE ADMINISTRAÇÃO DO ESTADO NOVO\nAUTARQUIA FEDERAL\nCONCURSO PÚBLICO Nº 02/2027\n'
TABLE = ('Cargo Escolaridade/Requisitos Carga horária Vagas* Total de vagas Salário inicial da carreira AC PCD PN PI PQ\n'
         'Analista Ensino Superior completo. 200 horas/mês 1 - - - - 1 R$ 8.991,81\nLegenda: CR > Cadastro de Reserva.')


@pytest.mark.parametrize('mutation', ['none', 'hash', 'notice', 'organization'])
@pytest.mark.parametrize('fee_words', [None, 'cem', 'cento e vinte'])
def test_annex_requires_matching_identity_and_immutable_bytes(monkeypatch, mutation, fee_words):
    c = FumarcAdapter().candidate_from_url('https://www.fumarc.com.br/SitePages/Home.aspx?concurso=88')
    url = 'https://www.fumarc.com.br/Documentos%20Compartilhados/Novo/anexo.pdf'
    content = b'preserved PDF bytes'
    artifact = Artifact(artifact_id='annex', sha256=hashlib.sha256(content).hexdigest(), byte_len=len(content),
        url_requested=url, url_final=url, downloaded_at=datetime.now(timezone.utc))
    doc = DocumentCandidate(doc_id='annex', title='Anexo I - Quadro de cargos', kind='anexo',url_requested=url)
    extra = SupplementaryDocument(document=doc,artifact=artifact)
    main = artifact.model_copy(update={'artifact_id':'main'})
    main_text = HEADER
    if fee_words:
        main_text += ('O valor correspondente à Taxa de Inscrição para cada cargo será de:\n'
            'a) Nível Médio/Técnico: R$70,00 (setenta reais);\n'
            f'b) Nível Superior: R$100,00 ({fee_words} reais).\n2.2.2. Inscrições.')
    fields = extract_fields(candidate=c,artifact=main,pages=[PageText(artifact_id='main',page_number=1,text=main_text)])
    text = HEADER + TABLE
    if mutation == 'notice': text = text.replace('02/2027','03/2027')
    if mutation == 'organization': text = text.replace('ESTADO NOVO','OUTRO ESTADO')
    pages = [PageText(artifact_id='annex',page_number=1,text=text)]
    monkeypatch.setattr('app.tenderproof.supplementary_fields.extract_pages_isolated', lambda *a,**k:(pages,1,1,False,[]))
    store = SimpleNamespace(load_artifact_bytes=lambda a: content if mutation != 'hash' else b'changed')
    if mutation != 'none':
        with pytest.raises(ValueError): supplement_fields(c,fields,[extra],store,TenderProofSettings(),1)
    else:
        result = supplement_fields(c,fields,[extra],store,TenderProofSettings(),1)
        jobs = next(f for f in result if f.field_name=='cargos')
        assert jobs.state.value=='supported' and len(jobs.value)==1
        assert jobs.value[0]['taxa_inscricao'] == ('100.00' if fee_words == 'cem' else None)
        if fee_words == 'cem':
            assert any('Nível Superior' in e.snippet and e.artifact_id == 'main' for e in jobs.evidence)
        assert {e.artifact_id for e in jobs.evidence} == {'main','annex'}
        from app.tenderproof.publication import _reproduced_evidence
        artifacts = {'main': main, 'annex': artifact}
        assert all(_reproduced_evidence(e,jobs,artifacts) for e in jobs.evidence)
        e = jobs.evidence[0]
        for changes in ({'artifact_id':'main'}, {'document_sha256':'b'*64},
                        {'page_number':2}, {'snippet':'Invented salary'},
                        {'source_url':'https://www.fumarc.com.br/other.pdf'}):
            assert not _reproduced_evidence(e.model_copy(update=changes),jobs,artifacts)
