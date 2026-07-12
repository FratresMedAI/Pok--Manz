"""Strategy matrix for dismantling Alakazam/Dudunsparce Psychic control."""

from __future__ import annotations

from typing import Any

from .archetypes import classify_from_card_ids
from .cards import CardFeature
from .option_utils import area_name_for, context_name_for, option_type_name_for


ABRA = 741
KADABRA = 742
ALAKAZAM = 743
DUNSPARCE = 305
DUDUNSPARCE = 66
MIST_ENERGY = 11
HAND_TRIMMER = 1087
XEROSIC = 1197
ENHANCED_HAMMER = 1081
ARTICUNO = 414
CORNERSTONE = 117
IRON_THORNS = 37
DRAGAPULT = 121
STAGING_BASICS = {ABRA, DUNSPARCE}
ENGINE_BASICS = {ABRA, KADABRA, ALAKAZAM, DUNSPARCE, DUDUNSPARCE}
DUNSPARCE_LINE = {DUNSPARCE, DUDUNSPARCE}
DRAW_ENGINE_LINE = DUNSPARCE_LINE
SPECIAL_ENERGY_IDS = {11, 13, 14, 18, 19}


def safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


def option_type_name(option: Any) -> str:
    return option_type_name_for(safe_getattr(option, "type", ""))


def context_name(obs: Any) -> str:
    select = safe_getattr(obs, "select")
    return context_name_for(safe_getattr(select, "context", ""))


def card_id_for_option(obs: Any, option: Any) -> int | None:
    if safe_getattr(option, "cardId") is not None:
        return option.cardId
    option_name = option_type_name(option)
    area_name = area_name_for(safe_getattr(option, "area", ""))
    index = safe_getattr(option, "index")
    player_index = safe_getattr(option, "playerIndex")
    state = safe_getattr(obs, "current")
    if area_name == "None" and option_name in {"PLAY", "ATTACH"}:
        area_name = "HAND"
    if state is None or index is None:
        return None
    if player_index is None:
        player_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if player_index >= len(players):
        return None
    player = players[player_index]
    zone = None
    if area_name == "HAND":
        zone = safe_getattr(player, "hand")
    elif area_name == "ACTIVE":
        zone = safe_getattr(player, "active")
    elif area_name == "BENCH":
        zone = safe_getattr(player, "bench")
    if not zone or index >= len(zone) or zone[index] is None:
        return None
    return safe_getattr(zone[index], "id")


def visible_opponent_ids(obs: Any) -> list[int]:
    state = safe_getattr(obs, "current")
    if state is None:
        return []
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    opponent_index = 1 - your_index
    if opponent_index >= len(players):
        return []
    opponent = players[opponent_index]
    ids: list[int] = []
    for pokemon in list(safe_getattr(opponent, "active", []) or []) + list(safe_getattr(opponent, "bench", []) or []):
        if pokemon is not None and safe_getattr(pokemon, "id") is not None:
            ids.append(pokemon.id)
    return ids


def visible_opponent_energy_ids(obs: Any) -> set[int]:
    state = safe_getattr(obs, "current")
    if state is None:
        return set()
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    opponent_index = 1 - your_index
    if opponent_index >= len(players):
        return set()
    opponent = players[opponent_index]
    energy_ids: set[int] = set()
    for pokemon in list(safe_getattr(opponent, "active", []) or []) + list(safe_getattr(opponent, "bench", []) or []):
        for energy in safe_getattr(pokemon, "energyCards", []) or []:
            card_id = safe_getattr(energy, "id")
            if card_id is not None:
                energy_ids.add(card_id)
    return energy_ids


def is_psychic_control_match(obs: Any, registry: dict[int, CardFeature]) -> bool:
    read = classify_from_card_ids(visible_opponent_ids(obs), registry)
    return read.name == "alakazam_control" and read.confidence >= 0.2


def opponent_hand_size(obs: Any) -> int:
    state = safe_getattr(obs, "current")
    if state is None:
        return 0
    opponent_index = 1 - safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if opponent_index >= len(players):
        return 0
    return int(safe_getattr(players[opponent_index], "handCount", 0) or 0)


