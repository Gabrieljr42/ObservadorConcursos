import pytest

from app.tenderproof.facepe_listing import (
    SAD_ROOT, parse_sad_listing, parse_drive_rows, download_url_from_view,
    validate_listing_url, folder_identity,
)

FOLDER = 'https://drive.google.com/drive/folders/abcdefghij1234?usp=sharing'


def test_sad_discovers_new_article_ids_and_scopes_cards_to_facepe():
    next_url = SAD_ROOT + '/64-concursos-e-selecoes-simplificadas/98765-selecoes-simplificadas-andamento'
    html = f'''<a href="{next_url}">Seleções</a><div itemprop="articleBody">
    <p><span><strong>Outra agência</strong></span></p><p><a href="https://other.test">Outro</a></p>
    <p><span><strong>Fundação FACEPE</strong></span></p><hr>
    <p><style>.x {{color:red}}</style><div><a href="{FOLDER}">Analistas 2027</a></div></p>
    <p><span><strong>Agência seguinte</strong></span></p><p><a href="https://other.test">Outro</a></p>
    </div>'''
    result = parse_sad_listing(html, SAD_ROOT)
    assert result['next_urls'] == [next_url]
    assert [(x['folder_id'], x['title_observed']) for x in result['items']] == [('abcdefghij1234', 'Analistas 2027')]
    assert not result['scope_complete']


@pytest.mark.parametrize('url', [
    SAD_ROOT + '?redirect=1', SAD_ROOT.replace('www.sad.pe.gov.br', 'www.sad.pe.gov.br.evil.test'),
    SAD_ROOT.replace('https:', 'http:'), SAD_ROOT + '/../../private',
])
def test_sad_rejects_unrelated_destinations(url):
    with pytest.raises(ValueError):
        validate_listing_url(url)


@pytest.mark.parametrize('url', [FOLDER + '&id=another', FOLDER.replace('drive.google.com', 'user@drive.google.com'), FOLDER + '#x'])
def test_folder_url_is_strict(url):
    with pytest.raises(ValueError):
        folder_identity(url)


def table(count=1, identity='documentabcdef', index=1):
    return f'''<table role="grid" aria-rowcount="{count}"><tr data-id="{identity}" data-target="doc" aria-rowindex="{index}">
    <td data-column-id="16"><svg><title>PDF</title></svg><strong>Errata - Reabertura.pdf</strong></td></tr></table>'''


def test_drive_preserves_observed_files_without_claiming_full_folder():
    result = parse_drive_rows(table(), FOLDER)
    assert result['items'][0]['view_url'] == 'https://drive.google.com/file/d/documentabcdef/view'
    assert not result['scope_complete']


@pytest.mark.parametrize('html', [table(2), table(index=2), table(identity='../secret'), '<html>Fazer login</html>'])
def test_incomplete_or_invalid_drive_is_not_empty(html):
    with pytest.raises(ValueError):
        parse_drive_rows(html, FOLDER)


def test_viewer_download_must_bind_observed_file_identity():
    html = r'"https://drive.usercontent.google.com/uc?id\u003ddocumentabcdef\u0026export\u003ddownload"'
    assert download_url_from_view(html, 'documentabcdef').endswith('id=documentabcdef&export=download')
    with pytest.raises(ValueError):
        download_url_from_view(html, 'differentabcdef')
