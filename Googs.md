# PokeMayne Pod Gauntlet Results

Last updated: 2026-07-11 17:55 UTC-4

## Iron Thorns v4-3 — Kaggle Ladder (enum-fix build)

Folder `REPLAYS/v4-2 Replays/` is **mislabeled** — this batch is **v4-3** (second v4 upload with `option_utils.py` enum fix + bench reserve).

| Metric | Value |
|--------|-------|
| **Win rate** | **46.2%** (12W / 14L) |
| **Avg steps (W)** | 84.4 |
| **Avg steps (L)** | 70.6 |
| **Board-out losses** | **0** (bench reserve fix worked) |
| **Going first** | 1W–3L |
| **Going second** | 11W–11L |
| **Action prefix bias** | 80.2% (down from ~100% pre-fix) |

### Loss breakdown by opponent

| Archetype | W | L |
|-----------|---|---|
| Abomasnow/Kyogre | 4 | 3 |
| Dragapult | 2 | 2 |
| Alakazam | 1 | 2 |
| Lucario | 0 | 2 |
| Other (Archaludon, Starmie, Walrein, Ogerpon, Ethan fire) | 5 | 5 |

**Takeaway:** Bench-outs solved; ladder losses are now matchup-speed and off-meta heuristics (anti-control only fired vs Alakazam).

---

## Iron Thorns v5 Take One — Kaggle Ladder (463.0 public score)

Folder: `REPLAYS/v5 Replays/` — **39 unique games** (40 files; `85297418.json` duplicated as `85297418(1).json`).

| Metric | v4-3 | v5 Take One | Δ |
|--------|------|-------------|---|
| **Public score** | 431.7 | **463.0** | **+31.3** |
| **Win rate** | 46.2% (12W–14L) | 46.2% (18W–21L deduped) | flat |
| **Avg steps (W)** | 84.4 | 85.2 | — |
| **Avg steps (L)** | 70.6 | 60.8 | faster losses |
| **Board-out losses** | 0 | **0** | held |
| **Going first** | 1W–3L | 1W–1L | improved |
| **Going second** | 11W–11L | 17W–21L | more volume |
| **Prefix-action bias** | 80.2% | 81.9% | still high |

### Matchup record (v5)

| Opponent | W | L | WR | v4-3 WR |
|----------|---|---|-----|---------|
| **Alakazam** | 5 | 3 | **62.5%** | 33% |
| **Dragapult** | 3 | 0 | **100%** | 50% |
| **Starmie** | 2 | 1 | 67% | — |
| **Abomasnow/Kyogre** | 2 | 6 | **25%** | 57% |
| **Lucario** | 0 | 3 | **0%** | 0% |
| **Archaludon** | 0 | 3 | **0%** | — |
| **Mega poison/Munkidori** | 0 | 3 | **0%** | — |
| **Ogerpon** | 1 | 1 | 50% | — |
| **Other** | 4 | 1 | 80% | — |

**Takeaway:** Score jumped +31 despite flat WR — Alakazam and Dragapult wins improved sharply (target matchups working). **Abomasnow regressed hard** (2–6). Lucario/Archaludon/poison box still 0–3. Prefix bias still ~82% → `play_mode` wiring is next priority.

### v5 loss list (priority tuning)

1. **Abomasnow ×6** — Kyogre/Mega Signal acceleration outpaces lock
2. **Lucario ×3** — Fighting Gong speed + Premium Power Pro
3. **Archaludon ×3** — Metal wall + Night Stretcher grind
4. **Mega poison/Munkidori ×3** — Disruption + Spikemuth line
5. **Alakazam ×3** — Mixed lists (Hop tech, partial lines); still net positive 5–3

---

## Iron Thorns v5 Take Two — REGRESSED (reverted)

Take Two over-stacked `play_mode_bonus` (+3200 ATTACK on `ladder_pressure`, +4600 on `endgame_rush`) on top of `anti_control_bonus` — **changed 73% of Alakazam game decisions**, breaking the 5W–3L line that drove the 463 score.

### v5 Take 2.1 hotfix (upload this)

