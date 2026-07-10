"""Probability utilities for Pokemon TCG action evaluation.

These helpers are intentionally dependency-free so the same logic can be copied
into a Kaggle submission bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb


@dataclass(frozen=True)
class OutsResult:
    remaining_outs: int
    deck_size: int
    single_draw_probability: float
    multi_draw_probability: float


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, value))


def at_least_one_success_probability(deck_size: int, outs: int, draws: int) -> float:
    """Return P(at least one out) with hypergeometric sampling."""
    if deck_size <= 0 or outs <= 0 or draws <= 0:
        return 0.0
    draws = min(draws, deck_size)
    outs = min(outs, deck_size)
    failures = deck_size - outs
    if draws > failures:
        return 1.0
    miss = comb(failures, draws) / comb(deck_size, draws)
    return clamp_probability(1.0 - miss)


def remaining_outs(
    total_copies: int,
    *,
    in_hand: int = 0,
    in_discard: int = 0,
    in_play: int = 0,
    known_prized: int = 0,
) -> int:
    """Count copies still available in deck."""
    unavailable = in_hand + in_discard + in_play + known_prized
    return max(0, total_copies - unavailable)


def evaluate_outs(
    total_copies: int,
    deck_size: int,
    draws: int,
    *,
    in_hand: int = 0,
    in_discard: int = 0,
    in_play: int = 0,
    known_prized: int = 0,
) -> OutsResult:
    outs = remaining_outs(
        total_copies,
        in_hand=in_hand,
        in_discard=in_discard,
        in_play=in_play,
        known_prized=known_prized,
    )
    single = 0.0 if deck_size <= 0 else outs / deck_size
    multi = at_least_one_success_probability(deck_size, outs, draws)
    return OutsResult(outs, deck_size, clamp_probability(single), multi)


def turns_to_deckout(deck_size: int, average_cards_drawn_per_turn: float) -> float:
    if deck_size <= 0:
        return 0.0
    if average_cards_drawn_per_turn <= 0:
        return float("inf")
    return deck_size / average_cards_drawn_per_turn


def deckout_penalty(deck_size: int, average_cards_drawn_per_turn: float) -> float:
    """Penalty that rises sharply below three estimated turns to deckout."""
    turns = turns_to_deckout(deck_size, average_cards_drawn_per_turn)
    if turns == float("inf"):
        return 0.0
    if turns <= 1:
        return 5000.0
    if turns <= 2:
        return 2500.0
    if turns <= 3:
        return 900.0
    return 0.0


def prize_value(is_ex: bool = False, is_mega_ex: bool = False) -> int:
    if is_mega_ex:
        return 3
    if is_ex:
        return 2
    return 1


def net_material_gain(prizes_gained: int, prizes_risked: int) -> int:
    return prizes_gained - prizes_risked

