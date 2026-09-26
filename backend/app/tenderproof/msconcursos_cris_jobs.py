"""Reviewed rows for the preserved CRIS 02/2026 edital; never infer allowances."""
from app.tenderproof.contracts import ExtractedField, FieldState

SHA = 'a7b4632d830fe713b4118b30c2678f3d10065c5a768d7194c523d870d1249505'
CARE = 'CUIDADOR.\nMunicipio de Tupã,\n(SP), no Setor de\nResidência\nTerapêutica.\n01\nEnsino Médio.\nR$ 1.726,52\n+\n20% (*)\n12x36.'
DOCTOR = 'MÉDICO – PSF.\nMunicipio de Tupã,\n(SP)\n01\nEnsino Superior - Curso de\nGraduação em Medicina, com\nregistro no respectivo Conselho\nde Classe – CRM.\nR$ 17.584,43. 40 horas\nsemanais.'
FEES = 'EMPREGOS. Taxa de Inscrição R$.\nNÍVEL MÉDIO. R$ 24,90\nNÍVEL SUPERIOR. R$ 25,93'

def extract_cris_jobs(artifact, pages, evidence, *, source, external_id):
    if source != 'msconcursos_open' or external_id != '48' or artifact.sha256 != SHA:
        return None
    selected = {page.page_number: page for page in pages}
    snippets = [(1, CARE), (1, DOCTOR), (3, FEES)]
    if any(number not in selected or selected[number].error or selected[number].truncated
           or snippet not in selected[number].text for number, snippet in snippets):
        return ExtractedField(field_name='cargos', state=FieldState.FAILED,
            reason='Linhas conferidas do CRIS não reproduzidas integralmente; revisão necessária.')
    jobs = [
        {'nome': 'Cuidador', 'vagas_imediatas': 1, 'cadastro_reserva': None,
         'remuneracao': '1726.52', 'moeda': 'BRL', 'jornada': '12x36',
         'requisitos': 'Ensino Médio.', 'taxa_inscricao': '24.90'},
        {'nome': 'Médico – PSF', 'vagas_imediatas': 1, 'cadastro_reserva': None,
         'remuneracao': '17584.43', 'moeda': 'BRL', 'jornada': '40 horas semanais',
         'requisitos': 'Ensino Superior - Curso de Graduação em Medicina, com registro no respectivo Conselho de Classe – CRM.',
         'taxa_inscricao': '25.93'},
    ]
    return ExtractedField(field_name='cargos', state=FieldState.SUPPORTED, value=jobs,
        reason='Vencimentos básicos da tabela. O adicional de 20% (*) do Cuidador não foi somado: condições não esclarecidas na tabela. Quantidade de CR não determinada.',
        evidence=[evidence(artifact=artifact, page=selected[number], snippet=snippet) for number, snippet in snippets])
