"""Public FAPEMIG API pagination and Nuxt detail payload, decoded as data only."""
import json,re
from urllib.parse import urlsplit,unquote,quote
from app.tenderproof.pilot_adapters import folded
LISTING='https://fapemig.br/api/calls?page=1&per_page=12&publicacao_status=publish'
DETAIL='https://fapemig.br/oportunidades/chamadas-e-editais/'

def listing_page(url):
    m=re.fullmatch(r'https://fapemig.br/api/calls\?page=([1-9]\d*)&per_page=12&publicacao_status=publish',url)
    if not m or int(m[1])>500:raise ValueError('Pagina FAPEMIG invalida')
    return int(m[1])

def detail_slug(url):
    if not url.startswith(DETAIL) or not re.fullmatch('[a-z0-9-]+',url[len(DETAIL):]):raise ValueError('Detalhe FAPEMIG invalido')
    return url[len(DETAIL):]

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='api.site.fapemig.br' or p.query or p.fragment or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|zip|odt)$',path,re.I) or any(x in ('.','..') for x in path.split('/')) or '%' in path or '\\' in path or any(ord(c)<32 for c in path):raise ValueError('Documento FAPEMIG fora do contrato')
    return 'https://api.site.fapemig.br'+quote(path,safe='/()')

def parse_api(raw,url):
    page=listing_page(url);data=json.loads(raw);p=data['pagination']
    if data['page']!=page or p['page']!=page or p['per_page']!=12 or data['total']!=p['total'] or not 1<=p['total_pages']<=500:raise ValueError('Paginacao divergente')
    calls=data['data']
    if not isinstance(calls,list) or len(calls)>12 or len({c['id'] for c in calls})!=len(calls):raise ValueError('Identidade repetida')
    for c in calls:
        detail_slug(DETAIL+c['slug'])
        if c['publicacao_status']!='publish':raise ValueError('Chamada nao publicada')
    return calls,p

def decode_payload(raw):
    data=json.loads(raw)
    if not isinstance(data,list) or len(data)>200000:raise ValueError('Payload invalido')
    visits=0
    def read(i,trail=()):
        nonlocal visits
        visits+=1
        if visits>300000 or len(trail)>60 or type(i)is not int or i in trail:raise ValueError('Payload cyclic or oversized')
        if i<0:return None
        v=data[i]
        if isinstance(v,dict):return {k:read(j,trail+(i,)) for k,j in v.items()}
        if isinstance(v,list):
            if v and isinstance(v[0],str):
                if len(v)!=2 or v[0] not in ('Reactive','ShallowReactive','Ref','ShallowRef'):raise ValueError('Unsupported payload wrapper')
                return read(v[1],trail+(i,))
            return [read(j,trail+(i,)) for j in v]
        return v
    return read(0)

def documents(call):
    docs=[];pending=[]
    for a in call['anexos']:
        title=a['descricao'];text=folded(title);kind='outro'
        try:url=document_url(a['url_anexo'])
        except ValueError:pending.append(a);continue
        if a['tipo'].startswith('resultado') or re.search('resultado|homolog|comunicado',text):pass
        elif 'prorrog' in text:kind='prorrogacao'
        elif a.get('retificacao') or re.search('retific|errata',text):kind='retificacao'
        elif re.search('anexo|formulario|modelo|termo',text):kind='anexo'
        elif re.search('chamada|edital|portaria',text):kind='edital'
        docs.append({'url':url,'title':title,'kind':kind,'format':urlsplit(url).path.rsplit('.',1)[-1].lower()})
    return docs,pending
