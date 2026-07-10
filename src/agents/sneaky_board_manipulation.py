"""Sneaky board-manipulation tactics vs Alakazam/Dudunsparce control."""

from __future__ import annotations

from typing import Any

from .anti_psychic_control import (
    ABRA,
    ALAKAZAM,
    CORNERSTONE,
    DUDUNSPARCE,
    DUNSPARCE,
    HAND_TRIMMER,
    MIST_ENERGY,
    XEROSIC,
    card_id_for_option,
    context_name,
    is_psychic_control_match,
    opponent_hand_size,
    option_type_name,
    safe_getattr,
    visible_opponent_energy_ids,
)
from .cards import CardFeature


PRIME_CATCHER = 1088
BOSS_ORDERS = 1182
POKEMON_CATCHER = 1124
BRUTE_BONNET = 986
MUNKIDORI = 112
MUNKIDORI_EX = 139
ERIKA_GLOOM = 910
SNORUNT = 103
FEZANDIPITI = 140
SHAYMIN = 343
SKWOVET = 391
SPIDOPS = 401

GUST_CARDS = {PRIME_CATCHER, BOSS_ORDERS, POKEMON_CATCHER}
POISON_ENGINE_IDS = {BRUTE_BONNET, MUNKIDORI, MUNKIDORI_EX, ERIKA_GLOOM}
DECK_CLUTTER_IDS = {HAND_TRIMMER, XEROSIC, SNORUNT}
UTILITY_NON_ATTACKERS = {FEZANDIPITI, DUNSPARCE, DUDUNSPARCE, ABRA, SHAYMIN, SKWOVET}
THINNING_BASICS = {ABRA, DUNSPARCE}


def opponent_player(obs: Any) -> Any | None:
    state = safe_getattr(obs, "current")
    if state is None:
        return None
    opponent_index = 1 - safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if opponent_index >= len(players):
        return None
    return players[opponent_index]


def pokemon_energy_count(pokemon: Any) -> int:
    return len(safe_getattr(pokemon, "energyCards", []) or [])


def opponent_bench_targets(obs: Any) -> list[tuple[int, int]]:
    opponent = opponent_player(obs)
    if opponent is None:
        return []
    targets: list[tuple[int, int]] = []
    for index, pokemon in enumerate(safe_getattr(opponent, "bench", []) or []):
        if pokemon is None:
            continue
        card_id = safe_getattr(pokemon, "id")
        if card_id is not None:
            targets.append((index, card_id))
    return targets


def opponent_has_benched_utility_non_attacker(obs: Any) -> bool:
    for _, card_id in opponent_bench_targets(obs):
        opponent = opponent_player(obs)
        if opponent is None:
            return False
        for index, pokemon in enumerate(safe_getattr(opponent, "bench", []) or []):
            if pokemon is None:
                continue
            if safe_getattr(pokemon, "id") == card_id and card_id in UTILITY_NON_ATTACKERS:
                if pokemon_energy_count(pokemon) == 0:
                    return True
    return False


def zero_energy_utility_on_bench(obs: Any) -> set[int]:
    opponent = opponent_player(obs)
    if opponent is None:
        return set()
    ids: set[int] = set()
    for pokemon in safe_getattr(opponent, "bench", []) or []:
        if pokemon is None:
            continue
        card_id = safe_getattr(pokemon, "id")
        if card_id in UTILITY_NON_ATTACKERS and pokemon_energy_count(pokemon) == 0:
            ids.add(card_id)
    return ids


def opponent_active_card_id(obs: Any) -> int | None:
    opponent = opponent_player(obs)
    if opponent is None:
        return None
    active = safe_getattr(opponent, "active", []) or []
    if not active or active[0] is None:
        return None
    return safe_getattr(active[0], "id")


