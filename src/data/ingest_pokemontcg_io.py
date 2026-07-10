"""Offline PokemonTCG.io metadata ingestion."""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "https://api.pokemontcg.io/v2/cards"


def search_cards(query: str, page_size: int = 250) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "pageSize": page_size})
    request = urllib.request.Request(f"{BASE_URL}?{params}")
    api_key = os.environ.get("POKEMONTCG_IO_API_KEY")
    if api_key:
        request.add_header("X-Api-Key", api_key)
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("data", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default='regulationMark:H OR regulationMark:I OR regulationMark:J')
    parser.add_argument("--out", default="data/external/pokemontcg_io_cards.json")
    args = parser.parse_args()

    records = search_cards(args.query)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} PokemonTCG.io records to {out}")


if __name__ == "__main__":
    main()

