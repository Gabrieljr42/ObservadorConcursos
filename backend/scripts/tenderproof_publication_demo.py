"""Run from backend: .venv/Scripts/python.exe scripts/tenderproof_publication_demo.py"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tenderproof.publication_demo import run_demo

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2, default=str))
