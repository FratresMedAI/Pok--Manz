# PokeMayne Pod Gauntlet Results

Last updated: 2026-07-10 08:18 UTC-4

## Dragapult v4 — COMPLETE

| Metric | Value |
|--------|-------|
| **Win rate** | **43.2%** |
| **Record** | 134W / 176L / 0D |
| **Errors** | 0 |
| **Workers** | 31 |
| **Avg loss turns** | 120.9 |
| **Code** | `52bfa26` |
| **Log** | `logs/vs_alakazam_dragapult_v4.log` |

### Anti-Alakazam pivot stack (v4)

- `check_anti_alakazam_overrides()` — Mist Energy priority, Dunsparce-over-Abra snipe, timed Xerosic/Hand Trimmer
- `simulator_exploits.py` — Articuno stall, Unfair Stamp, Bronzong jammer proxy
- `hail_mary_tactics.py` — deckout trap, Survival Brace bait, fast-pass clock safety
- `sneaky_board_manipulation.py` — gust trap, poison checkup, deck clutter
- Deck tech: 2× Xerosic, 2× Hand Trimmer, 2× Mist Energy, Brute Bonnet, Munkidori, Pokémon Catcher

---

## Prior Runs (reference)

| Matchup | Win rate | Record | Errors | Notes |
|---------|----------|--------|--------|-------|
| Dragapult v1 | 35.5% | 110W / 200L | 0 | Pre-pivot code |
| Ogerpon wall | 24.2% | 75W / 235L | 0 | Cornerstone immunity wall |
| Lucario vs baseline | 65.5% | 609W / 321L | 0 | Not vs Alakazam |

---

## Best counter so far

**Iron Thorns** at **68.7%** vs Alakazam control — default deck candidate for submission.

| Deck | vs Alakazam |
|------|-------------|
| **Iron Thorns v4** | **68.7%** |
| Dragapult v4 | 43.2% |
| Ogerpon wall | 24.2% |

---

## Iron Thorns v4 — COMPLETE ✓

| Metric | Value |
|--------|-------|
| **Win rate** | **68.7%** |
| **Record** | 213W / 97L / 0D |
| **Errors** | 0 |
| **Workers** | 31 |
| **Avg loss turns** | 95.9 |
| **Code** | `52bfa26` |
| **Log** | `logs/vs_alakazam_iron_thorns_v4.log` |

**Best Alakazam counter by a wide margin.** Zero-bench + Initialization ability-lock outperforms Dragapult snipe.

### Telemetry read (v4)

| Signal | Value | Meaning |
|--------|-------|---------|
| Errors | **0** | Legal-index gates solid — no corrupted submissions |
| Avg loss turns | **95.9** | Losses are deep grinds, not blowouts — lock is working |

### Pre-rebuild safety tweaks (v5 — coded, not yet gauntlet-tested)

1. **Deck-decay brake** — when `deckCount <= 10` + zero bench: block draw supporters / Ultra Ball (`-6500`)
2. **Micro-clock squeezer** — Iron Thorns lock vs control: favor fast `END` (`+5400`), penalize non-essential plays

Target: squeeze **+2–3%** by cutting inversion deckouts and long-loss micro-loops.

---

## Queued / In Progress

- Pod **idle** — no active gauntlet runs

---

## Pod

- SSH: `ssh root@64.247.206.229 -p 18611 -i ~/.ssh/id_ed25519`
- Repo: `/workspace/PokeManzRepo_47ee321`
- Venv: `.venv/bin/python`
- Max workers: **31**

---

# Kaggle Leaderboard Targets (Realistic)

Agent vs agent — win rate matters, but **who you beat** and **consistency** matter more.

| Placement | Est. overall win rate | Notes |
|-----------|----------------------|-------|
| Top 10 | 55–62% | Beating most average agents |
| Top 5 | 62–68% | Strong vs mid-tier and some top agents |
| **Top 3** | **68–75%+** | Must beat or go even with other strong agents consistently |
| #1 | 75%+ | Very strong meta understanding + execution |

### Important realities

- **Vs strong control (Alakazam):** Even **45–50%** can be good if you beat other popular strategies.
- **Dragapult v4 at 43.2%** vs Alakazam is decent progress — push to **50%+** for a real Top 3 path.
- Leaderboard likely dominated by **hybrid agents** (neural net + search/planning). Pure RL struggles more.

### Bottom line for Top 3

- Need **~70%+ overall** across a wide field.
- More importantly: strong results against **actual top agents**, not just random ones.

---

# Turning Gauntlet Results into Training Signals

