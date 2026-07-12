"""Helpers for CABT enum values that arrive as raw ints in Kaggle replays."""

from __future__ import annotations

from typing import Any


AREA_NAMES = {
    1: "DECK",
    2: "HAND",
    3: "DISCARD",
    4: "ACTIVE",
    5: "BENCH",
    6: "PRIZE",
    7: "STADIUM",
    8: "ENERGY",
    9: "TOOL",
    10: "PRE_EVOLUTION",
    11: "PLAYER",
    12: "LOOKING",
}

OPTION_TYPE_NAMES = {
    0: "NUMBER",
    1: "YES",
    2: "NO",
    3: "CARD",
    4: "TOOL_CARD",
    5: "ENERGY_CARD",
    6: "ENERGY",
    7: "PLAY",
    8: "ATTACH",
    9: "EVOLVE",
    10: "ABILITY",
    11: "DISCARD",
    12: "RETREAT",
    13: "ATTACK",
    14: "END",
    15: "SPECIAL_CONDITION",
}

CONTEXT_NAMES = {
    0: "MAIN",
    1: "SETUP_ACTIVE_POKEMON",
    2: "SETUP_BENCH_POKEMON",
    3: "SWITCH",
    4: "TO_ACTIVE",
    5: "TO_BENCH",
    6: "TO_FIELD",
    7: "TO_HAND",
    8: "DISCARD",
    9: "TO_DECK",
    10: "TO_DECK_BOTTOM",
    11: "TO_PRIZE",
    12: "NOT_MOVE",
    13: "DAMAGE_COUNTER",
    14: "DAMAGE_COUNTER_ANY",
    15: "DAMAGE",
    16: "REMOVE_DAMAGE_COUNTER",
    17: "HEAL",
    18: "EVOLVES_FROM",
    19: "EVOLVES_TO",
    20: "DEVOLVE",
    21: "ATTACH_FROM",
    22: "ATTACH_TO",
    23: "DETACH_FROM",
    24: "LOOK",
    25: "EFFECT_TARGET",
    26: "DISCARD_ENERGY_CARD",
    27: "DISCARD_TOOL_CARD",
    28: "SWITCH_ENERGY_CARD",
    29: "DISCARD_CARD_OR_ATTACHED_CARD",
    30: "DISCARD_ENERGY",
    31: "TO_HAND_ENERGY",
    32: "TO_DECK_ENERGY",
    33: "SWITCH_ENERGY",
    34: "SKILL_ORDER",
    35: "ATTACK",
    36: "DISABLE_ATTACK",
    37: "EVOLVE",
    38: "DRAW_COUNT",
    39: "DAMAGE_COUNTER_COUNT",
    40: "REMOVE_DAMAGE_COUNTER_COUNT",
    41: "IS_FIRST",
    42: "MULLIGAN",
    43: "ACTIVATE",
    44: "FIRST_EFFECT",
    45: "MORE_DEVOLVE",
    46: "COIN_HEAD",
    47: "AFFECT_SPECIAL_CONDITION",
    48: "RECOVER_SPECIAL_CONDITION",
}


def enum_name(value: Any, names: dict[int, str]) -> str:
    """Return enum names for both SDK IntEnums and Kaggle's raw integer JSON values."""
    if hasattr(value, "name"):
        return str(value.name)
    try:
        return names[int(value)]
    except (TypeError, ValueError, KeyError):
        return str(value)


def area_name_for(value: Any) -> str:
    return enum_name(value, AREA_NAMES)


def option_type_name_for(value: Any) -> str:
    return enum_name(value, OPTION_TYPE_NAMES)


def context_name_for(value: Any) -> str:
    return enum_name(value, CONTEXT_NAMES)
