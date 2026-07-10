"""Validate proposed natural-language deck cards against official CABT card data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.cards import load_card_csv, normalize_name


PROPOSED_DRAGAPULT = {
    "Dreepy": 4,
    "Drakloak": 2,
    "Dragapult ex": 3,
    "Pidgey": 2,
    "Pidgeot ex": 2,
    "Rotom V": 1,
    "Radiant Alakazam": 2,
    "Fezandipiti ex": 1,
    "Buddy-Buddy Poffin": 4,
    "Ultra Ball": 4,
    "Nest Ball": 3,
    "Rare Candy": 4,
    "Earthen Vessel": 2,
    "Prime Catcher": 1,
    "Super Rod": 1,
    "Professor's Research": 4,
    "Iono": 3,
    "Arven": 3,
    "Boss's Orders": 2,
    "Basic {R} Energy": 4,
    "Basic {P} Energy": 4,
}


PROPOSED_OGERPON_WALL = {
    "Cornerstone Mask Ogerpon ex": 3,
    "Teal Mask Ogerpon ex": 3,
    "Riolu": 2,
    "Lucario": 2,
    "Squawkabilly ex": 1,
    "Fezandipiti ex": 1,
    "Nest Ball": 4,
    "Ultra Ball": 4,
    "Earthen Vessel": 4,
    "Energy Switch": 3,
    "Switch Cart": 2,
    "Enhanced Hammer": 2,
    "Prime Catcher": 1,
    "Super Rod": 2,
    "Professor's Research": 4,
    "Iono": 4,
    "Boss's Orders": 3,
    "Battle Cage": 2,
    "Basic {F} Energy": 8,
    "Basic {G} Energy": 4,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official", default="data/raw/EN_Card_Data.csv")
    parser.add_argument("--out", default="data/processed/proposed_deck_validation.json")
    args = parser.parse_args()

    cards = load_card_csv(ROOT / args.official)
    name_index: dict[str, list[dict]] = {}
    for card in cards.values():
        name_index.setdefault(normalize_name(card.name), []).append(
            {"card_id": card.card_id, "name": card.name, "hp": card.hp, "tags": list(card.tags)}
        )

    def validate(deck: dict[str, int]) -> dict:
        result = {"found": {}, "missing": {}, "total_requested": sum(deck.values()), "total_resolved": 0}
        for name, count in deck.items():
            matches = name_index.get(normalize_name(name), [])
            if matches:
                result["found"][name] = {"count": count, "matches": matches}
                result["total_resolved"] += count
            else:
                result["missing"][name] = count
        return result

    report = {
        "dragapult_proposed": validate(PROPOSED_DRAGAPULT),
        "ogerpon_wall_proposed": validate(PROPOSED_OGERPON_WALL),
    }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote deck validation to {out}")


if __name__ == "__main__":
    main()