def opponent_active_has_attack_immunity(obs: Any) -> bool:
    opponent = opponent_player(obs)
    if opponent is None:
        return False
    active = safe_getattr(opponent, "active", []) or []
    if not active or active[0] is None:
        return False
    pokemon = active[0]
    if safe_getattr(pokemon, "id") == CORNERSTONE:
        return True
    for energy in safe_getattr(pokemon, "energyCards", []) or []:
        if safe_getattr(energy, "id") == MIST_ENERGY:
            return True
    return False


def opponent_discarded_thinning_basics(obs: Any) -> int:
    opponent = opponent_player(obs)
    if opponent is None:
        return 0
    count = 0
    for card in safe_getattr(opponent, "discard", []) or []:
        card_id = safe_getattr(card, "id")
        if card_id in THINNING_BASICS:
            count += 1
    return count


def can_inflict_special_condition(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return False
    board_ids = set()
    for pokemon in list(safe_getattr(players[your_index], "active", []) or []) + list(
        safe_getattr(players[your_index], "bench", []) or []
    ):
        if pokemon is not None and safe_getattr(pokemon, "id") is not None:
            board_ids.add(pokemon.id)
    hand_ids = {
        safe_getattr(card, "id")
        for card in safe_getattr(players[your_index], "hand", []) or []
        if card is not None
    }
    return bool(board_ids & POISON_ENGINE_IDS) or bool(hand_ids & POISON_ENGINE_IDS)


def execute_sneaky_board_manipulation(obs: Any, registry: dict[int, CardFeature]) -> str:
    if not is_psychic_control_match(obs, registry):
        return "DEFAULT_MIDGAME_FLOW"

    if opponent_has_benched_utility_non_attacker(obs):
        state = safe_getattr(obs, "current")
        if state is not None:
            your_index = safe_getattr(state, "yourIndex", 0)
            hand_ids = {
                safe_getattr(card, "id")
                for card in safe_getattr(state.players[your_index], "hand", []) or []
                if card is not None
            }
            if hand_ids & GUST_CARDS:
                return "GUST_AND_TRAP_ZERO_ENERGY_TARGET"

    if opponent_active_has_attack_immunity(obs) and can_inflict_special_condition(obs):
        return "APPLY_POISON_BURN_DAMAGE"

    if opponent_discarded_thinning_basics(obs) >= 2 or opponent_hand_size(obs) >= 10:
        return "DECK_CLUTTER_INJECTION"

    return "DEFAULT_MIDGAME_FLOW"


def sneaky_bonus(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    if not is_psychic_control_match(obs, registry):
        return 0.0

    strategy = execute_sneaky_board_manipulation(obs, registry)
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    bonus = 0.0
    utility_targets = zero_energy_utility_on_bench(obs)

    if strategy == "GUST_AND_TRAP_ZERO_ENERGY_TARGET":
        if option_name == "PLAY" and card_id in GUST_CARDS:
            bonus += 4600.0
        if ctx in {"SWITCH", "TO_ACTIVE", "EFFECT_TARGET", "CARD"}:
            selected_id = card_id
            if selected_id in utility_targets or selected_id in UTILITY_NON_ATTACKERS:
                bonus += 5000.0

    elif strategy == "APPLY_POISON_BURN_DAMAGE":
        if option_name == "ATTACK":
            bonus += 2400.0
        if option_name in {"ABILITY", "ATTACK", "EVOLVE"} and card_id in POISON_ENGINE_IDS:
            bonus += 4400.0
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and card_id in POISON_ENGINE_IDS:
            bonus += 3600.0
        if option_name == "ATTACH" and card_id in {5, 6, 13}:
            bonus += 1800.0

    elif strategy == "DECK_CLUTTER_INJECTION":
        if option_name == "PLAY" and card_id in DECK_CLUTTER_IDS:
            bonus += 3400.0
        if option_name == "ATTACK" and card_id == SNORUNT:
            bonus += 3000.0
        if option_name == "PLAY" and card_id == HAND_TRIMMER and opponent_hand_size(obs) >= 8:
            bonus += 2800.0

    if utility_targets and option_name == "PLAY" and card_id in GUST_CARDS:
        bonus += 2200.0

    return bonus
