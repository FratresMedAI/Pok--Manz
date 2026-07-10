"""Summarize downloaded Kaggle public leaderboard CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/leaderboard/pokemon-tcg-ai-battle-publicleaderboard-2026-07-10T09_45_40.csv")
    parser.add_argument("--out", default="data/processed/leaderboard_summary.json")
    args = parser.parse_args()

    path = ROOT / args.csv
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            row["Rank"] = int(row["Rank"])
            row["Score"] = float(row["Score"])
            row["SubmissionCount"] = int(row["SubmissionCount"])
            rows.append(row)

    top = rows[:25]
    scores = [row["Score"] for row in rows]
    summary = {
        "source": str(path),
        "teams": len(rows),
        "top_score": max(scores) if scores else None,
        "median_score": sorted(scores)[len(scores) // 2] if scores else None,
        "score_90th_percentile": sorted(scores)[int(len(scores) * 0.9)] if scores else None,
        "top_25": [
            {
                "rank": row["Rank"],
                "team_id": row["TeamId"],
                "team_name": row["TeamName"],
                "score": row["Score"],
                "last_submission": row["LastSubmissionDate"],
                "submissions": row["SubmissionCount"],
            }
            for row in top
        ],
    }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote leaderboard summary for {len(rows)} teams to {out}")


if __name__ == "__main__":
    main()

