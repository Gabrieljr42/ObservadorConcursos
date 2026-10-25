"""An institute masthead must be corroborated, never inferred from body mentions."""
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import _extract_orgao


ISSUER = 'INSTITUTO DE PREVIDÊNCIA DOS SERVIDORES DO ESTADO DE MINAS GERAIS – IPSEMG'


def inputs(text, *, title='IPSEMG - Instituto de Previdência dos Servidores do Estado de Minas Gerais', page=1):
    candidate = DiscoveredCandidate(candidate_id='access_open-175', source='access_open', external_id='175',
        title_observed=title, detail_url_observed='https://access.selecao.net.br/informacoes/175/',
        observed_at='2026-10-25T19:50:04Z')
    artifact = Artifact(artifact_id='test-institute', sha256='a' * 64, byte_len=100,
        url_requested='https://anexos-r2.selecao.net.br/edital.pdf',
        url_final='https://anexos-r2.selecao.net.br/edital.pdf', content_type='application/pdf',
        downloaded_at='2026-10-25T19:50:27Z')
    return candidate, artifact, [PageText(artifact_id=artifact.artifact_id, page_number=page, text=text)]


def test_access_institute_issuer_from_corroborated_first_page_masthead():
    candidate, artifact, pages = inputs(ISSUER + '\nHOSPITAL GOVERNADOR ISRAEL PINHEIRO - HGIP\nPROCESSO SELETIVO DE RESIDÊNCIA MÉDICA\nEDITAL Nº 2/2026')
    field = _extract_orgao(candidate, artifact, pages)
    assert field.state.value == 'supported'
    assert field.value == ISSUER
    assert field.evidence[0].page_number == 1
    assert field.evidence[0].document_sha256 == artifact.sha256


def test_access_institute_issuer_stays_unknown_without_independent_corroboration():
    for text, options in [
        (ISSUER + '\nPROCESSO SELETIVO', {'title': 'Instituto de Outro Estado'}),
        (ISSUER + '\nPROCESSO SELETIVO', {'page': 2}),
        (ISSUER + '\nCONVÊNIO DE ATENDIMENTO', {}),
    ]:
        candidate, artifact, pages = inputs(text, **options)
        assert _extract_orgao(candidate, artifact, pages).state.value == 'unknown'
