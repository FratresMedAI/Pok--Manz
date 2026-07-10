"""Merge official Kaggle card data with optional external metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.cards import CardFeature, load_card_csv, normalize_name


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def index_external(records: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for record in records:
        name = normalize_name(record.get("name", ""))
        if not name:
            continue
        index.setdefault(name, []).append(record)
    return index


def enrich_card(card: CardFeature, external_index: dict[str, list[dict]]) -> dict:
    records = external_index.get(normalize_name(card.name), [])
    best = records[0] if records else {}
    return {
        "card_id": card.card_id,
        "name": card.name,
        "card_type": card.card_type,
        "stage_or_type": card.stage_or_type,
        "hp": card.hp,
        "rule": card.rule,
        "weakness": card.weakness,
        "resistance": card.resistance,
        "retreat": card.retreat,
        "tags": list(card.tags),
        "external": {
            "matched": bool(best),
            "source_id": best.get("id"),
            "regulation_mark": best.get("regulationMark"),
            "legalities": best.get("legalities") or best.get("legal"),
            "rules": best.get("rules", []),
            "attacks": best.get("attacks", []),
            "abilities": best.get("abilities", []),
            "confidence": "name_exact" if best else "none",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official", default="data/raw/EN_Card_Data.csv")
    parser.add_argument("--tcgdex", default="data/external/tcgdex_cards.json")
    parser.add_argument("--pokemontcg", default="data/external/pokemontcg_io_cards.json")
    parser.add_argument("--out", default="data/processed/card_registry.json")
    args = parser.parse_args()

    official = load_card_csv(args.official)
    external_records = load_json(Path(args.tcgdex)) + load_json(Path(args.pokemontcg))
    external_index = index_external(external_records)
    merged = {str(card_id): enrich_card(card, external_index) for card_id, card in official.items()}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(merged)} merged card records to {out}")


if __name__ == "__main__":
    main()

