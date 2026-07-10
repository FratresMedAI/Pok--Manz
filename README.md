# PokeMayne

Pokemon TCG AI Battle Challenge agent scaffold for Kaggle CABT.

## What Is Built

- Official Kaggle SDK assets extracted under `vendor/cabt_sample_submission`.
- Lucario-based `submission/main.py` and `submission/deck.csv`.
- Heuristic evaluator under `src/agents`.
- Offline card metadata tooling under `src/data`.
- Local match/evaluation scripts under `src`.
- Packaging script at `scripts/build_submission.py`.

## Quick Commands

```powershell
python src\data\merge_card_metadata.py
python src\evaluate.py --games 5
python scripts\build_submission.py
```

The built archive is written to `artifacts/submission.tar.gz`.

## Notes

Kaggle evaluation has no network access. Use TCGdex and PokemonTCG.io only before packaging, then ship compact local metadata if needed.

