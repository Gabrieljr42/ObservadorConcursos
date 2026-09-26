"""Prepare existing TenderProof runs for human document review only.

No approval, apply, publication, or collection is performed.
"""
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import httpx

RUNS = {
    "jcm_268": "tp-tcj-e57a86e6e2ff5da5868acf49a60ac403-4",
    "consulplan_unai": "tp-tcj-706b5bc7f1f75e5cb0c3c05c48bce934-3",
    "imeso_139": "tp-tcj-377fa72c32a2587eb20c8e068572a18b-1",
    "abcp_2868": "tp-tcj-b7b17f29eeac52a9a43f71c360753e43-1",
    "idib_362": "tp-tcj-b6372819d87e51c185e6427865a5bf62-1",
    "cebraspe_ponta_pora": "tp-tcj-2b58bacc0b6a5a028ffc292908b9b6da-1",
    "fepese_caxambu": "tp-tcj-8c4428c810c45812a92132a23bf42958-1",
}


def main():
    email = os.environ.get("PILOT_OPERATOR_EMAIL")
    password = os.environ.get("PILOT_OPERATOR_PASSWORD")
    if not email or not password:
        credentials = Path(".tenderproof/local-pilot/ACESSO-LOCAL.md").read_text(encoding="utf-8")
        email = re.search(r"E-mail:\s*([^\r\n]+)", credentials)[1].strip(" `")
        password = re.search(r"Senha:\s*([^\r\n]+)", credentials)[1].strip(" `")
    result = {"observed_at": datetime.now(timezone.utc).isoformat(), "approve_or_apply": False, "runs": {}}
    base_url = os.environ.get("PILOT_API_BASE_URL", "http://localhost:8000")
    with httpx.Client(base_url=base_url, trust_env=False, timeout=240) as client:
        login = client.post("/auth/login", json={"email": email, "password": password})
        login.raise_for_status()
        client.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        for label, run_id in RUNS.items():
            item = {"run_id": run_id}
            try:
                response = client.post(f"/tenderproof/continuous/document-review/{run_id}/prepare")
                item["prepare_status"] = response.status_code
                item["prepare"] = response.json()
                current = client.get(f"/tenderproof/continuous/document-review/{run_id}/current")
                item["current_status"] = current.status_code
                item["current"] = current.json()
                review = client.get(f"/tenderproof/continuous/document-review/{run_id}")
                item["review_status"] = review.status_code
                item["review"] = review.json()
                if review.status_code == 200 and not review.json().get("pending"):
                    proposal = client.post("/tenderproof/publications/proposals", json={"run_id": run_id})
                    item["proposal_status"] = proposal.status_code
                    item["proposal"] = proposal.json()
            except Exception as exc:  # preserve per-run progress and continue
                item["error"] = f"{type(exc).__name__}: {exc}"
            result["runs"][label] = item
    output = Path("/var/lib/observador/tenderproof/product-completion/lote-01-review")
    output.mkdir(parents=True, exist_ok=True)
    (output / "preparation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
