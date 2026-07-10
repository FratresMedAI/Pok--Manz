"""Validate a CABT submission deck.csv."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.cards import load_card_csv


def read_deck(path: Path) -> list[int]:
    return [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_basic_energy_name(name: str) -> bool:
    return name.startswith("Basic {") and name.endswith("} Energy")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", default="submission/deck.csv")
    parser.add_argument("--cards", default="data/raw/EN_Card_Data.csv")
    args = parser.parse_args()

    deck_path = ROOT / args.deck
    registry = load_card_csv(ROOT / args.cards)
    deck = read_deck(deck_path)
    errors: list[str] = []

    if len(deck) != 60:
        errors.append(f"deck must contain 60 cards, found {len(deck)}")

    counts = Counter(deck)
    for card_id, count in sorted(counts.items()):
        card = registry.get(card_id)
        if card is None:
            errors.append(f"unknown card ID {card_id}")
            continue
        if count > 4 and not is_basic_energy_name(card.name):
            errors.append(f"{card.name} ({card_id}) has {count} copies; max 4")

    if errors:
        print("Deck validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Deck validation passed: {len(deck)} cards, {len(counts)} unique IDs")


if __name__ == "__main__":
    main()