def my_bench_count(obs: Any) -> int:
    state = safe_getattr(obs, "current")
    if state is None:
        return 0
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return 0
    bench = safe_getattr(players[your_index], "bench", []) or []
    return sum(1 for pokemon in bench if pokemon is not None)


def my_board_card_ids(obs: Any) -> set[int]:
    state = safe_getattr(obs, "current")
    if state is None:
        return set()
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return set()
    player = players[your_index]
    ids: set[int] = set()
    for pokemon in list(safe_getattr(player, "active", []) or []) + list(safe_getattr(player, "bench", []) or []):
        card_id = safe_getattr(pokemon, "id")
        if card_id is not None:
            ids.add(card_id)
    return ids


def opponent_has_basic_bench(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    opponent_index = 1 - safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if opponent_index >= len(players):
        return False
    for pokemon in safe_getattr(players[opponent_index], "bench", []) or []:
        if pokemon is None:
            continue
        if safe_getattr(pokemon, "id") in STAGING_BASICS:
            return True
    return False


def match_phase(obs: Any) -> str:
    state = safe_getattr(obs, "current")
    if state is None:
        return "opening"
    turn = int(safe_getattr(state, "turn", 0) or 0)
    if turn <= 4:
        return "opening"
    return "midgame"


def opponent_has_dunsparce_on_board(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    opponent_index = 1 - safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if opponent_index >= len(players):
        return False
    opponent = players[opponent_index]
    for pokemon in list(safe_getattr(opponent, "active", []) or []) + list(safe_getattr(opponent, "bench", []) or []):
        if pokemon is not None and safe_getattr(pokemon, "id") in DUNSPARCE_LINE:
            return True
    return False


def opponent_has_dunsparce_on_bench(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    opponent_index = 1 - safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if opponent_index >= len(players):
        return False
    for pokemon in safe_getattr(players[opponent_index], "bench", []) or []:
        if pokemon is not None and safe_getattr(pokemon, "id") in DUNSPARCE_LINE:
            return True
    return False


def can_snipe_bench(obs: Any) -> bool:
    return DRAGAPULT in my_board_card_ids(obs) or opponent_has_dunsparce_on_bench(obs) or opponent_has_basic_bench(obs)


def hand_has_disruption(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return False
    hand_ids = {
        safe_getattr(card, "id")
        for card in safe_getattr(players[your_index], "hand", []) or []
        if card is not None
    }
    return bool(hand_ids & {HAND_TRIMMER, XEROSIC})


def mist_energy_available(obs: Any) -> bool:
    if MIST_ENERGY in my_board_card_ids(obs):
        return False
    select = safe_getattr(obs, "select")
    exposed_deck = safe_getattr(select, "deck", None) if select is not None else None
    if exposed_deck and any(safe_getattr(card, "id") == MIST_ENERGY for card in exposed_deck):
        return True
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return False
    hand_ids = {
        safe_getattr(card, "id")
        for card in safe_getattr(players[your_index], "hand", []) or []
        if card is not None
    }
    return MIST_ENERGY in hand_ids


def check_anti_alakazam_overrides(obs: Any, registry: dict[int, CardFeature]) -> str:
    """Primary pivot layer: stop fighting Alakazam on its own terms."""
    if not is_psychic_control_match(obs, registry):
        return "CONTINUE_STANDARD_GAMEPLAY_FLOW"

    if mist_energy_available(obs):
        return "FORCE_SEARCH_AND_ATTACH_MIST_ENERGY_TO_ACTIVE"

    if can_snipe_bench(obs) and opponent_has_dunsparce_on_bench(obs):
        return "EXECUTE_BENCH_SNIPE_ON_DUNSPARCE"

    if hand_has_disruption(obs) and not opponent_has_dunsparce_on_board(obs):
        return "PLAY_HAND_DISRUPTION_RESOURCE_WIPE"

    if IRON_THORNS in my_board_card_ids(obs):
        return "ABILITY_LOCK_ZERO_BENCH"

    if my_bench_count(obs) >= 2:
        return "ATTACK_WITH_MINIMUM_BENCH"

    return "CONTINUE_STANDARD_GAMEPLAY_FLOW"


def select_optimal_anti_psychic_tool(obs: Any, registry: dict[int, CardFeature]) -> str:
    """High-priority tech selection for the Alakazam Powerful Hand line."""
    override = check_anti_alakazam_overrides(obs, registry)
    if override != "CONTINUE_STANDARD_GAMEPLAY_FLOW":
        return override

    if not is_psychic_control_match(obs, registry):
        return "CONTINUE_STANDARD_GAMEPLAN"

    board = my_board_card_ids(obs)
    if MIST_ENERGY in board:
        return "CONTINUE_STANDARD_GAMEPLAN"

    select = safe_getattr(obs, "select")
    exposed_deck = safe_getattr(select, "deck", None) if select is not None else None
    if exposed_deck and any(safe_getattr(card, "id") == MIST_ENERGY for card in exposed_deck):
        return "SEARCH_AND_ATTACH_MIST_ENERGY_TO_ACTIVE"

    state = safe_getattr(obs, "current")
    if state is not None:
        your_index = safe_getattr(state, "yourIndex", 0)
        players = safe_getattr(state, "players", [])
        if your_index < len(players):
            hand_ids = {
                safe_getattr(card, "id")
                for card in safe_getattr(players[your_index], "hand", []) or []
                if card is not None
            }
            if MIST_ENERGY in hand_ids:
                return "SEARCH_AND_ATTACH_MIST_ENERGY_TO_ACTIVE"

    if opponent_hand_size(obs) >= 12 and not opponent_has_dunsparce_on_board(obs):
        return "PLAY_HAND_TRIMMER_IMMEDIATELY"

    if ARTICUNO in board:
        return "PROMOTE_ARTICUNO_AND_CEASE_BENCHING"

    return select_anti_control_strategy(obs, registry)


def select_anti_control_strategy(obs: Any, registry: dict[int, CardFeature]) -> str:
    if not is_psychic_control_match(obs, registry):
        return "DEFAULT_METRIC"

    board = my_board_card_ids(obs)
    if DRAGAPULT in board and opponent_has_basic_bench(obs):
        if opponent_has_dunsparce_on_bench(obs):
            return "EXECUTE_BENCH_SNIPE_ON_DUNSPARCE"
        return "EXECUTE_BENCH_SNIPE_PRIORITY"
    if CORNERSTONE in board:
        return "MOVE_CORNERSTONE_TO_ACTIVE"
    if IRON_THORNS in board:
        return "ABILITY_LOCK_FREEZE"
    if ARTICUNO in board:
        return "PROMOTE_ARTICUNO_AND_CEASE_BENCHING"
    if opponent_hand_size(obs) >= 12:
        return "PLAY_HAND_TRIMMER"
    if visible_opponent_energy_ids(obs) & SPECIAL_ENERGY_IDS:
        return "PLAY_ENHANCED_HAMMER"
    if my_bench_count(obs) >= 2:
        return "ATTACK_WITH_MINIMUM_BENCH"
    return "DEFAULT_ANTI_CONTROL"


def anti_control_bonus(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    if not is_psychic_control_match(obs, registry):
        return 0.0

    strategy = select_optimal_anti_psychic_tool(obs, registry)
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    bonus = 0.0

    if strategy == "FORCE_SEARCH_AND_ATTACH_MIST_ENERGY_TO_ACTIVE":
        if card_id == MIST_ENERGY and option_name in {"ATTACH", "CARD"}:
            bonus += 6200.0
        if option_name == "PLAY" and card_id in {1121, 1086, 1152}:
            bonus += 3400.0
        if match_phase(obs) == "opening":
            bonus += 1200.0

    elif strategy == "EXECUTE_BENCH_SNIPE_ON_DUNSPARCE":
        if option_name == "ATTACK":
            bonus += 2800.0
        if ctx in {"DAMAGE_COUNTER", "DAMAGE_COUNTER_ANY", "DAMAGE", "EFFECT_TARGET"}:
            if card_id in DUNSPARCE_LINE:
                bonus += 5500.0
            elif card_id == ABRA:
                bonus += 200.0
            elif card_id in ENGINE_BASICS:
                bonus += 1200.0

    elif strategy == "PLAY_HAND_DISRUPTION_RESOURCE_WIPE":
        if option_name == "PLAY" and card_id in {HAND_TRIMMER, XEROSIC}:
            bonus += 5000.0
        if option_name == "PLAY" and card_id in {HAND_TRIMMER, XEROSIC} and opponent_has_dunsparce_on_board(obs):
            bonus -= 4500.0

    elif strategy == "ABILITY_LOCK_ZERO_BENCH":
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and card_id == IRON_THORNS:
            bonus += 5500.0
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"}:
            bonus -= 3500.0
        if option_name == "ATTACK":
            bonus += 2400.0

    elif strategy == "SEARCH_AND_ATTACH_MIST_ENERGY_TO_ACTIVE":
        if card_id == MIST_ENERGY and option_name in {"ATTACH", "CARD"}:
            bonus += 5200.0
        if option_name == "PLAY" and card_id in {1121, 1086}:  # Ultra Ball / Poffin deck search
            bonus += 2600.0

    elif strategy == "PLAY_HAND_TRIMMER_IMMEDIATELY":
        if option_name == "PLAY" and card_id in {HAND_TRIMMER, XEROSIC}:
            bonus += 4000.0

    elif strategy == "EXECUTE_BENCH_SNIPE_PRIORITY":
        if option_name == "ATTACK":
            bonus += 2200.0
        if ctx in {"DAMAGE_COUNTER", "DAMAGE_COUNTER_ANY", "DAMAGE", "EFFECT_TARGET"}:
            if card_id in DUNSPARCE_LINE:
                bonus += 5000.0
            elif card_id in STAGING_BASICS:
                bonus += 3200.0
            elif card_id in ENGINE_BASICS:
                bonus += 1800.0

    elif strategy == "MOVE_CORNERSTONE_TO_ACTIVE":
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and card_id == CORNERSTONE:
            bonus += 4500.0
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"}:
            bonus -= 1800.0
        if option_name == "ATTACK":
            bonus += 1600.0

    elif strategy == "ABILITY_LOCK_FREEZE":
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and card_id == IRON_THORNS:
            bonus += 5000.0
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"}:
            bonus -= 3500.0
        if option_name == "ATTACK":
            bonus += 2000.0

    elif strategy == "PROMOTE_ARTICUNO_AND_CEASE_BENCHING":
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and card_id == ARTICUNO:
            bonus += 4800.0
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"}:
            bonus -= 3000.0

    elif strategy == "PLAY_HAND_TRIMMER":
        if option_name == "PLAY" and card_id in {HAND_TRIMMER, XEROSIC}:
            bonus += 3600.0 if opponent_hand_size(obs) >= 12 else 1200.0

    elif strategy == "PLAY_ENHANCED_HAMMER":
        if option_name == "PLAY" and card_id == ENHANCED_HAMMER:
            bonus += 4200.0

    elif strategy == "ATTACK_WITH_MINIMUM_BENCH":
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"}:
            bonus -= 2000.0 if my_bench_count(obs) >= 2 else -800.0
        if option_name == "ATTACK":
            bonus += 1600.0

    if card_id == MIST_ENERGY and option_name == "ATTACH":
        bonus += 4200.0
    if option_name == "PLAY" and card_id == HAND_TRIMMER and opponent_hand_size(obs) >= 12:
        if not opponent_has_dunsparce_on_board(obs):
            bonus += 3600.0
        else:
            bonus -= 2000.0
    if option_name == "PLAY" and card_id == XEROSIC:
        if not opponent_has_dunsparce_on_board(obs):
            bonus += 3200.0
        else:
            bonus -= 2500.0
    if my_bench_count(obs) >= 2 and ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"}:
        bonus -= 1500.0
    if my_bench_count(obs) >= 1 and IRON_THORNS in my_board_card_ids(obs) and ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"}:
        bonus -= 2800.0

    if match_phase(obs) == "midgame" and option_name == "ATTACK":
        bonus += 400.0

    return bonus
