"""Observed personnel-selection contracts; funding/scholarships are excluded."""
import re,hashlib
from datetime import datetime,timezone
from urllib.parse import urljoin,urlsplit,parse_qs,urldefrag
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter,visible_soup,folded,document_kind
from app.tenderproof.validation import title_is_corroborated


def item(source,url,key,title):
 return DiscoveredCandidate(candidate_id=f'{source}-{key}',source=source,external_id=key,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))
def doc(source,title,url,kind=None):
 return DocumentCandidate(doc_id=source+'-'+hashlib.sha256(url.encode()).hexdigest()[:16],title=title,url_requested=url,kind=kind or document_kind(title,url))
def bounded(html):
 if len(html.encode('utf-8'))>2*1024*1024:raise ValueError('HTML excede2MiB')
 return visible_soup(html)


class FapespPersonnelAdapter(PilotHTMLAdapter):
 source='fapesp_selection'
 ready_selectors=('.page-body',)
 listing_query_keys=()
 document_identity_pattern=r'/files/upload/(\d+)/'
 def __init__(self):super().__init__(self.source,'https://fapesp.br/index.php/processoseletivo')
 def validate_detail_url(self,url):self.validate_listing_url(url)
 def candidate_from_url(self,url,title=None):
  self.validate_detail_url(url);return item(self.source,url,'4470',title)
 def _originals(self,s):
  return [a for a in s.select('.page-body a[href]') if re.fullmatch(r'concurso publico\s+n\s*o?\s*\d+/\d{4}',folded(a.get_text(' ',strip=True)))]
 def _verified_original(self,anchor):
  title=folded(anchor.get_text(' ',strip=True))
  if not re.fullmatch(r'concurso publico\s+n\s*o?\s*01/2026',title) or anchor['href']!='https://fapesp.br/files/upload/4470/concurso0126.pdf':
   raise ValueError('FAPESP: edital diferente de01/2026 exige novo contrato de identidade')
 def _candidates(self,html,url,limit):
  s=bounded(html);found=self._originals(s)
  if len(found)>1:raise ValueError('página FAPESP tem mais de um concurso principal; revisão de identidade necessária')
  if not found:return []
  a=found[0];self._verified_original(a);target=urljoin(url,a['href']);c=self.candidate_from_url(url,'FAPESP - '+a.get_text(' ',strip=True));self.validate_document_url(target,c)
  return [c]
 def confirm_identity(self,c,html,url):
  self._check_candidate(c);self.validate_detail_url(url);s=bounded(html)
  found=self._originals(s)
  if len(found)==1:self._verified_original(found[0])
  if c.title_observed and not re.search(r'\b01/2026\b',c.title_observed):raise ValueError('FAPESP: candidato de outro número/ano')
  if len(found)!=1 or not c.title_observed or not title_is_corroborated(c.title_observed,'FAPESP - '+found[0].get_text(' ',strip=True)):
   raise ValueError('concurso FAPESP incompatível ou ambíguo')
 def validate_document_url(self,url,c):
  self._check_candidate(c);p=self._destination(url)
  if p.hostname!=self.portal_host or p.query or not re.fullmatch(r'/files/upload/4470/[A-Za-z0-9_.-]+\.pdf',p.path):raise ValueError('documento FAPESP fora da página4470')
 def documents(self,html,c):
  self.confirm_identity(c,html,c.detail_url_observed);s=bounded(html);original=self._originals(s)[0];result=[];seen=set()
  base=s.select_one('base[href]')
  if not base or base['href']!='https://fapesp.br/':raise ValueError('base documental FAPESP mudou')
  for a in s.select('.page-body a[href]'):
   url=urljoin(base['href'],a['href'])
   if not urlsplit(url).path.lower().endswith('.pdf'):continue
   self.validate_document_url(url,c)
   if url in seen:continue
   seen.add(url);result.append(doc(self.source,a.get_text(' ',strip=True),url,'edital' if a==original else 'outro'))
  return result


