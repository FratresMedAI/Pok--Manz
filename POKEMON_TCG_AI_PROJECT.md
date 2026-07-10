# Pokemon TCG AI Battle Challenge - Project Bible

## Goal

Build a Kaggle CABT agent for The Pokemon Company - PTCG AI Battle Challenge Simulation. The agent should play legal Pokemon TCG matches by ranking the engine-provided legal options, not by implementing a separate TCG engine.

## Core Constraint

The simulator is authoritative. Public meta data, TCGdex, PokemonTCG.io, and strategy articles are used only to enrich features and explain strategy. The final Kaggle submission must run offline and must not call network APIs during evaluation.

## Competition Interface

- Submission archive: `submission.tar.gz`
- Required root files: `main.py`, `deck.csv`
- Local SDK: `vendor/cabt_sample_submission/cg`
- Agent function: `agent(obs_dict: dict) -> list[int]`
- Initial deck selection: when `obs.select is None`, return a 60-card deck list.
- Gameplay: return indices into `obs.select.option`.

## Current Strategy

The first build is a robust rule-based + mathematical heuristic agent around the public Mega Lucario ex deck. It prioritizes:

- Turn-by-turn velocity.
- Search/thin before draw/supporter sequencing.
- Prize Value Margin and Net Material Gain.
- Poker-style outs tracking and draw odds.
- Blackjack-style deck richness and EV.
- F1-style deckout risk.
- Fighting-game tempo clocks for setup threats.
- Dragapult-specific low-HP bench discipline.

## Data Sources

- Official CABT docs: https://matsuoinstitute.github.io/cabt/
- Kaggle competition: https://www.kaggle.com/competitions/pokemon-tcg-ai-battle
- TCGdex: https://tcgdex.dev/
- PokemonTCG.io: https://docs.pokemontcg.io/

## Build Path

1. Use `data/raw/EN_Card_Data.csv` and CABT `all_card_data()` as official card sources.
2. Optionally cache external API data into `data/external`.
3. Merge metadata into `data/processed/card_registry.json`.
4. Evaluate locally against random/sample agents.
5. Package with `python scripts/build_submission.py`.

