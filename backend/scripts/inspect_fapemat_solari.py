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
    out = Path('/var/lib/observador/tenderproof/product-completion/fapemat-solari')
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
              'url': 'https://www.fapemat.mt.gov.br/editais_1', 'closed': False, 'status': 'pending'}
    reservation = budget.reserve('browser', maximum_seconds=18000, hourly_usd='0.15',
        tariff='https://docs.getsolari.com/pricing; checked 2026-09-09; conservative Free rate, Starter 5h maximum')
    report['reservation'] = reservation
    (out / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    browser = None
    async with Solari(api_key=key, base_url='https://api.getsolari.com', max_attempts=1, timeout_ms=30000) as client:
        try:
            browser = await client.launch(recording=False, stealth=False, captcha=False, retries=0)
            budget.created(reservation, browser.id)
            (out / 'session.json').write_text(json.dumps({'session_id': browser.id, 'reservation': reservation}), encoding='utf-8')
            page = await browser.new_page()
            response = await page.goto(report['url'], wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(5000)
            html = await page.content()
            (out / 'listing.html').write_text(html, encoding='utf-8')
            report.update(http_status=response.status if response else None,
                          html_sha256=hashlib.sha256(html.encode()).hexdigest(), byte_len=len(html.encode()))
            report['status'] = 'challenge' if any(x in html.lower() for x in
                ('just a moment', 'verify you are human', 'challenge-platform')) else 'content_acquired'
            if report['status'] == 'content_acquired':
                report['title'] = (await page.title())[:200]
                report['tabs'] = []
                for label in ('Abertos', 'Encerrados', 'Resultado'):
                    target=page.get_by_text(label,exact=True)
                    if await target.count()!=1:
                        report['tabs'].append({'label':label,'status':'ambiguous_or_missing'})
                        continue
                    await target.click(timeout=15000)
                    await page.wait_for_timeout(3000)
                    tab_html=await page.content()
                    (out/(label.lower()+'.html')).write_text(tab_html,encoding='utf-8')
                    report['tabs'].append({'label':label,'sha256':hashlib.sha256(tab_html.encode()).hexdigest(),'bytes':len(tab_html.encode())})
        except Exception as exc:
            report.update(status='failed', error_type=type(exc).__name__, http_error_status=getattr(exc,'status_code',None))
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
            print(json.dumps({k: v for k, v in report.items() if k != 'reservation'}), flush=True)


asyncio.run(main())
