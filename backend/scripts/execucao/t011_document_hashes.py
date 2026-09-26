"""Read-only manifest check for T011's eight preserved documents.

This script only reads the compact runtime index and prints the selected IDs;
it never opens a database connection for writing and never creates proposals.
"""
import json
from pathlib import Path

IDS = {17, 18, 20, 21, 22, 23, 24, 25}


def main() -> None:
    index = Path(__file__).parents[2] / ".tenderproof" / "product-completion" / "T004-INDICE-DOCUMENTOS-32-runtime-compact.json"
    data = json.loads(index.read_text(encoding="utf-8"))
    for record in sorted(data["records"], key=lambda item: item["concurso_id"]):
        if record["concurso_id"] in IDS:
            print(record["concurso_id"], record["run_id"], record["artifact_sha256"], record["artifact_path"])
    payload = Path(__file__).parents[2].parent / "docs" / "execucao" / "evidencias" / "T011" / "ID17-payload-local.json"
    body = json.loads(payload.read_text(encoding="utf-8"))
    proposed = body["proposed"]
    assert body["status"] == "EM_REVISAO" and body["authorization"]["human_read"] is False
    assert len(proposed["cargos"]) == 27 and sum(item["vagas"] for item in proposed["cargos"]) == proposed["vagas"] == 79
    assert body["artifact"]["sha256"] == next(r["artifact_sha256"] for r in data["records"] if r["concurso_id"] == 17)
    print("ID17 local payload: valid (27 cargos, 79 vagas, no mutation)")


if __name__ == "__main__":
    main()
