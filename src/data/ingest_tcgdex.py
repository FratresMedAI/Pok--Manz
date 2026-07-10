"""Offline TCGdex metadata ingestion.

Run this outside Kaggle evaluation to cache public card metadata. The submitted
agent must never call network APIs during matches.
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://api.tcgdex.net/v2/en/cards"


def fetch_card(card_id: str) -> dict:
    url = f"{BASE_URL}/{urllib.parse.quote(card_id)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("card_ids", nargs="+", help="TCGdex card IDs such as sv06-130")
    parser.add_argument("--out", default="data/external/tcgdex_cards.json")
    args = parser.parse_args()

    records = []
    for card_id in args.card_ids:
        records.append(fetch_card(card_id))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} TCGdex records to {out}")


if __name__ == "__main__":
    main()

