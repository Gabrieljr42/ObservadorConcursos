"""Two bounded public HTTP cycles; sanitized fixtures and no publication."""
import os
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch30_institutional_adapters import BATCH30_INSTITUTIONAL_ADAPTERS
from app.tenderproof.batch30_uniselva_adapter import BATCH30_UNISELVA_ADAPTERS
import tenderproof_pilot_live as probe


class SanitizedDriver(probe.CapturingDriver):
    def _save(self, kind, url, html):
        if html.lstrip().startswith(('{', '[')):
            # API bodies must remain JSON for faithful offline replay.
            payload = json.loads(html)
            super()._save(kind, url, json.dumps(probe.redact(payload), ensure_ascii=False))
            self.captures[-1]['format'] = 'decoded public JSON; signed URL values redacted; fixture hash only'
            return
        soup = BeautifulSoup(html, 'lxml')
        for node in soup.find_all(True):
            for attribute in ('href', 'src', 'action', 'data-src'):
                value = node.get(attribute)
                if not isinstance(value, str):
                    continue
                parts = urlsplit(value)
                if re.search(r'X-Amz-|AWSAccessKeyId|Signature=', parts.query, re.I):
                    node[attribute] = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
        for node in soup.select('input[type=hidden]'):
            node.attrs.pop('value', None)
        super()._save(kind, url, str(soup))
        self.captures[-1]['format'] = 'decoded HTML; hidden values and public signed queries removed; fixture hash only'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='*')
    parser.add_argument('--report', default='../docs/tenderproof-batch30-institutional-live.json')
    parser.add_argument('--root', default='.tenderproof/batch30-institutional-live-20260908')
    parser.add_argument('--listing-url')
    args = parser.parse_args()
    probe.PILOT_ADAPTERS = tuple(a for a in (*BATCH30_INSTITUTIONAL_ADAPTERS, *BATCH30_UNISELVA_ADAPTERS) if not args.sources or a.source in args.sources)
    if not probe.PILOT_ADAPTERS:
        parser.error('no supported source selected')
    if args.listing_url:
        if len(probe.PILOT_ADAPTERS) != 1:
            parser.error('listing override requires exactly one source')
        probe.PILOT_ADAPTERS[0].validate_listing_url(args.listing_url)
        probe.PILOT_ADAPTERS[0].listing_urls = (args.listing_url,)
    probe.CapturingDriver = SanitizedDriver
    probe.ROOT = Path(args.root).resolve()
    probe.CAPTURE = Path('tests/fixtures/tenderproof_batch30_institutional')
    probe.REPORT = Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(probe.ROOT/'artifacts')
    probe.main()
