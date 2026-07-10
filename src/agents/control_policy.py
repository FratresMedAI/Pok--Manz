"""Dedicated policy for the mined Alakazam/Dunsparce control deck."""

from __future__ import annotations

from typing import Any

from .cards import CardFeature, alakazam_control_deck, count_cards
from .evaluator import (
    card_id_for_option,
    choose_indices,
    context_name,
    option_type_name,
    safe_getattr,
    visible_opponent_ids,
)


ABRA = 741
KADABRA = 742
ALAKAZAM = 743
DUNSPARCE = 305
DUDUNSPARCE = 66
FEZANDIPITI_EX = 140
MEGA_KANGASKHAN_EX = 756
DWEBBLE = 344
CRUSTLE = 345
ENRICHING_ENERGY = 13
TELEPATH_PSYCHIC_ENERGY = 19
ENHANCED_HAMMER = 1081
BUDDY_BUDDY_POFFIN = 1086
RARE_CANDY = 1079
POKE_PAD = 1152
BOSS_ORDERS = 1182
HILDA = 1225
DAWN = 1231
XEROSIC = 1197
NIGHTTIME_MINE = 1266
POWERFUL_HAND = 1072
RAPID_FIRE_COMBO = 1092

ALAKAZAM_DECK_COUNTS = count_cards(alakazam_control_deck())
ALAKAZAM_ENGINE = {ABRA, KADABRA, ALAKAZAM, DUNSPARCE, DUDUNSPARCE}
SETUP_BASICS = {ABRA, DUNSPARCE}
SPECIAL_ENERGIES = {ENRICHING_ENERGY, TELEPATH_PSYCHIC_ENERGY, 11, 14, 18}


def is_alakazam_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(ALAKAZAM, 0) >= 3 and counts.get(ABRA, 0) >= 3 and counts.get(DUNSPARCE, 0) >= 2


def zone_card(obs: Any, player_index: int, area_name: str, index: int | None) -> Any | None:
    if index is None:
        return None
    state = safe_getattr(obs, "current")
    players = safe_getattr(state, "players", []) if state is not None else []
    if player_index < 0 or player_index >= len(players):
        return None
    player = players[player_index]
    zone = None
    if area_name == "ACTIVE":
        zone = safe_getattr(player, "active")
    elif area_name == "BENCH":
        zone = safe_getattr(player, "bench")
    elif area_name == "HAND":
        zone = safe_getattr(player, "hand")
    elif area_name == "DISCARD":
        zone = safe_getattr(player, "discard")
    if not zone or index >= len(zone):
        return None
    return zone[index]


def option_inplay_pokemon(obs: Any, option: Any) -> Any | None:
    area = safe_getattr(safe_getattr(option, "inPlayArea"), "name", "")
    index = safe_getattr(option, "inPlayIndex")
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    return zone_card(obs, your_index, area, index)


def selected_card(obs: Any, option: Any) -> Any | None:
    area = safe_getattr(safe_getattr(option, "area"), "name", "")
    index = safe_getattr(option, "index")
    player_index = safe_getattr(option, "playerIndex")
    if player_index is None:
        state = safe_getattr(obs, "current")
        player_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    return zone_card(obs, player_index, area, index)


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


