"""Mine Kaggle CABT replay JSON into training examples.

The output is JSONL so we can use it for imitation learning, evaluator weight
tuning, and matchup scouting without keeping giant episode files in memory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def expand_replay_inputs(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        path = Path(item)
        if not path.is_absolute():
            path = ROOT / path
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.json")))
        elif any(char in str(path) for char in ("*", "?")):
            paths.extend(sorted(path.parent.glob(path.name)))
        else:
            paths.append(path)
    return paths


def card_ids_from_zone(zone: Any) -> list[int]:
    if not isinstance(zone, list):
        return []
    ids: list[int] = []
    for item in zone:
        if isinstance(item, dict) and isinstance(item.get("id"), int):
            ids.append(item["id"])
    return ids


def visible_board_ids(current: dict[str, Any], player_index: int) -> list[int]:
    players = current.get("players") or []
    if player_index >= len(players) or not isinstance(players[player_index], dict):
        return []
    player = players[player_index]
    return card_ids_from_zone(player.get("active")) + card_ids_from_zone(player.get("bench"))


def discard_ids(current: dict[str, Any], player_index: int) -> list[int]:
    players = current.get("players") or []
    if player_index >= len(players) or not isinstance(players[player_index], dict):
        return []
    return card_ids_from_zone(players[player_index].get("discard"))


def option_signature(option: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "type",
        "number",
        "area",
        "index",
        "playerIndex",
        "inPlayArea",
        "inPlayIndex",
        "attackId",
        "cardId",
        "serial",
    )
    return {key: option.get(key) for key in keep if key in option}


def extract_examples(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    episode = json.loads(path.read_text(encoding="utf-8"))
    rewards = episode.get("rewards") or [0, 0]
    winner = 0 if rewards[0] > rewards[1] else 1 if rewards[1] > rewards[0] else None

    examples: list[dict[str, Any]] = []
    decks: dict[str, list[int]] = {}
    for step_index, step in enumerate(episode.get("steps", [])):
        if not isinstance(step, list):
            continue
        for player_index, frame in enumerate(step):
            if not isinstance(frame, dict):
                continue
            action = frame.get("action")
            obs = frame.get("observation") or {}
            select = obs.get("select")
            current = obs.get("current")

            if isinstance(action, list) and len(action) == 60 and all(isinstance(card_id, int) for card_id in action):
                decks[str(player_index)] = action
                continue

            if not isinstance(select, dict) or not isinstance(current, dict):
                continue
            options = select.get("option") or []
            if not isinstance(options, list):
                continue
            selected = action if isinstance(action, list) else []
            if not selected:
                continue

            your_index = current.get("yourIndex", player_index)
            opponent_index = 1 - int(your_index)
            examples.append(
                {
                    "episode_id": episode.get("id"),
                    "source_file": path.name,
                    "step_index": step_index,
                    "player_index": player_index,
                    "is_winner": winner == player_index,
                    "reward": rewards[player_index] if player_index < len(rewards) else None,
                    "select_type": select.get("type"),
                    "select_context": select.get("context"),
                    "min_count": select.get("minCount"),
                    "max_count": select.get("maxCount"),
                    "selected": selected,
                    "option_count": len(options),
                    "selected_options": [
                        option_signature(options[index])
                        for index in selected
                        if isinstance(index, int) and 0 <= index < len(options)
                    ],
                    "my_board_ids": visible_board_ids(current, int(your_index)),
                    "opponent_board_ids": visible_board_ids(current, opponent_index),
                    "my_discard_ids": discard_ids(current, int(your_index)),
                    "opponent_discard_ids": discard_ids(current, opponent_index),
                    "my_deck_count": (current.get("players") or [{}])[int(your_index)].get("deckCount")
                    if current.get("players")
                    else None,
                    "opponent_hand_count": (current.get("players") or [{}, {}])[opponent_index].get("handCount")
                    if current.get("players")
                    else None,
                }
            )

    summary = {
        "episode_id": episode.get("id"),
        "source_file": path.name,
        "rewards": rewards,
        "winner": winner,
        "statuses": episode.get("statuses"),
        "steps": len(episode.get("steps", [])),
        "decks": decks,
        "examples": len(examples),
        "winner_examples": sum(1 for example in examples if example["is_winner"]),
    }
    return examples, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("replays", nargs="*", default=["data/replays/85181209.json"])
    parser.add_argument("--out", default="data/processed/replay_examples.jsonl")
    parser.add_argument("--summary", default="data/processed/replay_summary.json")
    parser.add_argument("--winner-only", action="store_true")
    args = parser.parse_args()

    all_examples: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for replay_path in expand_replay_inputs(args.replays):
        examples, summary = extract_examples(replay_path)
        if args.winner_only:
            examples = [example for example in examples if example["is_winner"]]
        all_examples.extend(examples)
        summaries.append(summary)

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for example in all_examples:
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")

    summary_path = ROOT / args.summary
    summary_path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(all_examples)} examples to {out}")
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()