| Fix | Why |
|-----|-----|
| Removed global `play_mode` score bonuses | Let `anti_control_bonus` own Alakazam exclusively |
| Reverted `ladder_matchup_bonus` to Take One values | Take Two inflation hurt more than it helped |
| Opponent-specific nudges only, confidence ≥ 0.2 | Small Boss/Hammer trims for Abomasnow/Lucario/Archaludon/poison |
| Skip all `play_mode_bonus` when `psychic_control` tags fire | No double-stacking vs Alakazam |

Upload: `artifacts/submission.tar.gz` as **v5 Take 2.1** (or re-upload Take One logic)

---

## Iron Thorns v5 Replays-2 batch (31 games)

Likely **Take Two** upload (pre-hotfix) — Alakazam line collapsed.

| Metric | v5 Take One | Replays-2 | Δ |
|--------|-------------|-----------|---|
| **Win rate** | 46.2% (18W–21L deduped) | **45.2%** (14W–17L) | slight down |
| **Alakazam** | 5W–3L (62.5%) | **0W–3L** | **collapsed** |
| **Dragapult** | 3W–0L | 1W–1L | regressed |
| **Abomasnow** | 2W–6L | **5W–3L** | improved |
| **Lucario** | 0W–2L deduped | **2W–2L** | improved |
| **Starmie** | 2W–1L | 1W–3L | worse |
| **Board-outs** | 0 | 0 | held |
| **Prefix bias** | 82.0% | 84.6% | worse |

**Diagnosis:** Take Two's global `play_mode` attack bonuses traded Alakazam/Dragapult wins for Abomasnow/Lucario — net loss on ladder score. Confirms hotfix direction.

**Replays-2 losses:** Alakazam ×3, Abomasnow ×3, Starmie ×3, Lucario ×2, Ogerpon/Crustle ×2, Dragapult ×1, Zacian/Xerneas/Cynthia shells ×3.

**Action:** Upload **Take 2.1** hotfix (`artifacts/submission.tar.gz`) — restores Take One Alakazam stack + light off-meta nudges only.

---

## Iron Thorns v6 — READY

Mined all requested folders:

- `REPLAYS/v4 Replays/` — 16 timing-only logs, no full episode strategy data
- `REPLAYS/v4-3 Replays/` — 26 full games, 12W–14L
- `REPLAYS/v5 Replays/` — 39 unique full games, 18W–21L
- `REPLAYS/v5 Replays-2/` — 31 full games, 14W–17L

### Combined full ladder read

| Archetype | W | L | WR | V6 action |
|-----------|---|---|----|-----------|
| Abomasnow | 11 | 12 | 47.8% | Keep Take Two target gains, no global attack inflation |
| Alakazam | 6 | 8 | 42.9% | Protect anti-control stack; no `play_mode_bonus` |
| Dragapult | 6 | 3 | 66.7% | Preserve v5 Take One target logic |
| Ogerpon/Crustle | 5 | 6 | 45.5% | Add Crustle wall targeting |
| Starmie/Froslass | 3 | 5 | 37.5% | Add Snorunt/Froslass target group |
| Lucario | 2 | 5 | 28.6% | Keep light Riolu/Mega Lucario target nudges |
| Archaludon | 0 | 4 | 0% | Add Zacian/Archaludon target group |
| Mega poison | 0 | 4 | 0% | Add Impidimp/Munkidori disruption target group |
| Zacian/Xerneas/Cynthia shells | 0 | 3 | 0% | Add new archetypes + target groups |

### V6 changes

| Change | Why |
|--------|-----|
| `submission/deck.csv` synced to generated 60-card Iron Thorns list | Avoid stale 59-line deck artifact |
| Alakazam classifier now requires Abra/Kadabra/Alakazam visibility | Prevent Dunsparce-only false positives vs mixed shells |
| `play_mode_bonus` still blocked for psychic control | Preserve the 463-score Alakazam path |
| Iron Thorns resource scoring | Value Hilda / Poké Pad / Night Stretcher; stop rewarding dead Rare Candy |
| Fast setup target groups | Snover/Kyogre, Staryu/Snorunt/Froslass, Riolu/Lucario, Dreepy, Archaludon/Zacian |
| New archetypes | Zacian box, Xerneas box, Cynthia/Garchomp shell |
| Crustle wall targeting | Try to gust/target Dwebble/Crustle before wall stabilizes |

