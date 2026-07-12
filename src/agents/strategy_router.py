"""Meta layer: pick deck archetype and in-game play mode from matchup signals."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from .archetypes import ArchetypeRead, classify_from_card_ids
from .cards import (
    CardFeature,
    alakazam_control_deck,
    count_cards,
    crustle_kangaskhan_deck,
    dragapult_snipe_deck,
    iron_thorns_counter_deck,
    lucario_deck,
    ogerpon_wall_deck,
    rocket_spidops_deck,
)
from .control_policy import choose_control_indices, is_alakazam_deck
from .counter_policy import (
    choose_counter_indices,
    is_crustle_kangaskhan_deck,
    is_dragapult_deck,
    is_iron_thorns_deck,
    is_ogerpon_wall_deck,
    is_rocket_spidops_deck,
)
from .evaluator import choose_indices, prize_remaining, safe_getattr


DeckFactory = Callable[[], list[int]]

DECK_ARCHETYPES: dict[str, DeckFactory] = {
    "crustle_kangaskhan": crustle_kangaskhan_deck,
    "rocket_spidops": rocket_spidops_deck,
    "lucario": lucario_deck,
    "alakazam": alakazam_control_deck,
    "dragapult": dragapult_snipe_deck,
    "ogerpon": ogerpon_wall_deck,
    "iron_thorns": iron_thorns_counter_deck,
}

# Leaderboard 50-game meta (Jul 2026): Crustle/Kangaskhan dominates.
GAUNTLET_MATCHUPS: dict[str, dict[str, float]] = {
    "crustle_kangaskhan": {"vs_alakazam": 0.727, "vs_ladder_est": 0.620, "vs_rocket_spidops": 0.273},
    "iron_thorns": {"vs_alakazam": 0.687, "vs_ladder_est": 0.462},
    "rocket_spidops": {"vs_crustle_wall": 0.727, "vs_ladder_est": 0.450},
    "dragapult": {"vs_alakazam": 0.432},
    "ogerpon": {"vs_alakazam": 0.242},
    "lucario": {"vs_baseline": 0.655},
    "alakazam": {"vs_mirror_est": 0.50},
}

# Blind Kaggle: we still pilot one deck, but telemetry notes ideal counter.
OPPONENT_COUNTER_DECK: dict[str, str] = {
    "alakazam_control": "crustle_kangaskhan",
    "crustle_wall": "crustle_kangaskhan",
    "rocket_spidops": "crustle_kangaskhan",
    "dragapult": "crustle_kangaskhan",
    "abomasnow": "crustle_kangaskhan",
    "walrein_lock": "crustle_kangaskhan",
    "lucario": "crustle_kangaskhan",
    "archaludon_metal": "crustle_kangaskhan",
    "ogerpon_toolbox": "crustle_kangaskhan",
    "starmie": "crustle_kangaskhan",
    "ethan_fire": "crustle_kangaskhan",
    "mega_poison": "crustle_kangaskhan",
    "noctowl_shell": "crustle_kangaskhan",
    "rogue_box": "crustle_kangaskhan",
}

PLAY_MODES = (
    "standard",
    "ability_lock",
    "ladder_pressure",
    "bench_snipe",
    "control_grind",
    "wall",
    "disruption",
    "endgame_rush",
)


@dataclass(frozen=True)
class StrategyPlan:
    deck_archetype: str
    play_mode: str
    opponent_archetype: str
    opponent_confidence: float
    notes: tuple[str, ...] = ()


def classify_our_deck(deck: list[int]) -> str:
    if is_crustle_kangaskhan_deck(deck):
        return "crustle_kangaskhan"
    if is_rocket_spidops_deck(deck):
        return "rocket_spidops"
    if is_alakazam_deck(deck):
        return "alakazam"
    if is_iron_thorns_deck(deck):
        return "iron_thorns"
    if is_dragapult_deck(deck):
        return "dragapult"
    if is_ogerpon_wall_deck(deck):
        return "ogerpon"
    counts = count_cards(deck)
    if counts.get(678, 0) >= 2:
        return "lucario"
    return "unknown"


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
    for pokemon in list(safe_getattr(opponent, "active", []) or []) + list(
        safe_getattr(opponent, "bench", []) or []
    ):
        if pokemon is not None and safe_getattr(pokemon, "id") is not None:
            ids.append(pokemon.id)
    return ids


def classify_opponent(obs: Any, registry: dict[int, CardFeature]) -> ArchetypeRead:
    return classify_from_card_ids(visible_opponent_ids(obs), registry)


def recommended_counter_deck(opponent: ArchetypeRead) -> str:
    if opponent.confidence < 0.15:
        return "crustle_kangaskhan"
    return OPPONENT_COUNTER_DECK.get(opponent.name, "crustle_kangaskhan")


def select_play_mode(
    obs: Any,
    deck_archetype: str,
    opponent: ArchetypeRead,
    registry: dict[int, CardFeature],
) -> str:
    """In-game tactical mode once opponent pieces are visible."""
    state = safe_getattr(obs, "current")
    if state is None or opponent.confidence < 0.15:
        return "standard"

    your_index = safe_getattr(state, "yourIndex", 0)
    opponent_index = 1 - your_index
    endgame = prize_remaining(obs, your_index) <= 2 or prize_remaining(obs, opponent_index) <= 2

    if deck_archetype == "crustle_kangaskhan":
        if opponent.name == "alakazam_control":
            return "endgame_rush" if endgame else "disruption"
        if opponent.name in {"rocket_spidops", "starmie", "mega_poison"}:
            return "endgame_rush" if endgame else "disruption"
        if opponent.name == "crustle_wall":
            return "endgame_rush" if endgame else "wall"
        if opponent.name in {"dragapult", "lucario", "ethan_fire"}:
            return "endgame_rush" if endgame else "ladder_pressure"
        return "endgame_rush" if endgame else "wall"

    if deck_archetype == "rocket_spidops":
        if opponent.name == "crustle_wall":
            return "endgame_rush" if endgame else "disruption"
        return "endgame_rush" if endgame else "disruption"

    if deck_archetype == "iron_thorns":
        if opponent.name == "alakazam_control":
            return "endgame_rush" if endgame else "ability_lock"
        if opponent.name == "mega_poison":
            return "endgame_rush" if endgame else "disruption"
        if opponent.name in {"dragapult", "starmie", "ethan_fire"}:
            return "endgame_rush" if endgame else "ladder_pressure"
        if opponent.name in {"abomasnow", "walrein_lock", "archaludon_metal", "lucario"}:
            return "endgame_rush" if endgame else "ladder_pressure"
        if opponent.name in {"ogerpon_toolbox", "crustle_wall"}:
            return "endgame_rush" if endgame else "ladder_pressure"
        return "endgame_rush" if endgame else "ladder_pressure"

    if deck_archetype == "dragapult":
        if opponent.name == "alakazam_control":
            return "bench_snipe"
        return "ladder_pressure" if endgame else "bench_snipe"

    if deck_archetype == "alakazam":
        return "endgame_rush" if endgame else "control_grind"

    if deck_archetype == "ogerpon":
        return "endgame_rush" if endgame else "wall"

    return "standard"


def build_strategy_plan(obs: Any, deck: list[int], registry: dict[int, CardFeature]) -> StrategyPlan:
    deck_archetype = classify_our_deck(deck)
    opponent = classify_opponent(obs, registry)
    play_mode = select_play_mode(obs, deck_archetype, opponent, registry)
    notes: list[str] = []
    if opponent.confidence >= 0.15:
        counter = recommended_counter_deck(opponent)
        if counter != deck_archetype:
            notes.append(f"counter_deck={counter}")
    if play_mode != "standard":
        notes.append(f"mode={play_mode}")
    return StrategyPlan(
        deck_archetype=deck_archetype,
        play_mode=play_mode,
        opponent_archetype=opponent.name,
        opponent_confidence=opponent.confidence,
        notes=tuple(notes),
    )


def resolve_deck_mode() -> str:
    """Submission deck selector. Blind at Kaggle game start — env/default only for now."""
    strategy = os.environ.get("POKEMAYNE_STRATEGY", "").lower().strip()
    if strategy in {"", "auto", "fixed"}:
        return os.environ.get("POKEMAYNE_DECK", "crustle_kangaskhan").lower()
    if strategy in DECK_ARCHETYPES:
        return strategy
    return os.environ.get("POKEMAYNE_DECK", "crustle_kangaskhan").lower()


def select_deck_for_submission() -> list[int]:
    mode = resolve_deck_mode()
    factory = DECK_ARCHETYPES.get(mode)
    if factory is None:
        return lucario_deck()
    return factory()


def choose_action_indices(
    obs: Any,
    deck: list[int],
    registry: dict[int, CardFeature],
    imitation_profile: dict[str, Any] | None = None,
    plan: StrategyPlan | None = None,
) -> list[int]:
    """Route to the correct policy stack for our deck archetype."""
    if plan is None:
        plan = build_strategy_plan(obs, deck, registry)
    deck_archetype = plan.deck_archetype
    if deck_archetype == "alakazam":
        return choose_control_indices(obs, registry, imitation_profile)
    if deck_archetype in {"dragapult", "ogerpon", "iron_thorns", "crustle_kangaskhan", "rocket_spidops"}:
        return choose_counter_indices(
            obs,
            deck,
            registry,
            imitation_profile,
            play_mode=plan.play_mode,
            opponent_archetype=plan.opponent_archetype,
            opponent_confidence=plan.opponent_confidence,
        )
    return choose_indices(obs, registry, imitation_profile)
