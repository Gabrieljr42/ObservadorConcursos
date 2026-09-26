"""Bounded OOXML cell inventory. Never evaluates formulas or follows links."""
import hashlib,io,json,posixpath,re,sys,zipfile
from xml.etree import ElementTree as ET

VERSION='tenderproof-xlsx-cells/2'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
P='{http://schemas.openxmlformats.org/package/2006/relationships}'
MAX_INPUT=8*1024*1024
MAX_OUTPUT=4*1024*1024


def extract_xlsx(content):
    if len(content)>MAX_INPUT:raise ValueError('XLSX input limit')
    pending=[];sheets=[];cell_count=0
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries=archive.infolist();names=[e.filename for e in entries]
        if len(entries)>1000 or len(set(names))!=len(names) or sum(e.file_size for e in entries)>40*1024*1024 or any(e.flag_bits&1 for e in entries):
            raise ValueError('XLSX package bounds or duplicate/encrypted entries')
        def xml(name):
            if name not in names or archive.getinfo(name).file_size>8*1024*1024:raise ValueError('XLSX XML part bounds')
            raw=archive.read(name).decode('utf-8-sig')
            if re.search(r'<!DOCTYPE|<!ENTITY',raw,re.I):raise ValueError('XLSX XML declarations forbidden')
            return ET.fromstring(raw)
        workbook=xml('xl/workbook.xml');relationships=xml('xl/_rels/workbook.xml.rels');mapping={}
        for rel in relationships:
            identity=rel.get('Id')
            if not identity or identity in mapping:raise ValueError('Ambiguous XLSX relationship')
            mapping[identity]=rel
        strings=[]
        if 'xl/sharedStrings.xml' in names:
            for si in xml('xl/sharedStrings.xml').findall(S+'si'):
                strings.append(''.join((child.text or '') if child.tag==S+'t' else ''.join(t.text or '' for t in child.findall(S+'t')) if child.tag==S+'r' else '' for child in si))
                if len(strings)>20000:raise ValueError('XLSX string count limit')
        seen=set()
        for sheet in workbook.findall(S+'sheets/'+S+'sheet'):
            name=sheet.get('name');rel=mapping.get(sheet.get(R+'id'))
            if not name or name in seen or rel is None or rel.get('TargetMode')=='External' or not rel.get('Type','').endswith('/worksheet'):
                raise ValueError('XLSX sheet identity invalid')
            seen.add(name)
            if len(seen)>50:raise ValueError('XLSX sheet limit')
            target=rel.get('Target','');part=posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/'+target)
            if not re.fullmatch(r'xl/worksheets/[A-Za-z0-9_-]+\.xml',part):raise ValueError('XLSX sheet part outside workbook')
            root=xml(part);cells=[];coordinates=set()
            for cell in root.findall(S+'sheetData/'+S+'row/'+S+'c'):
                address=cell.get('r','')
                if not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}',address) or address in coordinates:raise ValueError('XLSX cell coordinate invalid')
                coordinates.add(address);cell_count+=1
                if cell_count>20000:raise ValueError('XLSX cell count limit')
                kind=cell.get('t','n');value=cell.findtext(S+'v');formula=cell.find(S+'f')
                if kind=='s':
                    if value is None or not value.isdigit() or int(value)>=len(strings):raise ValueError('XLSX shared string reference invalid')
                    text=strings[int(value)]
                elif kind=='inlineStr':text=''.join(t.text or '' for t in cell.findall('.//'+S+'t'))
                elif kind in ('n','b','str','e','d'):text=value
                else:raise ValueError('Unsupported XLSX cell type')
                if text is None and formula is None:continue
                item={'coordinate':address,'value':text,'type':kind,'style_index':cell.get('s')}
                if formula is not None:
                    item['formula']=formula.text or '';item['formula_attributes']=dict(formula.attrib)
                    pending.append({'sheet':name,'cell':address,'feature':'formula_not_evaluated'})
                cells.append(item)
            for tag in ('drawing','legacyDrawing','oleObjects','hyperlinks','mergeCells'):
                if root.find(S+tag) is not None:pending.append({'sheet':name,'feature':tag})
            rel_part=posixpath.dirname(part)+'/_rels/'+posixpath.basename(part)+'.rels'
            sheet_rels={}
            if rel_part in names:
                for relationship in xml(rel_part):
                    identity=relationship.get('Id')
                    if not identity or identity in sheet_rels:raise ValueError('Ambiguous worksheet relationship')
                    sheet_rels[identity]=dict(relationship.attrib)
            hyperlinks=[]
            for link in root.findall(S+'hyperlinks/'+S+'hyperlink'):
                reference=link.get('ref','')
                if not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}(?::[A-Z]{1,3}[1-9][0-9]{0,6})?',reference):raise ValueError('Hyperlink cell reference invalid')
                hyperlinks.append({'reference':reference,'display':link.get('display'),'location':link.get('location'),
                    'relationship_id':link.get(R+'id'),'relationship':sheet_rels.get(link.get(R+'id')),'followed':False})
            merges=[node.get('ref','') for node in root.findall(S+'mergeCells/'+S+'mergeCell')]
            if any(not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}:[A-Z]{1,3}[1-9][0-9]{0,6}',reference) for reference in merges):raise ValueError('Merged cell reference invalid')
            sheets.append({'name':name,'part':part,'visibility':sheet.get('state','visible'),'cells':cells,
                'hyperlinks':hyperlinks,'merged_ranges':merges})
        if not sheets:raise ValueError('XLSX has no worksheets')
        for name in names:
            if name.startswith(('xl/externalLinks/','xl/embeddings/','xl/media/')) or name.lower().endswith('vbaproject.bin'):
                pending.append({'part':name,'feature':'non_cell_content_not_executed'})
    result={'input_sha256':hashlib.sha256(content).hexdigest(),'extractor_version':VERSION,'method':'ooxml_cells','sheets':sheets,'pending_features':pending,'formulas_evaluated':False,'review_required':True,'published':False}
    if len(json.dumps(result,ensure_ascii=False).encode())>MAX_OUTPUT:raise ValueError('XLSX output limit')
    return result


if __name__=='__main__':
    try:
        result=extract_xlsx(sys.stdin.buffer.read(MAX_INPUT+1))
        sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False).encode())
    except Exception as exc:
        sys.stdout.write(json.dumps({'error':type(exc).__name__+': '+str(exc)[:200]}));sys.exit(1)
