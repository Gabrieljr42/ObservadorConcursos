import pytest
from app.tenderproof.contracts import PageText, FieldState
from app.tenderproof.fields import extract_fields
from test_tenderproof_evidence import _artifact, _candidate


def notice(text, page=1):
    return next(f for f in extract_fields(candidate=_candidate(), artifact=_artifact(),
        pages=[PageText(artifact_id='art-ev', page_number=page, text=text)])
        if f.field_name == 'edital_numero')


@pytest.mark.parametrize('text,value', [
    ('EDITAL Nº 1 – FAPEAL, DE 7 DE MAIO DE 2026', '1/2026'),
    ('EDITAL N° 032 — ÓRGÃO/UF, DE 29 DE FEVEREIRO DE 2028', '032/2028'),
    ('EDITAL N. 4, DE 1º DE MARÇO DE 2030', '4/2030'),
])
def test_number_and_year_come_from_same_first_page_heading(text,value):
    f=notice(text)
    assert f.state==FieldState.SUPPORTED and f.value==value
    assert f.original_value==text
    assert f.evidence[0].snippet==text and f.evidence[0].page_number==1


@pytest.mark.parametrize('text,page', [
    ('EDITAL Nº 1 – FAPEAL, DE 31 DE FEVEREIRO DE 2026',1),
    ('EDITAL Nº 1 – FAPEAL\nPublicado em 7 de maio de 2026',1),
    ('Conforme EDITAL Nº 1 – FAPEAL, DE 7 DE MAIO DE 2026',1),
    ('EDITAL Nº 1 – FAPEAL, DE 7 DE MAIO DE 2026',2),
])
def test_references_missing_or_invalid_dates_do_not_supply_a_year(text,page):
    assert notice(text,page).state != FieldState.SUPPORTED


def test_two_principal_headings_are_a_conflict():
    f=notice('EDITAL Nº 1 – FAPEAL, DE 7 DE MAIO DE 2026\nEDITAL Nº 2/2026')
    assert f.state==FieldState.CONFLICT and f.value is None


def test_dated_principal_is_not_replaced_by_reference_to_older_notice():
    f=notice('EDITAL Nº 1 – FAPEAL, DE 7 DE MAIO DE 2026\nConforme edital 9/2025 anterior.')
    assert f.value=='1/2026'