### V6 checks

| Check | Result |
|-------|--------|
| Python compile | PASS |
| Build submission | PASS — `artifacts/submission.tar.gz` |
| Deck length | 60 |
| `play_mode_bonus` on Alakazam frames | **0 / 2676 options** |
| Targeted replay frames | Abomasnow 887, Starmie 478, Crustle 570, Mega poison 356, Archaludon 254, Lucario 213 |

Upload `artifacts/submission.tar.gz` as **v6**.

---

## V7 — Leaderboard Meta Pivot (Crustle/Kangaskhan default)

Mined all **50** games in `REPLAYS/Leaderboard Replays/`. The public ladder meta is not the Alakazam pod we tuned for.

### Leaderboard winner breakdown

| Winner archetype | Wins | Share |
|------------------|------|-------|
| **crustle_wall** (Budew / MPGaming line) | **31** | **62%** |
| rocket_spidops | 8 | 16% |
| alakazam_control | 6 | 12% |
| dragapult | 3 | 6% |
| other | 2 | 4% |

### Head-to-head signals (who beats whom on leaderboard)

| Matchup | W–L for left deck |
|---------|-------------------|
| Crustle vs Alakazam | **16–6** |
| Rocket Spidops vs Crustle | **8–3** |
| Alakazam vs Crustle | 6–16 |

Iron Thorns (our v5 463 pod build) is the wrong default for this field.

### V7 changes

| Change | Why |
|--------|-----|
| **Default deck → `crustle_kangaskhan_deck()`** | Matches 62% of top-replay winners |
| `submission/deck.csv` → Crustle/Kangaskhan 60 | Kaggle blind submit uses this list |
| `crustle_kangaskhan_score_option()` | Poffin/Pokégear setup, Crustle evolve, **skip ex trades** (crustle chip) |
| `crustle_matchup_bonus()` | Alakazam disruption, Rocket gust, mirror tempo |
| `rocket_spidops` archetype + optional deck | #2 leaderboard line for `POKEMAYNE_DECK=rocket_spidops` |
| Strategy router defaults + counter map | Blind play crustle; telemetry notes ideal counter |
| Iron Thorns anti-Crustle emergency | Penalize ex rushing into walls when `POKEMAYNE_DECK=iron_thorns` |

### Winning 60-card core (mined)

`Dwebble×4, Crustle×4, Mega Kangaskhan ex×4, Poffin×4, Pokégear×4, Jumbo Ice Cream×4, Lillie×4, Hilda×4, Xerosic×4, Mist×4, Spiky×4, Grow Grass×4, Switch×4, Boss×2, Battle Cage×2, Basic G×4`

### V7 env switches

| Env | Deck |
|-----|------|
| *(default)* | `crustle_kangaskhan` |
| `POKEMAYNE_DECK=iron_thorns` | Pod gauntlet build (463 baseline) |
| `POKEMAYNE_DECK=rocket_spidops` | Rocket toolbox |

Upload `artifacts/submission.tar.gz` as **v7**.

---

## V8 — V7 Ladder Loss Targeting (same Crustle deck)

Mined **41** games in `REPLAYS/V7 Replays/` (Kyle Bean, V7 `submission.tar.gz`).

### V7 ladder read

| Metric | Value |
|--------|-------|
| **Record** | **20W–21L (48.8%)** |
| vs Alakazam | 4W–2L (67%) |
| vs Lucario | 5W–4L (56%) |
| vs unknown | 7W–4L (64%) |
| vs Crustle mirror | 2W–3L (40%) |
| **vs Starmie** | **0W–5L (0%)** ← V8 priority |
| **vs Rocket Spidops** | **0W–2L (0%)** |
| vs Mega poison | 0W–1L |

### V8 changes (same 60-card list, smarter pilot)

