import json
import pytest
from app.tenderproof.batch60_major_adapters import CebraspeAdapter


def event():
    return {'eventoURL':'NOVO_27','eventoTipo':'concursos','eventoNomeAbreviado':'Órgão Novo',
        'arquivosEdital':[
            {'tipoExtensaoArquivo':'_.pdf','isGuid':False,'nomeArquivo':'latest.pdf','descricaoArquivo':'Edital nº 17 – Inclusão de candidato sub judice.'},
            {'tipoExtensaoArquivo':'_pdf','isGuid':False,'nomeArquivo':'OPENING.PDF','descricaoArquivo':'Edital nº 1 - Abertura'},
            {'tipoExtensaoArquivo':'_pdf','isGuid':False,'nomeArquivo':'change.pdf','descricaoArquivo':'Edital nº 2 - Retificação do Edital nº 1'}],
        'arquivosGabarito':[]}


def documents(data):
    adapter=CebraspeAdapter()
    candidate=adapter.candidate_from_url(adapter.api+'/NOVO_27','Órgão Novo')
    return adapter,adapter.documents(json.dumps(data),candidate)


def test_both_public_pdf_spellings_are_read_and_original_is_chosen():
    adapter,docs=documents(event())
    assert len(docs)==3
    assert [d.kind for d in docs]==['outro','edital','retificacao']
    assert adapter.choose_document(docs).url_requested.endswith('/OPENING.PDF')


def test_unrecognized_pdf_type_cannot_silently_omit_the_opening():
    data=event();data['arquivosEdital'][1]['tipoExtensaoArquivo']='unknown'
    with pytest.raises(ValueError):documents(data)


@pytest.mark.parametrize('field,value',[('nomeArquivo','../OTHER/opening.pdf'),('isGuid',True),('nomeArquivo','https://foreign.test/opening.pdf')])
def test_new_spelling_keeps_identity_and_destination_guards(field,value):
    data=event();data['arquivosEdital'][1][field]=value
    with pytest.raises(ValueError):documents(data)


@pytest.mark.parametrize('title', [
    'Edital nº 17 – Inclusão de candidato sub judice.',
    'EDITAL DE PRORROGAÇÃO',
    'Edital nº 18 - Prorrogação das inscrições',
    'Edital nº 19 - Ampliação do número de vagas',
    'Edital nº 20 - Redução de vagas',
])
@pytest.mark.parametrize('kind', ['edital', 'consolidado'])
def test_old_saved_act_or_update_is_rejected_despite_principal_kind(title, kind):
    from app.tenderproof.validation import validate_identity
    from app.tenderproof.contracts import PageText
    adapter=CebraspeAdapter()
    candidate=adapter.candidate_from_url(adapter.api+'/NOVO_27','Órgão Novo')
    result=validate_identity(candidate=candidate,pages=[PageText(artifact_id='doc',page_number=1,text='EDITAL Nº 17\nÓrgão Novo')],
        document_title=title,
        document_url='https://cdn.cebraspe.org.br/concursos/NOVO_27/arquivos/latest.pdf',document_kind=kind)
    assert result.status.value=='non_edital'
