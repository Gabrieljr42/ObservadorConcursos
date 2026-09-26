"""Read FUNCAP annual document groups without merging reused solicitation IDs."""
import re
from datetime import datetime
from urllib.parse import urlsplit,urljoin,parse_qs,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded

LISTING='https://montenegro.funcap.ce.gov.br/sugba/editais-site-wordpress/'


def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if (p.scheme!='https' or p.netloc!='montenegro.funcap.ce.gov.br' or p.query or p.fragment
            or not path.startswith('/sugba/edital/') or not re.search(r'\.(pdf|docx?|xlsx?|pptx|mp4|zip|odt)$',path,re.I)
            or any(x in ('.','..') for x in path.split('/')) or '\\' in path or '%' in path):
        raise ValueError('arquivo fora do contrato FUNCAP')
    return 'https://montenegro.funcap.ce.gov.br'+quote(path,safe='/')


def parse_panels(html):
    soup=BeautifulSoup(html,'html.parser');boxes=soup.select('.editais-conteudo .box')
    if not boxes:raise ValueError('seções FUNCAP não identificadas')
    panels=[];sections=[]
    for box in boxes:
        heading=box.select_one('.title h5')
        if heading is None:raise ValueError('seção sem rótulo')
        status=heading.get_text(' ',strip=True);count=0;current=None
        for row in box.select('tr.linha-titulo-edital,tr.linha-cabecalho-edital,tr.linha-documento-edital'):
            classes=row.get('class',[])
            if 'linha-titulo-edital' in classes:
                title=row.select_one('h4');links=row.select('a[href]')
                if title is None or len(links)!=1:raise ValueError('identidade de grupo FUNCAP ausente')
                p=urlsplit(links[0]['href']);q=parse_qs(p.query)
                if (p.scheme not in ('http','https') or p.netloc!='montenegro.funcap.ce.gov.br'
                        or p.path!='/sugba/index.php' or p.fragment or set(q)!={'cnpj','id_solicitacao'}
                        or len(q['id_solicitacao'])!=1 or not re.fullmatch(r'[1-9]\d*',q['id_solicitacao'][0])
                        or len(q['cnpj'])!=1 or not re.fullmatch(r'\d{14}',q['cnpj'][0])):
                    raise ValueError('referência de consulta FUNCAP divergente')
                year=row.find_parent(class_='bloco-ano-edital')
                current={'title':title.get_text(' ',strip=True),'solicitation_id':q['id_solicitacao'][0],
                    'consultation_url_observed':links[0]['href'],'status_observed':status,
                    'year_group':year.get('id') if year else None,'documents':[],
                    'identity_review_required':True,'scope_review_required':True}
                panels.append(current);count+=1
            elif 'linha-documento-edital' in classes:
                if current is None:raise ValueError('documento anterior à identidade do grupo')
                links=row.select('a[href]');cells=row.find_all('td',recursive=False)
                if len(links)!=1 or len(cells)!=2:raise ValueError('linha documental não interpretada')
                label=links[0].get_text(' ',strip=True);date=cells[1].get_text(' ',strip=True)
                target=document_url(urljoin(LISTING,links[0]['href']))
                if not label:raise ValueError('documento sem rótulo')
                parsed_date=datetime.strptime(date,'%d/%m/%Y').date().isoformat()
                text=folded(label).lstrip('- ')
                kind='outro'
                if '/resultados/' in target or re.search(r'resultado|homologacao|classific',text):kind='outro'
                elif re.search(r'prorrog',text):kind='prorrogacao'
                elif re.search(r'retificad|consolidad',text):kind='consolidado'
                elif re.search(r'adendo|retifica|errata',text):kind='retificacao'
                elif re.match(r'anexo',text):kind='anexo'
                elif re.search(r'\bedital\b',text):kind='edital'
                current['documents'].append({'title':label,'url':target,'published_at':parsed_date,'kind':kind,
                    'format':target.rsplit('.',1)[1].lower()})
        sections.append({'title':status,'groups':count,'empty_confirmed':False})
    if not panels or any(not p['documents'] for p in panels):raise ValueError('grupos sem documentos interpretados')
    ids={}
    for panel in panels:ids[panel['solicitation_id']]=ids.get(panel['solicitation_id'],0)+1
    for panel in panels:panel['solicitation_id_reused']=ids[panel['solicitation_id']]>1
    return {'sections':sections,'panels':panels,'coverage_complete':False,
        'reason':'Agrupamento anual e IDs de consulta não certificam identidade de concurso ou ausência de seleções abertas.'}
