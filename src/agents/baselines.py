"""Baseline CABT agents."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .cards import lucario_deck
from .evaluator import choose_indices


def read_deck_csv(path: str | Path = "deck.csv") -> list[int]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [int(line.strip()) for line in handle if line.strip()][:60]


def first_legal_agent(obs_dict: dict[str, Any]) -> list[int]:
    select = obs_dict.get("select")
    if select is None:
        return lucario_deck()
    max_count = int(select.get("maxCount") or 0)
    return list(range(min(max_count, len(select.get("option", [])))))


def random_agent(obs_dict: dict[str, Any]) -> list[int]:
    select = obs_dict.get("select")
    if select is None:
        return lucario_deck()
    options = list(range(len(select.get("option", []))))
    max_count = int(select.get("maxCount") or 0)
    return random.sample(options, min(max_count, len(options)))


def heuristic_agent(obs_dict: dict[str, Any], registry: dict[int, Any], to_observation_class: Any) -> list[int]:
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return lucario_deck()
    return choose_indices(obs, registry)

