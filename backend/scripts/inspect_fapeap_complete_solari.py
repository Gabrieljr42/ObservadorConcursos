"""One explicit budgeted discovery attempt; no challenge solving or publication."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from solari_browser import Solari
from app.tenderproof.solari_budget import configured_budget
from app.tenderproof.solari_adapter import confirm_browser_released


async def main():
    out = Path('/var/lib/observador/tenderproof/product-completion/fapeap-solari-complete')
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'report.json').exists():
        raise RuntimeError('Attempt already journaled; inspect it before any further paid action')
    key = os.environ.get('SOLARI_API_KEY')
    if not key:
        raise RuntimeError('Solari key missing')
    budget = configured_budget()
    if budget is None:
        raise RuntimeError('Shared budget missing')
    report = {'at': datetime.now(timezone.utc).isoformat(),
              'url': 'https://fapeap.portal.ap.gov.br/', 'closed': False, 'status': 'pending'}
    reservation = budget.reserve('browser', maximum_seconds=18000, hourly_usd='0.15',
        tariff='https://docs.getsolari.com/pricing; checked 2026-09-09; conservative Free rate, Starter 5h maximum')
    report['reservation'] = reservation
    (out / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    browser = None
    async with Solari(api_key=key, base_url='https://api.getsolari.com', max_attempts=1, timeout_ms=30000) as client:
        try:
            report['stage']='launch'
            browser = await client.launch(recording=False, stealth=False, captcha=False, retries=0)
            budget.created(reservation, browser.id)
            (out / 'session.json').write_text(json.dumps({'session_id': browser.id, 'reservation': reservation}), encoding='utf-8')
            report['stage']='new_page'
            page = await browser.new_page()
            report['stage']='navigate'
            response = await page.goto(report['url'], wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(5000)
            report['stage']='read_content'
            html = await page.content()
            (out / 'listing.html').write_text(html, encoding='utf-8')
            report.update(http_status=response.status if response else None,
                          html_sha256=hashlib.sha256(html.encode()).hexdigest(), byte_len=len(html.encode()))
            report['status'] = 'challenge' if any(x in html.lower() for x in
                ('just a moment', 'verify you are human', 'challenge-platform')) else 'content_acquired'
            if report['status'] == 'content_acquired':
                report['title'] = (await page.title())[:200]
            if report['status']=='content_acquired':
                from bs4 import BeautifulSoup
                from urllib.parse import urlsplit,urljoin
                import time
                start=time.monotonic()
                root_soup=BeautifulSoup(html,'html.parser')
                urls=list(dict.fromkeys(a['href'] for a in root_soup.select('a[href]') if a['href'].startswith('https://fapeap.portal.ap.gov.br/pagina/programas/')))
                urls.append('https://fapeap.portal.ap.gov.br/publicacoes')
                report['pages']=[];report['documents']=[];seen={}
                for url in urls:
                    if time.monotonic()-start>480:raise RuntimeError('Bounded collection deadline')
                    report['stage']='program_navigation'
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=45000)
                    await page.wait_for_timeout(1500)
                    body=await page.content();sha=hashlib.sha256(body.encode()).hexdigest();(out/(sha+'.html')).write_text(body,encoding='utf-8')
                    soup=BeautifulSoup(body,'html.parser');docs=[]
                    for a in soup.select('a[href]'):
                        target=urljoin(url,a['href']);p=urlsplit(target)
                        if p.scheme!='https' or p.netloc!='matrix.amapa.gov.br' or not p.path.startswith('//storage/'):continue
                        parent=a.find_parent('tr') or a.parent
                        label=parent.get_text(' ',strip=True)
                        docs.append({'url':target,'title':label})
                        seen.setdefault(target,[]).append({'page_url':url,'title':label})
                    report['pages'].append({'url':url,'status':response.status if response else None,'sha256':sha,'documents':docs})
                    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                report['stage']='publication_pagination'
                publication_hashes=set()
                for number in range(2,101):
                    nxt=page.locator('button[aria-label="Próxima"]')
                    if await nxt.count()!=1 or await nxt.is_disabled():
                        report['publication_pagination_verified']=True;break
                    await nxt.click(timeout=15000)
                    await page.wait_for_timeout(1500)
                    body=await page.content();soup=BeautifulSoup(body,'html.parser')
                    content=soup.select_one('table')
                    marker=hashlib.sha256(str(content).encode()).hexdigest()
                    if marker in publication_hashes:raise RuntimeError('Publication pagination repeated content')
                    publication_hashes.add(marker)
                    sha=hashlib.sha256(body.encode()).hexdigest();(out/(sha+'.html')).write_text(body,encoding='utf-8');docs=[]
                    for a in soup.select('a[href]'):
                        target=a['href']
                        if not target.startswith('https://matrix.amapa.gov.br//storage/'):continue
                        parent=a.find_parent('tr') or a.parent;label=parent.get_text(' ',strip=True)
                        docs.append({'url':target,'title':label});seen.setdefault(target,[]).append({'page_url':'https://fapeap.portal.ap.gov.br/publicacoes','publication_page':number,'title':label})
                    report['pages'].append({'url':page.url,'publication_page':number,'sha256':sha,'documents':docs})
                    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                report['stage']='document_request'
                report['broken_links']=[u for u in seen if u.endswith('/storage/')]

                for url,bindings in seen.items():
                    if url.endswith('/storage/'):continue
                    if time.monotonic()-start>720:
                        report['document_collection_pending']='deadline';break
                    response=await page.request.get(url,timeout=30000,max_redirects=0)
                    row={'url':url,'status':response.status,'bindings':bindings};report['documents'].append(row)
                    if response.status!=200:
                        report['document_collection_pending']='public_document_request_failed';break
                    length=int(response.headers.get('content-length','0'))
                    if length>30*1024*1024:
                        row['error']='byte_limit';continue
                    content=await response.body()
                    if len(content)>30*1024*1024:raise RuntimeError('Document byte limit')
                    sha=hashlib.sha256(content).hexdigest();suffix='pdf' if content.startswith(b'%PDF-') else 'zip' if content.startswith(b'PK') else 'bin'
                    (out/(sha+'.'+suffix)).write_bytes(content);row.update(sha256=sha,bytes=len(content),format=suffix)
                    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                    await page.wait_for_timeout(500)
                report['unique_document_links']=len(seen)
                report.setdefault('publication_pagination_verified',False)
        except Exception as exc:
            import re
            message=str(exc).replace(key,'[REDACTED]')
            message=re.sub(r'https?://[^\s]+','[URL]',message)
            report.update(status='failed', error_type=type(exc).__name__, error_message=message[:1200], http_error_status=getattr(exc,'status_code',None))
        finally:
            if browser is not None:
                try:
                    await browser.close()
                    report['closed'] = await confirm_browser_released(client, browser.id)
                    if report['closed']:
                        budget.closed(browser.id)
                except Exception as exc:
                    report['close_error_type'] = type(exc).__name__
            report['reserved_usd'] = budget.snapshot()['reserved_usd']
            report['confirmed_billed_usd'] = None
            (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps({k: v for k, v in report.items() if k not in ('reservation','pages','documents')}), flush=True)


asyncio.run(main())
