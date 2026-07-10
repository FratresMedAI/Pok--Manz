"""Heuristic action evaluator for CABT observations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .archetypes import classify_from_card_ids
from .cards import CardFeature
from .probability import deckout_penalty, net_material_gain, prize_value


SPECIAL_ENERGY_IDS = {11, 13, 14, 18, 19}


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    pvm: float = 0.0
    material: float = 0.0
    tempo: float = 0.0
    sequencing: float = 0.0
    safety: float = 0.0
    notes: tuple[str, ...] = ()


def safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


def option_type_name(option: Any) -> str:
    value = safe_getattr(option, "type", "")
    return safe_getattr(value, "name", str(value))


def option_type_value(option: Any) -> Any:
    value = safe_getattr(option, "type", "")
    return getattr(value, "value", value)


def context_name(obs: Any) -> str:
    select = safe_getattr(obs, "select")
    context = safe_getattr(select, "context", "")
    return safe_getattr(context, "name", str(context))


def context_value(obs: Any) -> Any:
    select = safe_getattr(obs, "select")
    context = safe_getattr(select, "context", "")
    return getattr(context, "value", context)


def imitation_key(obs: Any, option: Any) -> str:
    parts = [f"context={context_value(obs)}", f"type={option_type_value(option)}"]
    for field in ("cardId", "attackId", "area", "inPlayArea"):
        value = safe_getattr(option, field)
        if value is not None:
            value = getattr(value, "value", value)
            parts.append(f"{field}={value}")
    return "|".join(parts)


def card_id_for_option(obs: Any, option: Any) -> int | None:
    if safe_getattr(option, "cardId") is not None:
        return option.cardId
    area_name = safe_getattr(safe_getattr(option, "area"), "name", "")
    index = safe_getattr(option, "index")
    player_index = safe_getattr(option, "playerIndex")
    state = safe_getattr(obs, "current")
    if state is None or index is None or player_index is None:
        return None
    players = safe_getattr(state, "players", [])
    if player_index >= len(players):
        return None
    player = players[player_index]
    zone = None
    if area_name == "HAND":
        zone = safe_getattr(player, "hand")
    elif area_name == "DISCARD":
        zone = safe_getattr(player, "discard")
    elif area_name == "ACTIVE":
        zone = safe_getattr(player, "active")
    elif area_name == "BENCH":
        zone = safe_getattr(player, "bench")
    elif area_name == "PRIZE":
        zone = safe_getattr(player, "prize")
    if not zone or index >= len(zone) or zone[index] is None:
        return None
    return safe_getattr(zone[index], "id")


def prize_count_for_card(card: CardFeature | None) -> int:
    if card is None:
        return 1
    tags = set(card.tags)
    return prize_value(is_ex="multi_prize" in tags, is_mega_ex="mega" in tags)


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


def bench_low_hp_penalty(obs: Any, card: CardFeature | None, registry: dict[int, CardFeature]) -> float:
    if card is None or card.hp <= 0 or card.hp > 70:
        return 0.0
    read = classify_from_card_ids(visible_opponent_ids(obs), registry)
    if "avoid_low_hp_bench" in read.tags and read.confidence >= 0.25:
        return 650.0
    return 0.0


def opponent_archetype_tags(obs: Any, registry: dict[int, CardFeature]) -> set[str]:
    return set(classify_from_card_ids(visible_opponent_ids(obs), registry).tags)


def prize_remaining(obs: Any, player_index: int) -> int:
    state = safe_getattr(obs, "current")
    players = safe_getattr(state, "players", []) if state is not None else []
    if player_index < 0 or player_index >= len(players):
        return 6
    return len(safe_getattr(players[player_index], "prize", []) or [])


def match_phase(obs: Any) -> str:
    state = safe_getattr(obs, "current")
    if state is None:
        return "opening"
    your_index = safe_getattr(state, "yourIndex", 0)
    opponent_index = 1 - your_index
    if prize_remaining(obs, your_index) <= 2 or prize_remaining(obs, opponent_index) <= 2:
        return "endgame"
    turn = int(safe_getattr(state, "turn", 0) or 0)
    if turn <= 4:
        return "opening"
    return "midgame"


def is_single_prize(card: CardFeature | None) -> bool:
    if card is None:
        return True
    tags = set(card.tags)
    return "multi_prize" not in tags and "mega" not in tags


def score_option(
    obs: Any,
    option: Any,
    registry: dict[int, CardFeature],
    imitation_profile: dict[str, Any] | None = None,
) -> ScoreBreakdown:
    option_name = option_type_name(option)
    ctx = context_name(obs)
    phase = match_phase(obs)
    card_id = card_id_for_option(obs, option)
    card = registry.get(card_id) if card_id is not None else None
    opp_tags = opponent_archetype_tags(obs, registry)
    notes: list[str] = []

    score = 0.0
    pvm = 0.0
    material = 0.0
    tempo = 0.0
    sequencing = 0.0
    safety = 0.0

    if option_name == "NUMBER":
        score += float(safe_getattr(option, "number", 0) or 0)
    elif option_name == "YES":
        score += 3.0
    elif option_name == "NO":
        score -= 1.0
    elif option_name == "END":
        score -= 150.0
    elif option_name == "ATTACK":
        score += 1200.0
        pvm += 400.0
        if "avoid_ex_into_crustle" in opp_tags:
            score -= 900.0
        if phase == "endgame":
            pvm += 1400.0
    elif option_name == "EVOLVE":
        score += 1600.0
        tempo += 700.0
        if phase == "opening":
            tempo += 450.0
    elif option_name == "ABILITY":
        score += 1350.0
        sequencing += 250.0
    elif option_name == "ATTACH":
        score += 1250.0
        tempo += 250.0
        if card and "prefer_non_ex_attacker" in opp_tags and card.name in {"Hariyama", "Makuhita"}:
            tempo += 700.0
    elif option_name == "RETREAT":
        score += 250.0
    elif option_name == "PLAY":
        score += 900.0
        if card:
            tags = set(card.tags)
            if "search" in tags:
                sequencing += 650.0
                notes.append("search-first")
                if phase == "opening":
                    sequencing += 600.0
            if "draw" in tags:
                sequencing += 250.0
                notes.append("draw")
            if "gust" in tags:
                pvm += 750.0
                tempo += 450.0
                notes.append("gust")
                if phase == "endgame":
                    pvm += 2200.0
            if "energy" in tags:
                tempo += 200.0
            if card.name == "Enhanced Hammer" and "hammer_special_energy" in opponent_archetype_tags(obs, registry):
                tempo += 1500.0
            if card.name in {"Crispin", "Technical Machine: Evolution"} and phase == "opening":
                sequencing += 1800.0
    elif option_name == "CARD":
        score += score_card_selection(obs, card, ctx, registry)
    else:
        score += 0.0

    if card:
        material += 150.0 * net_material_gain(prize_count_for_card(card), 1)
        safety -= bench_low_hp_penalty(obs, card, registry)

    if imitation_profile:
        bonus = imitation_profile.get("option_bonuses", {}).get(imitation_key(obs, option), 0.0)
        if bonus:
            sequencing += float(bonus)
            notes.append("imitation")

    state = safe_getattr(obs, "current")
    if state is not None:
        your_index = safe_getattr(state, "yourIndex", 0)
        player = safe_getattr(state, "players", [None])[your_index]
        deck_count = safe_getattr(player, "deckCount", 60)
        safety -= deckout_penalty(deck_count, average_cards_drawn_per_turn=2.2)

    total = score + pvm + material + tempo + sequencing + safety
    return ScoreBreakdown(total, pvm, material, tempo, sequencing, safety, tuple(notes))


def score_card_selection(obs: Any, card: CardFeature | None, ctx: str, registry: dict[int, CardFeature]) -> float:
    if card is None:
        return 0.0
    tags = set(card.tags)
    opp_tags = opponent_archetype_tags(obs, registry)
    phase = match_phase(obs)
    score = 0.0
    if ctx in {"SETUP_ACTIVE_POKEMON", "SETUP_BENCH_POKEMON", "TO_FIELD", "TO_BENCH"}:
        score += 300.0
        if card.hp >= 90:
            score += 120.0
        score -= bench_low_hp_penalty(obs, card, registry)
        if "limit_bench" in opp_tags and card.hp <= 70:
            score -= 350.0
        if phase == "opening" and "poffin_target" in tags:
            score += 300.0
    if ctx in {"TO_HAND", "LOOK"}:
        if "search" in tags:
            score += 300.0
        if "draw" in tags:
            score += 220.0
        if "gust" in tags:
            score += 450.0
        if "energy" in tags:
            score += 180.0
        if "multi_prize" in tags:
            score += 150.0
        if phase == "endgame" and ("gust" in tags or card.name in {"Boss’s Orders", "Prime Catcher"}):
            score += 1800.0
    if ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET", "SWITCH", "TO_ACTIVE"}:
        score += 200.0 * prize_count_for_card(card)
        if "multi_prize" in tags:
            score += 200.0
        if card.hp and card.hp <= 90:
            score += 180.0
        if "target_engine_basics" in opp_tags and card.card_id in {741, 742, 743, 305, 66}:
            score += 1400.0
        if "avoid_ex_into_crustle" in opp_tags and card.card_id == 345:
            score -= 1600.0
        if phase == "endgame" and card.hp and card.hp <= 170:
            score += 1200.0
        if phase == "endgame" and ctx in {"SWITCH", "TO_ACTIVE"} and is_single_prize(card):
            score += 900.0
    if ctx in {"DISCARD", "TO_DECK_BOTTOM"}:
        score -= 100.0 * prize_count_for_card(card)
        opponent_energy = visible_opponent_energy_ids(obs)
        if "energy" in tags:
            score += 80.0
        if "search" in tags or "draw" in tags or "gust" in tags:
            score -= 500.0
        if phase == "opening" and ("poffin_target" in tags or card.name in {"Technical Machine: Evolution", "Crispin"}):
            score -= 1200.0
        if card.name == "Enhanced Hammer" and not (opponent_energy & SPECIAL_ENERGY_IDS):
            score += 1400.0
        if card.name == "Nighttime Mine" and phase == "endgame":
            score += 450.0
        if "limit_bench" in opp_tags and not ({"search", "draw", "gust", "energy"} & tags):
            score += 250.0
    return score


def choose_indices(
    obs: Any,
    registry: dict[int, CardFeature],
    imitation_profile: dict[str, Any] | None = None,
) -> list[int]:
    select = safe_getattr(obs, "select")
    options = list(safe_getattr(select, "option", []) or [])
    min_count = int(safe_getattr(select, "minCount", 0) or 0)
    max_count = int(safe_getattr(select, "maxCount", 0) or 0)
    if max_count <= 0 or not options:
        return []
    ranked = sorted(
        range(len(options)),
        key=lambda index: score_option(obs, options[index], registry, imitation_profile).total,
        reverse=True,
    )
    count = max(min_count, max_count)
    return ranked[: min(count, len(ranked))]