def opponent_has_special_energy(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    opponent_index = 1 - safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if opponent_index >= len(players):
        return False
    opponent = players[opponent_index]
    for pokemon in list(safe_getattr(opponent, "active", []) or []) + list(safe_getattr(opponent, "bench", []) or []):
        for card in safe_getattr(pokemon, "energyCards", []) or []:
            if safe_getattr(card, "id") in SPECIAL_ENERGIES:
                return True
    return False


def hand_count(obs: Any) -> int:
    state = safe_getattr(obs, "current")
    if state is None:
        return 0
    player = state.players[state.yourIndex]
    return int(safe_getattr(player, "handCount", 0) or 0)


def alakazam_score_option(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    """Return an additive control-deck score."""
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    card = registry.get(card_id) if card_id is not None else None
    card_name = card.name if card else ""
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    counts = board_counts(obs, your_index)
    opponent_ids = visible_opponent_ids(obs)
    opponent_has_kangaskhan = MEGA_KANGASKHAN_EX in opponent_ids

    score = 0.0

    if option_name == "ABILITY":
        source = selected_card(obs, option)
        source_id = safe_getattr(source, "id")
        if source_id == DUDUNSPARCE:
            score += 5000.0  # Run Away Draw is the deck engine and prize denial loop.
        elif source_id in {KADABRA, ALAKAZAM}:
            score += 1800.0
        elif source_id == FEZANDIPITI_EX:
            score += 1100.0

    if option_name == "EVOLVE":
        target = option_inplay_pokemon(obs, option)
        target_id = safe_getattr(target, "id")
        if card_id == ALAKAZAM or target_id in {ABRA, KADABRA}:
            score += 4200.0
        elif card_id == DUDUNSPARCE or target_id == DUNSPARCE:
            score += 3200.0
        elif card_id == KADABRA:
            score += 2600.0

    if option_name == "ATTACH":
        target = option_inplay_pokemon(obs, option)
        target_id = safe_getattr(target, "id")
        if card_id in {ENRICHING_ENERGY, TELEPATH_PSYCHIC_ENERGY, 5}:
            if target_id in {ALAKAZAM, KADABRA, ABRA}:
                score += 3600.0
            elif target_id in {DUNSPARCE, DUDUNSPARCE}:
                score -= 1200.0

    if option_name == "PLAY":
        if card_id == BUDDY_BUDDY_POFFIN:
            # Only play Poffin while it still finds engine basics.
            score += 4500.0 if counts.get(ABRA, 0) < 2 or counts.get(DUNSPARCE, 0) < 1 else 700.0
        elif card_id == RARE_CANDY:
            score += 3000.0 if counts.get(ABRA, 0) > 0 else -800.0
        elif card_id == ENHANCED_HAMMER:
            score += 4200.0 if opponent_has_special_energy(obs) else -500.0
        elif card_id == BOSS_ORDERS:
            score += 3500.0 if opponent_has_kangaskhan else 1600.0
        elif card_id in {HILDA, DAWN, POKE_PAD}:
            score += 1700.0
        elif card_id == XEROSIC:
            score += 1600.0
        elif card_id == NIGHTTIME_MINE:
            score += 900.0

    if option_name == "ATTACK":
        attack_id = safe_getattr(option, "attackId")
        if attack_id == POWERFUL_HAND:
            score += 2600.0 + 150.0 * hand_count(obs)
        elif attack_id == 1070:  # Abra Teleportation Attack
            score += 900.0
        else:
            score += 500.0

    if option_name == "CARD":
        selected = selected_card(obs, option)
        selected_id = safe_getattr(selected, "id") or card_id
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"}:
            if selected_id in {DUNSPARCE, DUDUNSPARCE, ABRA}:
                score += 2200.0
            if selected_id == ALAKAZAM:
                score -= 1200.0
        elif ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"}:
            if selected_id == ABRA and counts.get(ABRA, 0) < 3:
                score += 2500.0
            elif selected_id == DUNSPARCE and counts.get(DUNSPARCE, 0) < 2:
                score += 2200.0
            elif selected_id in {FEZANDIPITI_EX, 343}:
                score += 500.0
            elif selected_id not in SETUP_BASICS:
                score -= 600.0
        elif ctx in {"TO_HAND", "LOOK"}:
            if selected_id in {ALAKAZAM, RARE_CANDY} and counts.get(ABRA, 0) > 0:
                score += 3600.0
            elif selected_id == DUDUNSPARCE and counts.get(DUNSPARCE, 0) > 0:
                score += 3000.0
            elif selected_id in {ABRA, DUNSPARCE}:
                score += 2200.0
            elif selected_id in {ENHANCED_HAMMER, BOSS_ORDERS}:
                score += 1800.0
            elif selected_id in {HILDA, DAWN, POKE_PAD}:
                score += 1400.0
        elif ctx in {"DISCARD", "TO_DECK_BOTTOM"}:
            if selected_id in ALAKAZAM_ENGINE or selected_id in {ENRICHING_ENERGY, TELEPATH_PSYCHIC_ENERGY, RARE_CANDY}:
                score -= 3000.0
            elif selected_id in {BOSS_ORDERS, HILDA, DAWN, POKE_PAD}:
                score -= 900.0
            elif selected_id == ENHANCED_HAMMER:
                score += 1800.0 if not opponent_has_special_energy(obs) else -600.0
            else:
                score += 600.0
        elif ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET"}:
            # Counter-control and Kangaskhan: do not tunnel into the 300 HP active.
            if selected_id in {ABRA, DUNSPARCE, KADABRA, DUDUNSPARCE, DWEBBLE, 343, FEZANDIPITI_EX}:
                score += 3200.0
            elif selected_id == MEGA_KANGASKHAN_EX:
                score -= 1000.0

    return score


def choose_control_indices(
    obs: Any,
    registry: dict[int, CardFeature],
    imitation_profile: dict[str, Any] | None = None,
) -> list[int]:
    select = safe_getattr(obs, "select")
    options = list(safe_getattr(select, "option", []) or [])
    if not options:
        return []
    base = choose_indices(obs, registry, imitation_profile)
    ranked = sorted(
        range(len(options)),
        key=lambda index: alakazam_score_option(obs, options[index], registry),
        reverse=True,
    )
    # If the control layer has a strong opinion, trust it. Otherwise fall back.
    if ranked and alakazam_score_option(obs, options[ranked[0]], registry) > 1000:
        min_count = int(safe_getattr(select, "minCount", 0) or 0)
        max_count = int(safe_getattr(select, "maxCount", 0) or 0)
        count = max(min_count, max_count)
        return ranked[: min(count, len(ranked))]
    return base

