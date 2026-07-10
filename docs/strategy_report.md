# Pokemon TCG AI Battle Strategy Report

## Executive Summary

This submission uses a deterministic hybrid agent. It starts from a stable Mega Lucario ex deck and ranks legal CABT options with phase-aware heuristics, matchup tags, prize pressure, resource safety, and a clock-guarded fallback.

## Deck Overview

- Deck size: 60
- Unique cards: 17
- Strategic roles: 10

| Card ID | Card | Copies | Role |
|---:|---|---:|---|
| 6 | Basic {F} Energy | 13 | Energy |
| 1192 | Carmine | 4 | Draw Support |
| 1102 | Dusk Ball | 4 | Search |
| 1142 | Fighting Gong | 4 | Search |
| 1227 | Lillie's Determination | 4 | Draw Support |
| 678 | Mega Lucario ex | 4 | Primary Attacker |
| 1152 | Poké Pad | 4 | Search |
| 1141 | Premium Power Pro | 4 | Other |
| 677 | Riolu | 3 | Evolution Line |
| 676 | Solrock | 3 | Secondary Attacker |
| 1182 | Boss’s Orders | 2 | Board Control |
| 1252 | Gravity Mountain | 2 | Board Control |
| 674 | Hariyama | 2 | Secondary Attacker |
| 675 | Lunatone | 2 | Other |
| 673 | Makuhita | 2 | Evolution Line |
| 1123 | Switch | 2 | Mobility |
| 1159 | Hero’s Cape | 1 | Durability |

## Role Distribution

- Energy: 13 cards
- Search: 12 cards
- Draw Support: 8 cards
- Other: 6 cards
- Evolution Line: 5 cards
- Secondary Attacker: 5 cards
- Primary Attacker: 4 cards
- Board Control: 4 cards
- Mobility: 2 cards
- Durability: 1 cards

## Agent Architecture

| Metric | Value |
|---|---:|
| Classes | 0 |
| Functions | 7 |
| Global constants | 6 |
| Conditional branches | 25 |
| For loops | 4 |
| Return statements | 23 |
| Unique calls | 40 |

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
