"""FAPEAM public catalogue acquisition. Personnel scope remains document review."""
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fapeam_listing import TABS, acquire_page, parse_listing, validate_detail_url
from app.tenderproof.fapeam_detail import DOCUMENT_HOSTS, parse_detail, validate_document_url
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage
from app.tenderproof.pilot_adapters import document_kind, folded

LISTING='https://www.fapeam.am.gov.br/editais/'
LIVE_LISTING=LISTING+'?aba=vigentes&p=1'


class FapeamAdapter(HTMLSourceAdapter):
    source='fapeam_selection'
    allowed_hosts=DOCUMENT_HOSTS
    # The legacy tab URLs now return the official 404 page. The public
    # ``vigentes`` route is the current navigation contract and maps to the
    # observed get-editais/editais-abertos AJAX request.
    listing_urls=(LIVE_LISTING,)
    ready_selectors=('article.post-type-editais',)
    observed_url_paths=()
    document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Catálogo público misto; compatibilidade com seleção de pessoas exige análise por edital. PDFs digitalizados e publicação ainda pendentes.'

    def _cursor(self,url):
        parts=urlsplit(url)
        if parts.scheme!='https' or parts.netloc!='www.fapeam.am.gov.br' or parts.path!='/editais/' or parts.fragment:
            raise ValueError('cursor fora da listagem FAPEAM')
        query=parse_qs(parts.query,keep_blank_values=True)
        raw_tab=(query.get('aba') or [None])[0]
        if raw_tab=='vigentes':
            if set(query)-{'aba','p'} or any(len(values)!=1 for values in query.values()):
                raise ValueError('cursor fora da listagem FAPEAM')
            raw_page=(query.get('p') or ['1'])[0]
            if not re.fullmatch(r'[1-9]\d*',raw_page):
                raise ValueError('cursor fora da listagem FAPEAM')
            return 'editais-abertos',int(raw_page)
        if set(query)!={'aba','p'}:
            raise ValueError('cursor fora da listagem FAPEAM')
        if raw_tab not in TABS or len(query['aba'])!=1 or len(query['p'])!=1 or not re.fullmatch(r'[1-9]\d*',query['p'][0]):
            raise ValueError('cursor fora da listagem FAPEAM')
        return raw_tab,int(query['p'][0])

    def validate_listing_url(self,url):
        self._cursor(url)

    def acquire_listing(self,url,fetch):
        tab,page=self._cursor(url)
        response,_=acquire_page(fetch,tab=tab,page=page)
        return response.content.decode('utf-8-sig')

    def _detail(self,url):
        base,separator,fragment=url.partition('#')
        validate_detail_url(base)
        if not separator or not re.fullmatch(r'post-[1-9]\d*',fragment):
            raise ValueError('detalhe FAPEAM sem identidade do artigo')
        return base,fragment[5:]

    def validate_detail_url(self,url):
        self._detail(url)

    def candidate_from_url(self,url,title=None):
        _,identity=self._detail(url)
        return DiscoveredCandidate(candidate_id=self.source+'-'+identity,source=self.source,
            external_id=identity,title_observed=title,detail_url_observed=url,
            observed_at=datetime.now(timezone.utc))

    def parse_listing(self,html,url,limit=200):
        tab,page=self._cursor(url)
        if type(limit) is not int or not 1<=limit<=10000:
            raise ValueError('limite de candidatos inválido')
        parsed=parse_listing(html,tab=tab,page=page)
        truncated=len(parsed['items'])>limit
        candidates=[self.candidate_from_url(row['url']+'#post-'+row['external_id'],row['title'])
                    for row in parsed['items'][:limit]]
        return ListingPage(candidates=candidates,
            next_urls=[LISTING+'?aba='+tab+'&p='+str(n) for n in parsed['linked_pages'] if n!=page],
            truncated=truncated,
            empty_evidence='Array editais_formatted vazio na resposta pública validada.' if not parsed['items'] else None,
            terminal_evidence='Resposta de paginação validada sem página posterior.' if parsed['terminal'] and not truncated else None,
            diagnostics=['Catálogo misto: compatibilidade de cada item exige análise documental; período bruto não adotado como prazo.']
                +(['Limite de candidatos atingido; página parcial.'] if truncated else []))

    def _parsed_detail(self,candidate,html,url):
        base,identity=self._detail(url)
        if (candidate.source!=self.source or candidate.external_id!=identity
                or candidate.detail_url_observed!=url):
            raise ValueError('candidato incompatível com detalhe FAPEAM')
        return parse_detail(html,url=base,external_id=identity)

    def acquire_detail(self,url,candidate,fetch):
        base,_=self._detail(url)
        def validate(target):
            validate_detail_url(target)
            if target!=base:raise ValueError('redirect altera detalhe FAPEAM')
        response=fetch(base,validate,2*1024*1024)
        html=response.content.decode('utf-8-sig')
        self._parsed_detail(candidate,html,url)
        return html

    def confirm_identity(self,candidate,html,url):
        self._parsed_detail(candidate,html,url)

    def documents(self,html,candidate):
        parsed=self._parsed_detail(candidate,html,candidate.detail_url_observed)
        def kind(row):
            if row['kind']=='edital':return 'edital'
            label=' / '.join(row['labels_observed'])
            # The label establishes review need, not an approved field effect.
            if re.search(r'\bretificacao\b|\bitem alterado\b',folded(label)):
                return 'retificacao'
            observed=document_kind(label,row['url'])
            return observed if observed not in ('edital','consolidado') else 'outro'
        return [DocumentCandidate(doc_id='fapeam-'+candidate.external_id+'-'+hashlib.sha256(row['url'].encode()).hexdigest()[:20],
            title=parsed['title_observed'] if row['kind']=='edital' else ' / '.join(row['labels_observed']) or 'Documento vinculado ao edital',
            kind=kind(row),url_requested=row['url'],
            reason_chosen='Documento no corpo do artigo post-'+candidate.external_id+'. Efeito e compatibilidade ainda não avaliados.')
            for row in parsed['documents']]

    def validate_document_url(self,url,candidate):
        _,identity=self._detail(candidate.detail_url_observed)
        if candidate.source!=self.source or candidate.external_id!=identity:
            raise ValueError('identidade documental FAPEAM incompatível')
        validate_document_url(url)

    def choose_document(self,docs):
        originals=[doc for doc in docs if doc.kind=='edital']
        if len(originals)!=1:raise ValueError('edital principal FAPEAM não é único')
        return originals[0]
