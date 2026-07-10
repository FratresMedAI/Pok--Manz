"""Generate a Strategy-track style report for the current submission."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.cards import CardFeature, load_card_csv


ROLE_KEYWORDS = {
    "Primary Attacker": ("Mega Lucario", "Alakazam", "Dragapult", "Cornerstone Mask Ogerpon"),
    "Secondary Attacker": ("Hariyama", "Solrock", "Fezandipiti", "Shaymin", "Dunsparce"),
    "Evolution Line": ("Riolu", "Makuhita", "Abra", "Kadabra", "Dreepy", "Drakloak"),
    "Search": ("Ball", "Poffin", "Rare Candy", "Pad", "Crispin"),
    "Draw Support": ("Carmine", "Determination", "Hilda", "Dawn", "Research", "Draw"),
    "Mobility": ("Switch", "Catcher"),
    "Board Control": ("Boss", "Hammer", "Xerosic", "Nighttime Mine", "Gravity Mountain"),
    "Durability": ("Cape", "Battle Cage", "Mist Energy", "Legacy Energy"),
    "Energy": ("Energy",),
}


class ArchitectureAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.classes: set[str] = set()
        self.functions: set[str] = set()
        self.globals: set[str] = set()
        self.ifs = 0
        self.fors = 0
        self.returns = 0
        self.calls: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                self.globals.add(target.id)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.ifs += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.fors += 1
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self.returns += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)


def read_deck(path: Path) -> list[int]:
    return [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def assign_role(card: CardFeature) -> str:
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword.lower() in card.name.lower() for keyword in keywords):
            return role
    if "multi_prize" in card.tags:
        return "Attacker"
    if "search" in card.tags:
        return "Search"
    if "draw" in card.tags:
        return "Draw Support"
    if "energy" in card.tags:
        return "Energy"
    return "Other"


def deck_table(deck: list[int], registry: dict[int, CardFeature]) -> tuple[list[str], Counter[str]]:
    rows = []
    roles: Counter[str] = Counter()
    for card_id, copies in sorted(Counter(deck).items(), key=lambda item: (-item[1], registry.get(item[0], CardFeature(item[0], "")).name)):
        card = registry.get(card_id, CardFeature(card_id, f"Unknown {card_id}"))
        role = assign_role(card)
        roles[role] += copies
        rows.append(f"| {card_id} | {card.name} | {copies} | {role} |")
    return rows, roles


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", default="data/raw/EN_Card_Data.csv")
    parser.add_argument("--deck", default="submission/deck.csv")
    parser.add_argument("--agent", default="submission/main.py")
    parser.add_argument("--out", default="docs/strategy_report.md")
    args = parser.parse_args()

    registry = load_card_csv(ROOT / args.cards)
    deck = read_deck(ROOT / args.deck)
    rows, roles = deck_table(deck, registry)

    tree = ast.parse((ROOT / args.agent).read_text(encoding="utf-8"))
    analyzer = ArchitectureAnalyzer()
    analyzer.visit(tree)

    role_lines = [f"- {role}: {count} cards" for role, count in roles.most_common()]
    report = f"""# Pokemon TCG AI Battle Strategy Report

## Executive Summary

This submission uses a deterministic hybrid agent. It starts from a stable Mega Lucario ex deck and ranks legal CABT options with phase-aware heuristics, matchup tags, prize pressure, resource safety, and a clock-guarded fallback.

## Deck Overview

- Deck size: {len(deck)}
- Unique cards: {len(set(deck))}
- Strategic roles: {len(roles)}

| Card ID | Card | Copies | Role |
|---:|---|---:|---|
{chr(10).join(rows)}

## Role Distribution

{chr(10).join(role_lines)}

## Agent Architecture

| Metric | Value |
|---|---:|
| Classes | {len(analyzer.classes)} |
| Functions | {len(analyzer.functions)} |
| Global constants | {len(analyzer.globals)} |
| Conditional branches | {analyzer.ifs} |
| For loops | {analyzer.fors} |
| Return statements | {analyzer.returns} |
| Unique calls | {len(analyzer.calls)} |

## Strategic Systems

- Opening: search, setup, and evolution velocity are prioritized.
- Midgame: matchup tags adjust target selection, bench discipline, and resource denial.
- Endgame: attacks, gust cards, low-HP targets, and single-prize pivots receive elevated priority.
- Hidden information: a state tracker records deck-search windows and estimates known prize contents.
- Runtime safety: if evaluation runs long or errors, the agent falls back to a fast velocity policy.

## Replay/Leaderboard Data

The repository includes replay mining and leaderboard summary tools:

- `src/replay_mining.py`
- `src/train_imitation_profile.py`
- `src/deck_report.py`
- `src/leaderboard_report.py`

Current replay analysis identified Alakazam/Dunsparce control and Mega Kangaskhan ex as important ladder archetypes. Alakazam control support exists behind `POKEMAYNE_DECK=alakazam`, but the packaged default remains Lucario until the control policy beats the local gauntlet reliably.
"""

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

