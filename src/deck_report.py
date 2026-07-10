"""Create readable deck reports from mined replay summaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_registry(path: Path) -> dict[int, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(card_id): record.get("name", str(card_id)) for card_id, record in data.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="data/processed/replay_summary.json")
    parser.add_argument("--registry", default="data/processed/card_registry.json")
    parser.add_argument("--out", default="data/processed/replay_deck_report.md")
    args = parser.parse_args()

    summaries = json.loads((ROOT / args.summary).read_text(encoding="utf-8"))
    names = load_registry(ROOT / args.registry)
    lines: list[str] = ["# Replay Deck Report", ""]
    for summary in summaries:
        lines.append(f"## {summary['source_file']}")
        lines.append("")
        lines.append(f"- Episode: `{summary['episode_id']}`")
        lines.append(f"- Rewards: `{summary['rewards']}`")
        lines.append(f"- Winner: player `{summary['winner']}`")
        lines.append("")
        for player, deck in sorted(summary.get("decks", {}).items()):
            lines.append(f"### Player {player} Deck")
            lines.append("")
            for card_id, count in sorted(Counter(deck).items(), key=lambda item: (-item[1], names.get(item[0], ""))):
                lines.append(f"- {count}x `{card_id}` {names.get(card_id, 'Unknown')}")
            lines.append("")

    out = ROOT / args.out
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

