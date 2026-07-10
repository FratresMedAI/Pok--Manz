"""Dedicated pilot logic for Alakazam counter decks."""

from __future__ import annotations

from typing import Any

from .anti_psychic_control import anti_control_bonus, select_anti_control_strategy
from .cards import CardFeature, count_cards
from .control_policy import ABRA, ALAKAZAM, DUDUNSPARCE, DUNSPARCE, KADABRA, selected_card
from .evaluator import card_id_for_option, choose_indices, context_name, option_type_name, safe_getattr, visible_opponent_energy_ids


DREEPY = 119
DRAKLOAK = 120
DRAGAPULT = 121
CORNERSTONE = 117
TEAL_OGERPON = 96
IRON_THORNS = 37
FEZANDIPITI = 140
POFFIN = 1086
RARE_CANDY = 1079
ULTRA_BALL = 1121
PRIME_CATCHER = 1088
BOSS = 1182
CRISPIN = 1198
ALAKAZAM_ENGINE = {ABRA, KADABRA, ALAKAZAM, DUNSPARCE, DUDUNSPARCE}


def is_dragapult_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(DRAGAPULT, 0) >= 2 and counts.get(DREEPY, 0) >= 3


def is_ogerpon_wall_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(CORNERSTONE, 0) >= 2 and counts.get(TEAL_OGERPON, 0) >= 2


def is_iron_thorns_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(IRON_THORNS, 0) >= 2


def board_counts(obs: Any, player_index: int) -> dict[int, int]:
    state = safe_getattr(obs, "current")
    players = safe_getattr(state, "players", []) if state is not None else []
    if player_index >= len(players):
        return {}
    player = players[player_index]
    counts: dict[int, int] = {}
    for pokemon in list(safe_getattr(player, "active", []) or []) + list(safe_getattr(player, "bench", []) or []):
        card_id = safe_getattr(pokemon, "id")
        if card_id is not None:
            counts[card_id] = counts.get(card_id, 0) + 1
    return counts


def dragapult_score_option(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    counts = board_counts(obs, your_index)
    score = 0.0

    if option_name == "PLAY":
        if card_id == POFFIN and counts.get(DREEPY, 0) < 3:
            score += 4200.0
        elif card_id in {ULTRA_BALL, RARE_CANDY, CRISPIN}:
            score += 2600.0
        elif card_id in {BOSS, PRIME_CATCHER}:
            score += 2200.0

    if option_name == "EVOLVE":
        if card_id == DRAGAPULT or safe_getattr(selected_card(obs, option), "id") in {DREEPY, DRAKLOAK}:
            score += 5000.0
        elif card_id == DRAKLOAK:
            score += 3200.0

    if option_name == "ATTACH":
        target_id = safe_getattr(selected_card(obs, option), "id")
        if target_id in {DRAGAPULT, DRAKLOAK, DREEPY}:
            score += 2800.0

    if option_name == "ATTACK":
        score += 3600.0
        if select_anti_control_strategy(obs, registry) == "EXECUTE_BENCH_SNIPE_PRIORITY":
            score += 1800.0

    if option_name == "PLAY":
        if card_id in {1087, 1197}:  # Hand Trimmer / Xerosic
            score += 2800.0
        if card_id == 11:
            score += 2200.0

    if option_name == "ATTACH" and card_id == 11:
        score += 3000.0

    if option_name == "CARD":
        selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"} and selected_id == DREEPY:
            score += 2400.0
        elif ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET", "SWITCH", "TO_ACTIVE"}:
            if selected_id in ALAKAZAM_ENGINE:
                score += 3600.0
            elif selected_id == FEZANDIPITI:
                score += 900.0

    return score


def ogerpon_score_option(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    counts = board_counts(obs, your_index)
    score = 0.0

    if option_name == "ABILITY" and safe_getattr(selected_card(obs, option), "id") == TEAL_OGERPON:
        score += 2800.0

    if option_name == "PLAY":
        if card_id in {ULTRA_BALL, CRISPIN}:
            score += 2200.0
        elif card_id == BOSS:
            score += 1800.0

    if option_name == "ATTACH":
        target_id = safe_getattr(selected_card(obs, option), "id")
        if target_id in {CORNERSTONE, TEAL_OGERPON}:
            score += 3600.0

    if option_name == "ATTACK":
        score += 3400.0

    if option_name == "PLAY" and card_id == 1081 and visible_opponent_energy_ids(obs) & {11, 13, 14, 18, 19}:
        score += 3600.0

    if option_name == "CARD":
        selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and selected_id == CORNERSTONE:
            score += 4200.0
        elif ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"}:
            if selected_id == TEAL_OGERPON and counts.get(TEAL_OGERPON, 0) < 2:
                score += 1800.0
            elif selected_id not in {TEAL_OGERPON, CORNERSTONE}:
                score -= 1200.0
        elif ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET"} and selected_id in ALAKAZAM_ENGINE:
            score += 2200.0

    return score


def iron_thorns_score_option(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    counts = board_counts(obs, your_index)
    score = 0.0

    if option_name == "PLAY":
        if card_id in {ULTRA_BALL, RARE_CANDY, CRISPIN}:
            score += 2600.0
        elif card_id in {BOSS, PRIME_CATCHER}:
            score += 2000.0

    if option_name == "ATTACH":
        target_id = safe_getattr(selected_card(obs, option), "id")
        if target_id == IRON_THORNS:
            score += 4200.0

    if option_name == "ATTACK":
        score += 3800.0

    if option_name == "CARD":
        selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and selected_id == IRON_THORNS:
            score += 4500.0
        elif ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"} and selected_id != IRON_THORNS:
            score -= 1500.0
        elif ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET"} and selected_id in ALAKAZAM_ENGINE:
            score += 2800.0

    if counts.get(IRON_THORNS, 0) == 0 and option_name in {"PLAY", "CARD", "EVOLVE"}:
        score += 600.0

    return score


def choose_counter_indices(
    obs: Any,
    deck: list[int],
    registry: dict[int, CardFeature],
    imitation_profile: dict[str, Any] | None = None,
) -> list[int]:
    if is_dragapult_deck(deck):
        scorer = dragapult_score_option
    elif is_ogerpon_wall_deck(deck):
        scorer = ogerpon_score_option
    elif is_iron_thorns_deck(deck):
        scorer = iron_thorns_score_option
    else:
        return choose_indices(obs, registry, imitation_profile)

    select = safe_getattr(obs, "select")
    options = list(safe_getattr(select, "option", []) or [])
    if not options:
        return []
    ranked = sorted(
        range(len(options)),
        key=lambda index: scorer(obs, options[index], registry) + anti_control_bonus(obs, options[index], registry),
        reverse=True,
    )
    if ranked and scorer(obs, options[ranked[0]], registry) + anti_control_bonus(obs, options[ranked[0]], registry) > 1000:
        min_count = int(safe_getattr(select, "minCount", 0) or 0)
        max_count = int(safe_getattr(select, "maxCount", 0) or 0)
        count = max(min_count, max_count)
        return ranked[: min(count, len(ranked))]
    return choose_indices(obs, registry, imitation_profile)
