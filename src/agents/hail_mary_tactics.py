"""High-risk hail mary overrides for desperate Psychic-control endgames."""

from __future__ import annotations

from typing import Any

from .anti_psychic_control import (
    HAND_TRIMMER,
    XEROSIC,
    card_id_for_option,
    context_name,
    is_psychic_control_match,
    option_type_name,
    safe_getattr,
)
from .cards import CardFeature
from .simulator_exploits import (
    is_board_stabilized,
    my_active_card_id,
    my_hand_size,
    opponent_deck_count,
    prize_counts,
)


SURVIVAL_BRACE = 1155
HAND_SHUFFLE_IDS = {HAND_TRIMMER, XEROSIC}
BAIT_EX_IDS = {37, 121, 139, 140, 677, 678}  # Iron Thorns, Dragapult, Munkidori ex, Fezandipiti, Lucario line


def is_desperate_prize_deficit(obs: Any) -> bool:
    my_prizes, opp_prizes = prize_counts(obs)
    return my_prizes <= 2 and opp_prizes < my_prizes


def has_hand_shuffle_tool(obs: Any) -> bool:
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
    return bool(hand_ids & HAND_SHUFFLE_IDS)


def has_survival_brace_available(obs: Any) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return False
    for card in safe_getattr(players[your_index], "hand", []) or []:
        if safe_getattr(card, "id") == SURVIVAL_BRACE:
            return True
    return False


def has_bait_target_available(obs: Any, registry: dict[int, CardFeature]) -> bool:
    state = safe_getattr(obs, "current")
    if state is None:
        return False
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return False
    player = players[your_index]
    for pokemon in list(safe_getattr(player, "bench", []) or []) + list(safe_getattr(player, "active", []) or []):
        if pokemon is None:
            continue
        card_id = safe_getattr(pokemon, "id")
        if card_id in BAIT_EX_IDS:
            return True
        feature = registry.get(card_id or -1)
        if feature and "multi_prize" in feature.tags:
            return True
    return False


_remaining_clock: float = 999.0


def update_runtime_context(obs_dict: dict) -> None:
    global _remaining_clock
    _remaining_clock = float(obs_dict.get("remainingOverageTime", 999.0) or 999.0)


def evaluate_hail_mary_tactics(obs: Any, registry: dict[int, CardFeature]) -> str:
    return evaluate_hail_mary_tactics_with_clock(obs, registry, _remaining_clock)


def evaluate_hail_mary_tactics_with_clock(
    obs: Any, registry: dict[int, CardFeature], remaining_clock: float
) -> str:
    if not is_psychic_control_match(obs, registry):
        return "DEFAULT_ENSEMBLE_FLOW"

    my_prizes, opp_prizes = prize_counts(obs)

    if opponent_deck_count(obs) <= 3 and is_desperate_prize_deficit(obs) and has_hand_shuffle_tool(obs):
        return "EXECUTE_TERMINAL_DECKOUT_COMBINATION"

    if remaining_clock < 45.0 and is_board_stabilized(obs):
        return "TRIGGER_FAST_PASS_STALL_SPEED"

    if opp_prizes <= 2 and has_survival_brace_available(obs) and has_bait_target_available(obs, registry):
        return "ATTACH_BRACE_PROMOTE_BAIT_TO_ACTIVE"

    if my_prizes == 1 and opp_prizes >= 3 and opponent_deck_count(obs) <= 5 and has_hand_shuffle_tool(obs):
        return "EXECUTE_TERMINAL_DECKOUT_COMBINATION"

    return "DEFAULT_ENSEMBLE_FLOW"


def hail_mary_bonus(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    return hail_mary_bonus_with_clock(obs, option, registry, _remaining_clock)


def hail_mary_bonus_with_clock(
    obs: Any,
    option: Any,
    registry: dict[int, CardFeature],
    remaining_clock: float = 999.0,
) -> float:
    if not is_psychic_control_match(obs, registry):
        return 0.0

    strategy = evaluate_hail_mary_tactics_with_clock(obs, registry, remaining_clock)
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    bonus = 0.0

    if strategy == "EXECUTE_TERMINAL_DECKOUT_COMBINATION":
        if option_name == "PLAY" and card_id in HAND_SHUFFLE_IDS:
            bonus += 6500.0
        if option_name == "END" and my_hand_size(obs) <= 2:
            bonus += 2800.0
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "SWITCH"}:
            bonus -= 2000.0

    elif strategy == "TRIGGER_FAST_PASS_STALL_SPEED":
        if option_name == "END":
            bonus += 4800.0
        if option_name in {"PLAY", "ABILITY", "ATTACK"}:
            bonus -= 1600.0
        if legal_option_is_simple_pass(option_name, ctx):
            bonus += 2200.0

    elif strategy == "ATTACH_BRACE_PROMOTE_BAIT_TO_ACTIVE":
        if option_name == "ATTACH" and card_id == SURVIVAL_BRACE:
            bonus += 5200.0
        if ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"}:
            target = card_id
            if target in BAIT_EX_IDS or (registry.get(target or -1) and "multi_prize" in registry[target].tags):
                bonus += 4600.0

    return bonus


def legal_option_is_simple_pass(option_name: str, ctx: str) -> bool:
    return option_name in {"END", "YES"} or ctx in {"PASS", "END_TURN"}