Currently the gauntlet is mostly **evaluation**. Below is how to convert it into stronger training.

## A. Gauntlet losses = high-value training data

Losses vs Alakazam (and other strong decks) are gold.

- Extract replays from losing games
- Use for **imitation learning** (what strong play looks like)
- Use for **hard negative mining** (positions where we fail)

**Repo tools already exist:**

- `src/replay_mining.py` → `data/processed/replay_examples.jsonl`
- `src/train_imitation_profile.py` → `submission/imitation_profile.json`
- Enable with `POKEMAYNE_USE_IMITATION=1` in submission

## B. Shaped reward signals (beyond +1/-1)

| Signal | What to reward |
|--------|----------------|
| Anti-control bonus | Beating stall/control decks (Alakazam, etc.) |
| Prize racing efficiency | Taking prizes faster than opponent |
| Disruption success | Successful Xerosic, Hand Trimmer, Unfair Stamp plays |
| Energy management | Penalize brick games vs control |

**Already partially wired in heuristic layers:** `anti_psychic_control.py`, `sneaky_board_manipulation.py`, `hail_mary_tactics.py`

## C. Curriculum learning from gauntlet

Build a difficulty curve:

1. Start training mostly vs weaker/mid agents
2. Gradually increase % of games vs Alakazam + strong control as win rate improves
3. **Milestone:** When Dragapult hits **~48–50%** vs Alakazam → increase its weight in training mix

| Phase | Alakazam gauntlet weight | Trigger |
|-------|-------------------------|---------|
| Current | 100% (diagnostic) | Baseline measurement |
| Next | 60% Alakazam + 40% other | Dragapult ≥ 48% vs Alakazam |
| Target | 40% Alakazam + 60% wide field | Overall ≥ 55% across mixed gauntlet |

## D. Immediate priorities

1. **#1 priority:** Improve vs Alakazam control (biggest weakness)
2. Keep running gauntlet after every major change
3. **Save replay logs** from pod runs — high value for imitation
4. **Add second strong control deck** to gauntlet soon (avoid overfitting to one Alakazam list)
   - Candidates: Mega Kangaskhan ex, Noctowl shell (from replay mining notes)

## Next gauntlet queue (after Iron Thorns v4)

1. Iron Thorns v4 result → compare vs Dragapult 43.2%
2. Mixed-field eval: Dragapult vs Lucario baseline + random sample agent
3. Second control deck mirror match (Kangaskhan or mined list from `data/processed/replay_summary.json`)


## Dragapult v4 — COMPLETE

| Metric | Value |
|--------|-------|
| **Win rate** | **43.2%** |
| **Record** | 134W / 176L / 0D |
| **Errors** | 0 |
| **Workers** | 31 |
| **Avg loss turns** | 120.9 |
| **Code** | `52bfa26` |
| **Log** | `logs/vs_alakazam_dragapult_v4.log` |

### Anti-Alakazam pivot stack (v4)

- `check_anti_alakazam_overrides()` — Mist Energy priority, Dunsparce-over-Abra snipe, timed Xerosic/Hand Trimmer
- `simulator_exploits.py` — Articuno stall, Unfair Stamp, Bronzong jammer proxy
- `hail_mary_tactics.py` — deckout trap, Survival Brace bait, fast-pass clock safety
- `sneaky_board_manipulation.py` — gust trap, poison checkup, deck clutter
- Deck tech: 2× Xerosic, 2× Hand Trimmer, 2× Mist Energy, Brute Bonnet, Munkidori, Pokémon Catcher

---

## Prior Runs (reference)

| Matchup | Win rate | Record | Errors | Notes |
|---------|----------|--------|--------|-------|
| Dragapult v1 | 35.5% | 110W / 200L | 0 | Pre-pivot code |
| Ogerpon wall | 24.2% | 75W / 235L | 0 | Cornerstone immunity wall |
| Lucario vs baseline | 65.5% | 609W / 321L | 0 | Not vs Alakazam |

---

## Best counter so far

**Dragapult snipe** at **43.2%** vs Alakazam control — +7.7 pts over v1.

---

## Queued / In Progress

- **Iron Thorns v4** vs Alakazam — `52bfa26`, 31 workers, 310 games — **RUNNING** (started 08:09)
  - Log: `logs/vs_alakazam_iron_thorns_v4.log`

---

## Pod

- SSH: `ssh root@64.247.206.229 -p 18611 -i ~/.ssh/id_ed25519`
- Repo: `/workspace/PokeManzRepo_47ee321`
- Venv: `.venv/bin/python`
- Max workers: **31**