| Change | Why |
|--------|-----|
| `crustle_matchup_bonus` — **Starmie** | Boss Snorunt/Staryu line, early Crustle pressure, Battle Cage turn ≤6 |
| `crustle_matchup_bonus` — **Rocket** | Earlier Battle Cage, harder Boss on Spidops/Tarountula, Kangaskhan ability race |
| `crustle_matchup_bonus` — **mirror** | Boss Dwebble before evolve, more Jumbo/Lillie tempo, penalize Kangaskhan ex trades harder |
| `crustle_play_mode_bonus()` | Wire disruption/wall/endgame modes into Crustle scoring |
| `crustle_endgame_bonus()` | Prize ≤2: chip with Crustle, Boss finishers, no ex throw |
| Archetype classifier tighten | Crustle wall requires Dwebble/Crustle visible; rogue box needs Clefairy/Mewtwo/Absol |
| Strategy router | Starmie + Mega poison → disruption mode |

Upload `artifacts/submission.tar.gz` as **v8**.

---

## Tomorrow — Strategy Router (deck + play-mode selection)

Scaffold landed in `src/agents/strategy_router.py`. Goal: agent picks **which archetype to pilot** and **which in-game mode** to run.

### Two layers

| Layer | When | Status |
|-------|------|--------|
| **Deck pick** | `obs.select is None` (blind — no opponent info on Kaggle) | Env/default only today (`POKEMAYNE_DECK`, `POKEMAYNE_STRATEGY`) |
| **Play mode** | Once opponent mons visible on board | **Live** — `ability_lock`, `ladder_pressure`, `bench_snipe`, `control_grind`, `wall`, `endgame_rush` |

### Wired tonight

- `build_strategy_plan()` — classifies our deck + opponent archetype + play mode
- `choose_action_indices()` — single policy router (replaces `main.py` if/elif chain)
- `GAUNTLET_MATCHUPS` + `OPPONENT_COUNTER_DECK` tables — pod WR baselines for tomorrow tuning
- Telemetry logs `strategy`, `play_mode`, `opponent` on every decision

### Tomorrow TODO

1. **Feed `play_mode` into scorers** — `counter_policy` / `anti_psychic_control` weight shifts per mode (not just logged)
2. **Opponent-agent registry** — map Kaggle `info.Agents[].Name` → known deck if sim exposes it pre-game
3. **Auto deck select for gauntlet** — `POKEMAYNE_STRATEGY=auto` picks iron_thorns vs alakazam, dragapult vs noctowl, etc.
4. **Replay-mined matchup matrix** — update `OPPONENT_COUNTER_DECK` from v4-3/v5 ladder losses
5. **Multi-deck submission research** — whether Kaggle allows runtime deck swap or only `deck.csv` default

---

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

## Iron Thorns v5 — DONE (500 games)

| Result | Value |
|--------|-------|
| Win rate | **63.2%** (316W–184L) |
| Avg loss turns | **95.6** |
| Opponent timeouts | **0** |
| Verdict | **FAIL** — draw penalty -6500 + END forcing starved resources |

## Iron Thorns v6 — RUNNING (500 games)

| Setting | Value |
|---------|-------|
| Games | **500** |
| Workers | **32** |
| Code | `860c511` |
| Log | `logs/vs_alakazam_iron_thorns_v6.log` |

### v6 patch (vs v5)

| Tweak | v5 | v6 |
|-------|----|----|
| Draw supporter penalty | -6500 | **-2500** |
| Deck-decay threshold | 10 cards | **7 cards** |
| END turn bias | +5400 / +1200 | **removed** |

### v6 pass criteria (vs v4 baseline 68.7%)

| Benchmark | v4 | v6 target |
|-----------|-----|-----------|
| Win rate | 68.7% | **≥ 70.0%** |
| Avg loss turns | 95.9 | **< 95.9** (keep brake, no deckout) |
| Opponent timeouts | 0 | any lift is bonus |

---

## Queued / In Progress

- **Iron Thorns v6** — 500 games, 32 workers — **RUNNING**

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
