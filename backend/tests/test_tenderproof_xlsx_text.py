import io,zipfile
import pytest
from app.tenderproof.xlsx_text import extract_xlsx,S,R,P
from app.tenderproof.xlsx_processing import extract_xlsx_isolated


def workbook(sheet=None,strings=None,target='worksheets/sheet1.xml',extra=None):
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{S[1:-1]}" xmlns:r="{R[1:-1]}"><sheets><sheet name="Evidence" sheetId="1" r:id="s1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',f'<Relationships xmlns="{P[1:-1]}"><Relationship Id="s1" Type="{R[1:-1]}/worksheet" Target="{target}"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml',sheet or f'<worksheet xmlns="{S[1:-1]}"><sheetData><row r="2"><c r="I2" t="s"><v>0</v></c><c r="J2"><f>WEBSERVICE("https://example.invalid")</f><v>7</v></c></row></sheetData></worksheet>')
        z.writestr('xl/sharedStrings.xml',strings or f'<sst xmlns="{S[1:-1]}"><si><t>Academic places</t></si></sst>')
        if extra:z.writestr(*extra)
    return data.getvalue()


def test_coordinates_formula_and_isolated_output_preserve_raw_evidence():
    data=workbook();result=extract_xlsx_isolated(data)
    assert result==extract_xlsx(data)
    cells=result['sheets'][0]['cells']
    assert cells[0]['coordinate']=='I2' and cells[0]['value']=='Academic places'
    assert cells[1]['value']=='7' and cells[1]['formula'].startswith('WEBSERVICE')
    assert result['pending_features'][0]['feature']=='formula_not_evaluated'
    assert result['formulas_evaluated'] is False and result['review_required'] is True


def test_xml_declarations_duplicate_cells_and_bad_references_rejected():
    with pytest.raises(ValueError):extract_xlsx(workbook(strings='<!DOCTYPE sst [<!ENTITY x "injected">]><sst/>'))
    with pytest.raises(ValueError):extract_xlsx(workbook(sheet=f'<worksheet xmlns="{S[1:-1]}"><sheetData><row><c r="I2"/><c r="I2"/></row></sheetData></worksheet>'))
    with pytest.raises(ValueError):extract_xlsx(workbook(strings=f'<sst xmlns="{S[1:-1]}"/>'))


def test_external_parts_and_embedded_content_are_not_silently_used():
    with pytest.raises(ValueError):extract_xlsx(workbook(target='https://example.invalid/sheet.xml'))
    with pytest.raises(ValueError):extract_xlsx(workbook(target='../../outside.xml'))
    result=extract_xlsx(workbook(extra=('xl/embeddings/unknown.bin',b'not executed')))
    assert any(x['feature']=='non_cell_content_not_executed' for x in result['pending_features'])


def test_hyperlink_targets_missing_targets_and_merged_ranges_keep_locations():
    sheet=f'<worksheet xmlns="{S[1:-1]}" xmlns:r="{R[1:-1]}"><sheetData/><mergeCells><mergeCell ref="I2:P2"/></mergeCells><hyperlinks><hyperlink ref="J6" r:id="h1"/><hyperlink ref="N6" display="broken link"/></hyperlinks></worksheet>'
    rels=f'<Relationships xmlns="{P[1:-1]}"><Relationship Id="h1" Target="https://example.invalid/programme" TargetMode="External" Type="{R[1:-1]}/hyperlink"/></Relationships>'
    result=extract_xlsx(workbook(sheet=sheet,extra=('xl/worksheets/_rels/sheet1.xml.rels',rels)))['sheets'][0]
    assert result['merged_ranges']==['I2:P2']
    assert result['hyperlinks'][0]['relationship']['Target']=='https://example.invalid/programme'
    assert result['hyperlinks'][0]['followed'] is False
    assert result['hyperlinks'][1]['relationship'] is None and result['hyperlinks'][1]['reference']=='N6'
