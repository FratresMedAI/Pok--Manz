"""Train a tiny imitation profile from mined replay examples.

This is not a neural model. It is a compact count/bonus table that can be
shipped safely inside Kaggle submissions and used to bias heuristic scores.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def key_for_option(context: Any, option: dict[str, Any]) -> str:
    parts = [f"context={context}", f"type={option.get('type')}"]
    for field in ("cardId", "attackId", "area", "inPlayArea"):
        if option.get(field) is not None:
            parts.append(f"{field}={option[field]}")
    return "|".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", default="data/processed/replay_examples.jsonl")
    parser.add_argument("--out", default="submission/imitation_profile.json")
    parser.add_argument("--max-bonus", type=float, default=125.0)
    args = parser.parse_args()

    counts: Counter[str] = Counter()
    context_counts: Counter[str] = Counter()
    deck_counts: dict[str, Counter[int]] = defaultdict(Counter)

    examples_path = ROOT / args.examples
    with examples_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            example = json.loads(line)
            context = example.get("select_context")
            context_counts[str(context)] += 1
            for option in example.get("selected_options", []):
                counts[key_for_option(context, option)] += 1
            for card_id in example.get("my_board_ids", []):
                deck_counts["winner_board"][int(card_id)] += 1

    max_count = max(counts.values(), default=1)
    profile = {
        "version": 1,
        "source": str(examples_path),
        "num_option_keys": len(counts),
        "context_counts": dict(context_counts),
        "option_bonuses": {
            key: round(args.max_bonus * count / max_count, 3)
            for key, count in counts.items()
        },
        "winner_board_counts": {
            str(card_id): count for card_id, count in deck_counts["winner_board"].most_common()
        },
    }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote imitation profile with {len(counts)} option keys to {out}")


if __name__ == "__main__":
    main()

