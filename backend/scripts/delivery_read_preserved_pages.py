"""Read explicitly selected pages of a preserved run through the normal processor."""
import argparse
import hashlib
import json
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--pages', required=True, help='Explicit comma-separated page numbers')
    parser.add_argument('--supplement-sha', help='Select an already preserved supplementary artifact by its full SHA')
    args = parser.parse_args()
    wanted = {int(number) for number in args.pages.split(',')}
    store = get_store()
    run = store.get_run(args.run)
    assert run and run.artifact
    artifact = run.artifact
    if args.supplement_sha:
        matches = [item.artifact for item in run.supplementary_documents if item.artifact.sha256 == args.supplement_sha]
        assert len(matches) == 1
        artifact = matches[0]
    content = store.load_artifact_bytes(artifact)
    assert hashlib.sha256(content).hexdigest() == artifact.sha256
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content, artifact_id=artifact.artifact_id, owner_id=str(run.owner_user_id),
        max_bytes=max(len(content), 30 * 1024 * 1024), max_pages=200, reuse_completed=True)
    assert not truncated and not errors and total == processed
    print(json.dumps({'source': run.source, 'sha256': artifact.sha256,
        'pages': [{'number': page.page_number, 'text': page.text} for page in pages if page.page_number in wanted]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
