"""FEPESE discovery follows official links in the year-prefixed host family.

Document tabs must be observed on the same contest homepage. TR/TA filenames
remain amendments even when their visible label says Edital.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape
from urllib.parse import parse_qs,urlsplit,urljoin
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter,visible_soup,folded,document_kind
from app.tenderproof.validation import title_is_corroborated
from app.tenderproof.security import DestinationBlocked
from app.tenderproof.source_adapter_base import ListingPage

HOSTS=('2026pseducasj.fepese.org.br','2026seletivocomcap.fepese.org.br','2026cpcelesc.fepese.org.br')
CONTEST_HOST = re.compile(r'20\d{2}[a-z0-9]{1,59}\.fepese\.org\.br')
# Legacy address observed in the official ongoing catalogue and inspected
# with the same document-tab contract. Unknown legacy hosts remain refused.
LEGACY_CONTEST_HOSTS = ('sap.fepese.org.br',)

class FepeseAdapter(PilotHTMLAdapter):
    candidate_selector='.highlight .cell p a[href]'
    ready_selectors=(candidate_selector,)
    listing_query_keys=()
    document_hosts=('fepese.org.br',)
    document_identity_pattern=r'(?<![a-z0-9])((?:20\d{2})[a-z0-9]+|sap)\.fepese\.org\.br'

    def __init__(self):
        super().__init__('fepese_open','https://fepese.org.br/concursos/')

    def _host_in_contract(self, host):
        return host == self.portal_host or host in LEGACY_CONTEST_HOSTS or bool(CONTEST_HOST.fullmatch(host or ''))

    def _title(self,anchor):
        row=anchor.find_parent(class_='cell')
        header=row.select_one('strong') if row else None
        return header.get_text(' ',strip=True) if header else None

    def _scope_title(self,anchor):
        return anchor.get_text(' ',strip=True)

    def in_scope(self,title,url):
        return super().in_scope(title,url) and bool(re.search(r'concurso publico|processo seletivo',folded(title)))

    def validate_detail_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        valid_query=(not p.query or (set(q)=={'go','edital'} and q['go']==['home']
                     and len(q['edital'])==1 and re.fullmatch(r'[1-9]\d{0,11}',q['edital'][0])))
        if not (CONTEST_HOST.fullmatch(p.hostname or '') or p.hostname in LEGACY_CONTEST_HOSTS) or p.path not in ('','/') or not valid_query:
            raise ValueError('detalhe fora da família de concursos FEPESE')

    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url)
        external=urlsplit(url).hostname.split('.')[0]
        selection=parse_qs(urlsplit(url).query).get('edital')
        if selection:external+='-edital-'+selection[0]
        return DiscoveredCandidate(candidate_id=self.source+'-'+external,external_id=external,source=self.source,title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))

    def parse_listing(self,html,url,limit=200):
        if html.startswith('{"fepese_catalog_v1":'):
            return self._parse_catalog(html,url,limit)
        page=super().parse_listing(html,url,limit)
        unsupported=set()
        for anchor in visible_soup(html).select(self.candidate_selector):
            target=urljoin(url,anchor['href'])
            if self.in_scope(self._scope_title(anchor) or '',target):
                try:
                    self.validate_detail_url(target)
                except (ValueError, DestinationBlocked):
                    unsupported.add(target)
        if unsupported:
            page.truncated=True
            page.terminal_evidence=None
            page.diagnostics.append(f'{len(unsupported)} concursos visíveis fora dos subdomínios inspecionados; cobertura parcial de contrato')
        return page

    def validate_catalog_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host:
            raise ValueError('API fora do portal FEPESE')
        if p.path=='/wp-json/wp/v2/tax_concurso_status' and q=={'per_page':['100']}:
            return
        if (p.path=='/wp-json/wp/v2/concurso' and set(q)=={'per_page','page','tax_concurso_status_exclude'}
                and q['per_page']==['100'] and all(len(q[k])==1 and re.fullmatch(r'[1-9]\d{0,5}',q[k][0]) for k in ('page','tax_concurso_status_exclude'))):
            return
        raise ValueError('consulta fora do contrato público FEPESE')

    def acquire_listing(self,url,fetch):
        """Preserve the public WP catalogue, not only the popular carousel.

        Every request uses the driver's shared deadline, DNS/TLS checks and
        request cap. A missing page/total fails acquisition, never proves EOF.
        """
        home=fetch(url,self.validate_listing_url,2*1024*1024).content.decode('utf-8')
        soup=visible_soup(home)
        if not soup.select_one('#listaconcursos'):
            raise ValueError('catálogo oficial FEPESE não observado')
        taxonomy_url='https://fepese.org.br/wp-json/wp/v2/tax_concurso_status?per_page=100'
        response=fetch(taxonomy_url,self.validate_catalog_url,2*1024*1024)
        terms=json.loads(response.content)
        closed=[t['id'] for t in terms if t.get('slug')=='encerrados']
        if len(closed)!=1 or type(closed[0]) is not int:
            raise ValueError('taxonomia de encerramento ambígua')
        captures=[];expected=None;number=1
        while True:
            target=f'https://fepese.org.br/wp-json/wp/v2/concurso?per_page=100&page={number}&tax_concurso_status_exclude={closed[0]}'
            response=fetch(target,self.validate_catalog_url,2*1024*1024)
            headers=response.pagination_headers
            total=int(headers['x-wp-total']);pages=int(headers['x-wp-totalpages'])
            if total<0 or pages!=((total+99)//100) or (expected is not None and expected!=(total,pages)):
                raise ValueError('paginação FEPESE mudou ou é inconsistente')
            expected=(total,pages)
            records=json.loads(response.content)
            if not isinstance(records,list) or len(records)!=min(100,max(0,total-(number-1)*100)):
                raise ValueError('página de catálogo incompleta')
            captures.append({'url':target,'headers':headers,'records':records})
            if number>=pages:break
            number+=1
        envelope=json.dumps({'fepese_catalog_v1':{'home':home,'taxonomy':terms,'pages':captures}},ensure_ascii=False)
        if len(envelope.encode('utf-8'))>2*1024*1024:
            raise ValueError('catálogo excede limite de snapshot; requer paginação em trabalhos separados')
        return envelope

    def _parse_catalog(self,html,url,limit):
        self.validate_listing_url(url)
        if not 1<=limit<=10000 or len(html.encode('utf-8'))>2*1024*1024:
            raise ValueError('limite de catálogo inválido')
        data=json.loads(html)['fepese_catalog_v1'];result=ListingPage();seen=set()
        excluded=[];unsupported=[]
        for page in data['pages']:
            self.validate_catalog_url(page['url'])
            for record in page['records']:
                if record['id'] in seen:raise ValueError('registro repetido entre páginas')
                seen.add(record['id'])
                title=visible_soup(record['title']['rendered']).get_text(' ',strip=True)
                body=visible_soup(record['content']['rendered'])
                target=record.get('acf',{}).get('link_hotsite')
                text=body.get_text(' ',strip=True)
                if not self.in_scope(text,target or ''):
                    excluded.append(record['id']);continue
                linked=[(urljoin(url,a['href']),a.get_text(' ',strip=True)) for a in body.select('a[href]')]
                try:
                    if not target:raise ValueError('hotsite não corroborado')
                    root=urlsplit(target)
                    selections=[(link,label) for link,label in linked if self.in_scope(label,link)
                        and urlsplit(link).hostname==root.hostname
                        and urlsplit(link).path.rstrip('/')==root.path.rstrip('/')]
                    if not selections:raise ValueError('hotsite não corroborado')
                    # Keep the portal's title verbatim. The link's selection
                    # label remains in the preserved catalogue response; it
                    # must not become an invented combined title.
                    candidates=[self.candidate_from_url(link,title).model_copy(update={'selection_label_observed':label}) for link,label in selections]
                except (ValueError,DestinationBlocked):
                    unsupported.append(record['id']);continue
                result.candidates.extend(candidates)
        total=int(data['pages'][0]['headers']['x-wp-total'])
        if len(seen)!=total:raise ValueError('total de catálogo não confere')
        result.truncated=bool(unsupported) or len(result.candidates)>limit
        result.candidates=result.candidates[:limit]
        result.diagnostics=[f'API oficial: {total} registros; {len(excluded)} fora do escopo; {len(unsupported)} sem contrato de detalhe']
        if excluded:result.diagnostics.append('registros fora do escopo: '+','.join(map(str,excluded)))
        if unsupported:result.diagnostics.append('detalhes pendentes: '+','.join(map(str,unsupported)))
        if not result.truncated:
            result.terminal_evidence=f'API oficial: {total} registros conferidos em {len(data["pages"])} páginas pelo total declarado'
        return result

    def validate_detail_resource_url(self,url,candidate):
        self._check_candidate(candidate)
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=urlsplit(candidate.detail_url_observed).hostname or p.path not in ('','/') or set(q)!={'go','mn','edital'} or q['go']!=['edital'] or len(q['mn'])!=1 or not re.fullmatch(r'[a-f0-9]{16,64}',q['mn'][0]) or len(q['edital'])!=1 or not re.fullmatch(r'[1-9]\d{0,11}',q['edital'][0]):
            raise ValueError('aba documental pertence a outro concurso FEPESE')
        selected=parse_qs(urlsplit(candidate.detail_url_observed).query).get('edital')
        if selected and q['edital']!=selected:
            raise ValueError('aba documental pertence a outro edital do mesmo site')

    def detail_resource_urls(self,html,url):
        c=self.candidate_from_url(url)
        soup=visible_soup(html);found=[]
        for a in soup.select('a[href]'):
            target=urljoin(url,a['href'])
            if parse_qs(urlsplit(target).query).get('go')!=['edital']:continue
            self.validate_detail_resource_url(target,c)
            if target not in found:found.append(target)
        if len(found)!=1:raise ValueError('aba edital FEPESE ausente ou ambígua')
        return found

    def compose_detail(self,html,url,resources):
        expected=self.detail_resource_urls(html,url)
        if len(resources)!=1 or resources[0].get('url')!=expected[0] or not isinstance(resources[0].get('body'),str):
            raise ValueError('recurso FEPESE não corresponde à aba observada')
        home=visible_soup(html);tab=visible_soup(resources[0]['body'])
        if not home.title or not tab.title or folded(home.title.get_text())!=folded(tab.title.get_text()):
            raise ValueError('cabeçalho da aba FEPESE diverge do concurso')
        for node in tab.select('html,body,head'):
            node.unwrap()
        marker=home.new_tag('section',id='fepese-document-tab')
        marker.append(tab)
        (home.body or home).append(marker)
        evidence=home.new_tag('script',id='fepese-resource-evidence',type='application/json')
        evidence.string=json.dumps(resources,ensure_ascii=False).replace('<',chr(92)+'u003c')
        (home.body or home).append(evidence)
        return str(home)

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate)
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=urlsplit(candidate.detail_url_observed).hostname or p.path not in ('','/') or set(q)!={'go','arquivo','inline'} or q['go']!=['download'] or q['inline']!=['1'] or len(q['arquivo'])!=1 or not re.fullmatch(r'[A-Za-z0-9_.-]{1,180}\.pdf',q['arquivo'][0]):
            raise ValueError('documento fora do subdomínio e rota FEPESE associados')

    def documents(self,html,candidate):
        self._check_candidate(candidate)
        soup=visible_soup(html);tab=soup.select_one('#fepese-document-tab')
        if tab is None:raise ValueError('aba documental FEPESE não capturada')
        docs=[];seen=set()
        for a in tab.select('a[href]'):
            url=urljoin(candidate.detail_url_observed,a['href'])
            if parse_qs(urlsplit(url).query).get('go')!=['download']:continue
            self.validate_document_url(url,candidate)
            if url in seen:continue
            seen.add(url)
            title=a.get_text(' ',strip=True);filename=parse_qs(urlsplit(url).query)['arquivo'][0]
            kind=document_kind(title,url)
            revised = re.search(r'(?:^|[_-])(?:TR|TA)\d+(?:[_-]|\.)',filename,re.I)
            if re.search(r'retifica|errata|termo\s+aditivo', folded(title)) or re.match(r'^(?:TR|TA)[_-]?\d+[_-]', filename, re.I):
                kind='retificacao'
            elif kind == 'edital' and revised:
                # The observed edital contains incorporated revisions; acquire
                # its bytes, but the publication gate requires effect review.
                kind='consolidado'
            elif re.search(r'prorrog', folded(title)):
                kind='prorrogacao'
            docs.append(DocumentCandidate(doc_id=self.source+'-'+hashlib.sha256(url.encode()).hexdigest()[:16],title=title,url_requested=url,kind=kind))
        return docs

    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        if not title_is_corroborated(candidate.title_observed or '',soup.get_text(' ',strip=True)):
            raise ValueError('órgão observado não confirmado no detalhe FEPESE')
        if not self.documents(html,candidate):raise ValueError('manifesto documental FEPESE ausente')

    def document_identity_ids(self,candidate,pages):
        """A shared host needs the observed selection label and main heading.

        The numeric query ID is a portal key, not an edital number. Never map
        it by equality with a PDF number or by the common municipality alone.
        """
        text='\n'.join(p.text for p in pages)
        ids=set(re.findall(self.document_identity_pattern,text,re.I))
        selected=parse_qs(urlsplit(candidate.detail_url_observed).query).get('edital')
        if not selected:return ids
        self._check_candidate(candidate)
        host=urlsplit(candidate.detail_url_observed).hostname.split('.')[0]
        label=candidate.selection_label_observed or ''
        number_pattern=r'\bedital\s+(?:n[ºo.]?\s*)?(\d{1,5}/\d{4})\b'
        numbers=set(re.findall(number_pattern,label,re.I))
        from app.tenderproof.validation import distinctive_title_words
        words=distinctive_title_words(label)
        first=next((p.text for p in pages if p.page_number==1),'')
        # Restrict corroboration to the masthead, before the opening clause;
        # a mention in a job requirement or annex cannot identify the issuer.
        heading=re.split(r'\babre(?:m)?[-\s]se\b|\babre\s+inscri',first,flags=re.I)[0][:600]
        if (ids=={host} and len(numbers)==1 and words
                and numbers==set(re.findall(number_pattern,heading,re.I))
                and title_is_corroborated(label,heading)):
            return {candidate.external_id}
        return ids or {'selection-identity-unproven'}

BATCH99_FEPESE_ADAPTERS={'fepese_open':FepeseAdapter()}
