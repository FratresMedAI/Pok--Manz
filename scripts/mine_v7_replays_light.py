"""Lightweight replay miner — one file at a time."""

from __future__ import annotations

import argparse
import gc
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ARCHETYPE_CARD_HINTS: dict[str, set[int]] = {
    "crustle_wall": {344, 345, 532, 533, 756},
    "rocket_spidops": {400, 401, 1134, 1216, 1220, 1218, 1257},
    "alakazam_control": {741, 742, 743, 305, 66},
    "dragapult": {119, 120, 121},
    "abomasnow": {418, 419, 722, 723},
    "lucario": {677, 678, 333},
    "starmie": {360, 361, 1030, 1031},
    "mega_poison": {112, 139, 646},
    "iron_thorns": {37},
}


def classify(ids: set[int]) -> str:
    best, score = "unknown", 0
    for name, hints in ARCHETYPE_CARD_HINTS.items():
        hit = len(ids & hints)
        if hit > score:
            score, best = hit, name
    return best if score else "unknown"


def opp_ids(obs: dict, player_index: int) -> set[int]:
    current = obs.get("current") or {}
    players = current.get("players") or []
    if player_index >= len(players):
        return set()
    out: set[int] = set()
    for zone in ("active", "bench"):
        for pokemon in players[player_index].get(zone) or []:
            if pokemon and pokemon.get("id") is not None:
                out.add(int(pokemon["id"]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default="REPLAYS/V7 Replays")
    parser.add_argument("--our-name", default="Kyle Bean")
    parser.add_argument("--sample-every", type=int, default=25)
    args = parser.parse_args()

    folder = Path.cwd() / args.folder
    if not folder.exists():
        print(f"Missing {folder}", file=sys.stderr)
        return 1

    w = l = 0
    by_opp: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    loss_types: Counter[str] = Counter()

    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        teams = data.get("info", {}).get("TeamNames", [])
        if args.our_name not in teams:
            continue
        side = teams.index(args.our_name)
        rewards = data.get("rewards") or []
        won = bool(rewards) and rewards[side] == max(rewards)
        steps = data.get("steps") or []
        votes: Counter[str] = Counter()
        for i, step in enumerate(steps):
            if i % args.sample_every and i != len(steps) - 1:
                continue
            frame = step[side] if isinstance(step, list) else step
            obs = frame.get("observation")
            if not obs:
                continue
            votes[classify(opp_ids(obs, 1 - side))] += 1
        opp = votes.most_common(1)[0][0] if votes else "unknown"
        if won:
            w += 1
            by_opp[opp][0] += 1
        else:
            l += 1
            by_opp[opp][1] += 1
            if steps:
                last = steps[-1][side] if isinstance(steps[-1], list) else steps[-1]
                cur = (last.get("observation") or {}).get("current") or {}
                players = cur.get("players") or [{}, {}]
                our_p = players[side].get("prizeCount") if side < len(players) else None
                opp_p = players[1 - side].get("prizeCount") if 1 - side < len(players) else None
                if our_p == 6:
                    loss_types["board_out"] += 1
                elif opp_p == 0:
                    loss_types["prize_race"] += 1
                else:
                    loss_types["other"] += 1
        del data
        gc.collect()

    total = w + l
    print(f"{args.our_name}: {w}W-{l}L ({100 * w / total:.1f}%)" if total else "no games")
    print("Matchups:")
    for opp, (a, b) in sorted(by_opp.items(), key=lambda x: -(x[1][0] + x[1][1])):
        t = a + b
        print(f"  vs {opp:18s} {a}W-{b}L ({100 * a / t:.0f}%)")
    if loss_types:
        print("Loss types:", dict(loss_types))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
