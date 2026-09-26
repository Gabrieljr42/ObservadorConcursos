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
    out = Path('/var/lib/observador/tenderproof/product-completion/remaining-bancas-solari-20260909')
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
              'sources': [], 'closed': False, 'status': 'pending'}
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
            for source,url in [('aocp_open','https://www.institutoaocp.org.br/'),('unifil_open','https://main.institutounifil.com.br/'),('oppus_open','https://www.oppusconcursos.com.br/')]:
                row={'source':source,'url':url};report['sources'].append(row)
                try:
                    page=await browser.new_page()
                    response=await page.goto(url,wait_until='domcontentloaded',timeout=45000)
                    await page.wait_for_timeout(5000)
                    html=await page.content();(out/(source+'.html')).write_text(html,encoding='utf-8')
                    row.update(http_status=response.status if response else None,html_sha256=hashlib.sha256(html.encode()).hexdigest(),title=(await page.title())[:200])
                    row['status']='challenge' if any(x in html.lower() for x in ('just a moment','verify you are human','challenge-platform','checking your browser')) else 'content_acquired'
                    await page.close()
                except Exception as exc:
                    row.update(status='failed',error_type=type(exc).__name__)
                (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                print(json.dumps(row),flush=True)
            report['status']='attempted_all_sources'
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
            print(json.dumps({k: v for k, v in report.items() if k != 'reservation'}), flush=True)


asyncio.run(main())