class FaperjPersonnelAdapter(PilotHTMLAdapter):
 source='faperj_selection'
 ready_selectors=('section.corpo-interna',)
 document_identity_pattern=r'\?id=(\d+\.7\.\d+)'
 candidate_selector='a[href]'
 listing_query_keys=('pg',)
 def __init__(self):super().__init__(self.source,'https://faperj.br/arquivo_noticias.phtml',document_hosts=('www.faperj.br',))
 def _title(self,a):return a.get_text(' ',strip=True)
 def in_scope(self,title,url):
  text=folded(title)
  return not any(w in text for w in ('bolsa','bolsista','premio','propostas','resultado','eliminacao','auxilio','nao realizacao')) and (('edital' in text and 'cargo de' in text) or 'concurso publico' in text or 'contratacao de pessoal' in text)
 def validate_detail_url(self,url):
  p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
  if p.hostname!=self.portal_host or p.path not in ('','/') or set(q)!={'id'} or len(q['id'])!=1 or not re.fullmatch(r'\d+\.7\.\d+',q['id'][0]):raise ValueError('artigo FAPERJ fora da identidade observada')
 def candidate_from_url(self,url,title=None):
  self.validate_detail_url(url)
  # Drop only the observed editorial prefix; retain the literal position name.
  if title:title=re.sub(r'^FAPERJ anuncia edital de chamamento p[uú]blico para o cargo de\s+', '', title, flags=re.I)
  return item(self.source,url,parse_qs(urlsplit(url).query)['id'][0],title)
 def confirm_identity(self,c,html,url):
  s=self._check_detail(c,html,url);bounded(html);heads=s.select('h1')
  if len(heads)!=1 or not c.title_observed or not self.in_scope(heads[0].get_text(' ',strip=True),url) or not title_is_corroborated(c.title_observed,heads[0].get_text(' ',strip=True)):
   raise ValueError('detalhe FAPERJ não confirma seleção de pessoas')
 def validate_document_url(self,url,c):
  self._check_candidate(c);p=self._destination(url)
  if p.query or not re.fullmatch(r'/rp/downloads/[^/]+\.pdf',p.path,re.I):raise ValueError('PDF FAPERJ fora do diretório observado')
 def documents(self,html,c):
  self.confirm_identity(c,html,c.detail_url_observed);s=bounded(html);result=[];seen=set()
  for a in s.select('section.corpo-interna .tamanho-fonte a[href]'):
   url=urljoin(c.detail_url_observed,a['href'])
   if not urlsplit(url).path.lower().endswith('.pdf'):continue
   self.validate_document_url(url,c)
   if url in seen:continue
   seen.add(url);result.append(doc(self.source,a.get_text(' ',strip=True),url))
  return result

class FapesbPersonnelAdapter(PilotHTMLAdapter):
 source='fapesb_selection'
 ready_selectors=('#reda-tab-2026',)
 listing_query_keys=()
 document_identity_pattern=r'REDA[^\n]{0,50}(2026)'
 original='https://www.fapesb.ba.gov.br/wp-content/uploads/2019/08/EDITAL_DEFINITIVO_REDA_2026.pdf'
 def __init__(self):super().__init__(self.source,'https://www.fapesb.ba.gov.br/reda/')
 def validate_detail_url(self,url):
  base,fragment=urldefrag(url);self.validate_listing_url(base)
  if fragment!='reda-tab-2026':raise ValueError('aba REDA fora do ano observado')
 def candidate_from_url(self,url,title=None):
  self.validate_detail_url(url);return item(self.source,url,'01-2026',title)
 def _section(self,html):
  s=bounded(html);sections=s.select('#reda-tab-2026')
  if len(sections)!=1:raise ValueError('aba REDA2026 ausente ou ambígua')
  section=sections[0];head=section.select('h4')
  if len(head)!=1 or not re.fullmatch(r'processo seletivo simplificado\s*[–-]\s*edital n[ºo]?\s*01/2026\s*[–-]\s*fapesb',head[0].get_text(' ',strip=True),re.I):
   raise ValueError('número/ano ou título REDA não corresponde a01/2026')
  originals=[a for a in section.select('a[href]') if folded(a.get_text(' ',strip=True))=='edital de abertura']
  if len(originals)!=1 or originals[0]['href']!=self.original:raise ValueError('principal REDA diferente ou ambíguo')
  return section,head[0].get_text(' ',strip=True)
 def _candidates(self,html,url,limit):
  section,title=self._section(html)
  return [self.candidate_from_url(url+'#reda-tab-2026',title)]
 def confirm_identity(self,c,html,url):
  self._check_detail(c,html,url);section,title=self._section(html)
  if c.title_observed!=title:raise ValueError('título REDA incompatível')
 def validate_document_url(self,url,c):
  self._check_candidate(c);p=self._destination(url)
  if p.query or p.hostname!=self.portal_host or not re.fullmatch(r'/wp-content/uploads/2019/08/[^/]+\.pdf',p.path,re.I):raise ValueError('documento REDA fora do diretório observado')
 def documents(self,html,c):
  self.confirm_identity(c,html,c.detail_url_observed);section,title=self._section(html);result=[];seen=set()
  for a in section.select('a[href]'):
   url=urljoin(c.detail_url_observed,a['href'])
   if not urlsplit(url).path.lower().endswith('.pdf'):continue
   self.validate_document_url(url,c)
   if url in seen:continue
   seen.add(url);result.append(doc(self.source,a.get_text(' ',strip=True),url,'edital' if url==self.original else 'outro'))
  return result

BATCH99_SOUTHEAST_ADAPTERS=(FapespPersonnelAdapter(),FaperjPersonnelAdapter(),FapesbPersonnelAdapter())
