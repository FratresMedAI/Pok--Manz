"""Parse Card_ID List_EN.pdf into machine-readable indexes."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
LINE_RE = re.compile(r"^(\d+)\s+(.+?)\s+([A-Z0-9]+)\s+([A-Z0-9]+)\s+View Image$")
NO_EXPANSION_LINE_RE = re.compile(r"^(\d+)\s+(.+?)\s+([A-Z0-9]+)\s+View Image$")


def parse_pdf(path: Path) -> list[dict[str, str | int]]:
    reader = PdfReader(str(path))
    records: list[dict[str, str | int]] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = " ".join(raw_line.strip().split())
            match = LINE_RE.match(line)
            if match:
                card_id, name, expansion, collection_no = match.groups()
            else:
                fallback_match = NO_EXPANSION_LINE_RE.match(line)
                if not fallback_match:
                    continue
                card_id, name, collection_no = fallback_match.groups()
                expansion = ""
            records.append(
                {
                    "card_id": int(card_id),
                    "name": name,
                    "expansion": expansion,
                    "collection_no": collection_no,
                }
            )
    records.sort(key=lambda record: int(record["card_id"]))
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="data/raw/Card_ID List_EN.pdf")
    parser.add_argument("--json", default="data/processed/card_id_list_en.json")
    parser.add_argument("--csv", default="data/processed/card_id_list_en.csv")
    args = parser.parse_args()

    records = parse_pdf(ROOT / args.pdf)
    json_path = ROOT / args.json
    csv_path = ROOT / args.csv
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["card_id", "name", "expansion", "collection_no"])
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} records to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()

