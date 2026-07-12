"""Dedicated pilot logic for Alakazam counter decks."""

from __future__ import annotations

from typing import Any

from .anti_psychic_control import anti_control_bonus, select_anti_control_strategy
from .cards import CardFeature, count_cards
from .control_policy import ABRA, ALAKAZAM, DUDUNSPARCE, DUNSPARCE, KADABRA, selected_card
from .evaluator import (
    card_id_for_option,
    choose_indices,
    context_name,
    opponent_archetype_tags,
    option_type_name,
    prize_remaining,
    safe_getattr,
    visible_opponent_energy_ids,
)
from .hail_mary_tactics import hail_mary_bonus
from .simulator_exploits import exploit_bonus, execute_advanced_simulator_exploits, my_active_card_id, update_match_signals
from .sneaky_board_manipulation import sneaky_bonus


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
ENHANCED_HAMMER = 1081
HAND_TRIMMER = 1087
XEROSIC = 1197
HILDA = 1225
POKE_PAD = 1152
NIGHT_STRETCHER = 1097
KYOGRE_LINE = {721}
POISON_LINE = {112, 139, 646}
ZACIAN_LINE = {299, 336, 816}
FROSLASS_LINE = {103, 104, 860, 861}
CRUSTLE_LINE = {344, 345, 532, 533}
CRUSTLE_ATTACKERS = {345, 533}
DWEBBLE = 344
MEGA_KANGASKHAN = 756
JUMBO_ICE_CREAM = 1147
LILLIE = 1227
POKEGEAR = 1122
GROW_GRASS = 18
SPIKY = 14
MIST = 11
SWITCH_CARD = 1123
BATTLE_CAGE = 1264
ROCKET_LINE = {400, 401, 1134, 1216, 1220, 1218, 1257, 434, 1094}
XERNEAS_LINE = {183, 331, 751}
CYNTHIA_LINE = {379, 380, 381}
ALAKAZAM_ENGINE = {ABRA, KADABRA, ALAKAZAM, DUNSPARCE, DUDUNSPARCE}
DRAGA_STAGING = {DREEPY, DRAKLOAK}
LUCARIO_LINE = {333, 677, 974, 678}
ABOMA_LINE = {418, 419, 722, 723}
ARCHALUDON_LINE = {169, 170, 190, 839, 840, 992}
ETHAN_FIRE_LINE = {352, 354}
STARMIE_LINE = {360, 361, 1030, 1031}
OGERPON_LINE = {95, 96, 99, 108, 117, 349, 358, 370, 386}
DAMAGE_CONTEXTS = {"DAMAGE", "DAMAGE_COUNTER", "DAMAGE_COUNTER_ANY", "EFFECT_TARGET", "SWITCH", "TO_ACTIVE"}
FAST_SETUP_TARGETS = (
    DRAGA_STAGING
    | LUCARIO_LINE
    | ABOMA_LINE
    | KYOGRE_LINE
    | STARMIE_LINE
    | FROSLASS_LINE
    | ARCHALUDON_LINE
    | POISON_LINE
    | CRUSTLE_LINE
    | XERNEAS_LINE
    | CYNTHIA_LINE
)


def is_dragapult_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(DRAGAPULT, 0) >= 2 and counts.get(DREEPY, 0) >= 3


def is_ogerpon_wall_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(CORNERSTONE, 0) >= 2 and counts.get(TEAL_OGERPON, 0) >= 2


def is_iron_thorns_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(IRON_THORNS, 0) >= 2


def is_crustle_kangaskhan_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(345, 0) >= 2 and counts.get(MEGA_KANGASKHAN, 0) >= 2 and counts.get(DWEBBLE, 0) >= 3


def is_rocket_spidops_deck(deck: list[int]) -> bool:
    counts = count_cards(deck)
    return counts.get(401, 0) >= 2 and counts.get(400, 0) >= 3


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


def hand_size(obs: Any) -> int:
    state = safe_getattr(obs, "current")
    if state is None:
        return 0
    your_index = safe_getattr(state, "yourIndex", 0)
    players = safe_getattr(state, "players", [])
    if your_index >= len(players):
        return 0
    return len(safe_getattr(players[your_index], "hand", []) or [])


def turn_count(obs: Any) -> int:
    state = safe_getattr(obs, "current")
    return int(safe_getattr(state, "turn", 0) or 0) if state is not None else 0


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
        elif card_id in {BOSS, PRIME_CATCHER, 1124}:
            score += 2200.0

    if option_name == "PLAY":
        if card_id in {1087, 1197}:
            score += 2800.0
        if card_id in {1088, 1182, 1124}:
            score += 3000.0
        if card_id == 11:
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
        if card_id in {986, 112, 139}:
            score += 2200.0

    if option_name == "ATTACH" and card_id == 11:
        score += 3000.0

    if option_name == "CARD":
        selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"} and selected_id == DREEPY:
            score += 2400.0
        elif ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET", "SWITCH", "TO_ACTIVE"}:
            if selected_id in {DUNSPARCE, DUDUNSPARCE}:
                score += 5200.0
            elif selected_id in ALAKAZAM_ENGINE:
                score += 2200.0
            elif selected_id in {FEZANDIPITI, 343, 391}:
                score += 2400.0

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


def crustle_kangaskhan_score_option(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    """Leaderboard #1 pilot: wall with Crustle, race with Kangaskhan, skip ex trades."""
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    counts = board_counts(obs, your_index)
    turn = turn_count(obs)
    active_id = my_active_card_id(obs)
    opp_tags = opponent_archetype_tags(obs, registry)
    score = 0.0

    if option_name == "PLAY":
        if card_id == POFFIN and counts.get(DWEBBLE, 0) < 2:
            score += 4800.0
        elif card_id == POKEGEAR:
            score += 4200.0 if turn <= 5 else 2600.0
        elif card_id == JUMBO_ICE_CREAM:
            score += 3600.0 if hand_size(obs) <= 5 else 2200.0
        elif card_id == LILLIE:
            score += 3400.0
        elif card_id == HILDA:
            score += 3000.0 if hand_size(obs) <= 4 else 1800.0
        elif card_id == XEROSIC:
            score += 3200.0 if opp_tags & {"target_engine_basics", "disruption", "gust_engine"} else 2400.0
        elif card_id == BATTLE_CAGE:
            score += 3000.0 if turn <= 6 else 1600.0
        elif card_id in {BOSS, PRIME_CATCHER}:
            score += 2600.0
        elif card_id == SWITCH_CARD:
            score += 1400.0

    if option_name == "EVOLVE":
        evolve_target = safe_getattr(selected_card(obs, option), "id")
        if evolve_target in {DWEBBLE, 532} or card_id in CRUSTLE_ATTACKERS:
            score += 5200.0

    if option_name == "ABILITY" and active_id == MEGA_KANGASKHAN:
        score += 3600.0

    if option_name == "ATTACH":
        target_id = safe_getattr(selected_card(obs, option), "id")
        if target_id in CRUSTLE_ATTACKERS:
            score += 4000.0
        elif target_id == MEGA_KANGASKHAN:
            score += 2800.0
        elif target_id == DWEBBLE:
            score += 1200.0
        if card_id in {GROW_GRASS, SPIKY, MIST}:
            score += 600.0

    if option_name == "ATTACK":
        score += 3200.0
        if active_id in CRUSTLE_ATTACKERS:
            score += 4200.0
        elif active_id == MEGA_KANGASKHAN:
            score += 800.0 if "ex_damage_wall" not in opp_tags else -1800.0

    if option_name == "CARD":
        selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
        if ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH", "TO_FIELD"} and selected_id == DWEBBLE:
            score += 3800.0
        elif ctx in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and selected_id in CRUSTLE_ATTACKERS:
            score += 4400.0
        elif ctx in DAMAGE_CONTEXTS and selected_id in ALAKAZAM_ENGINE:
            score += 3000.0
        elif ctx in DAMAGE_CONTEXTS and selected_id in ROCKET_LINE:
            score += 3400.0
        elif ctx in DAMAGE_CONTEXTS and selected_id in CRUSTLE_LINE:
            score += 2200.0

    crustle_ready = sum(counts.get(cid, 0) for cid in CRUSTLE_ATTACKERS)
    if crustle_ready == 0 and option_name in {"PLAY", "CARD", "EVOLVE"}:
        score += 800.0
    if option_name == "END":
        score -= 250.0

    return score


def crustle_matchup_bonus(
    obs: Any,
    option: Any,
    registry: dict[int, CardFeature],
    opponent_archetype: str,
    opponent_confidence: float,
) -> float:
    if opponent_confidence < 0.15:
        return 0.0

    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
    active_id = my_active_card_id(obs)
    turn = turn_count(obs)
    bonus = 0.0

    if opponent_archetype == "alakazam_control":
        if option_name == "PLAY" and card_id == XEROSIC:
            bonus += 1800.0
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER}:
            bonus += 1600.0
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
            bonus += 2200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ALAKAZAM_ENGINE:
            bonus += 2600.0

    elif opponent_archetype == "rocket_spidops":
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER} and turn <= 12:
            bonus += 3000.0
        if option_name == "PLAY" and card_id == BATTLE_CAGE and turn <= 7:
            bonus += 2600.0
        if option_name == "PLAY" and card_id == XEROSIC:
            bonus += 2000.0
        if ctx in DAMAGE_CONTEXTS and selected_id in {400, 401}:
            bonus += 3600.0
        if option_name == "ABILITY" and active_id == MEGA_KANGASKHAN and turn <= 10:
            bonus += 2200.0
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS and turn <= 8:
            bonus += 1200.0

    elif opponent_archetype == "crustle_wall":
        if option_name == "PLAY" and card_id in {JUMBO_ICE_CREAM, LILLIE}:
            bonus += 2000.0
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER} and turn <= 8:
            bonus += 2600.0
        if ctx in DAMAGE_CONTEXTS and selected_id in {DWEBBLE, 532}:
            bonus += 4000.0
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
            bonus += 2200.0
        if option_name == "ATTACK" and active_id == MEGA_KANGASKHAN:
            bonus -= 1800.0

    elif opponent_archetype == "starmie":
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER} and turn <= 12:
            bonus += 3200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in STARMIE_LINE | FROSLASS_LINE:
            bonus += 4000.0
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS and turn <= 10:
            bonus += 2400.0
        if option_name == "PLAY" and card_id == BATTLE_CAGE and turn <= 6:
            bonus += 1800.0

    elif opponent_archetype == "mega_poison":
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER, XEROSIC}:
            bonus += 2200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in POISON_LINE:
            bonus += 3000.0
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
            bonus += 1600.0

    elif opponent_archetype == "dragapult":
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER}:
            bonus += 1800.0
        if ctx in DAMAGE_CONTEXTS and selected_id in DRAGA_STAGING:
            bonus += 2800.0

    elif opponent_archetype == "lucario":
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER} and turn <= 10:
            bonus += 1600.0
        if ctx in DAMAGE_CONTEXTS and selected_id in LUCARIO_LINE:
            bonus += 2400.0

    return bonus


def crustle_play_mode_bonus(
    obs: Any,
    option: Any,
    registry: dict[int, CardFeature],
    play_mode: str,
    opponent_archetype: str,
    opponent_confidence: float,
) -> float:
    if opponent_confidence < 0.15 or play_mode == "standard":
        return 0.0

    option_name = option_type_name(option)
    card_id = card_id_for_option(obs, option)
    active_id = my_active_card_id(obs)
    turn = turn_count(obs)
    bonus = 0.0

    if play_mode == "disruption":
        if option_name == "PLAY" and card_id in {XEROSIC, BATTLE_CAGE, BOSS, PRIME_CATCHER}:
            bonus += 1400.0
        if option_name == "ABILITY" and active_id == MEGA_KANGASKHAN and turn <= 12:
            bonus += 1000.0

    elif play_mode == "wall":
        if option_name in {"EVOLVE", "ATTACH"}:
            bonus += 900.0
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
            bonus += 1200.0

    elif play_mode == "ladder_pressure":
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
            bonus += 1600.0
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER}:
            bonus += 1200.0

    elif play_mode == "endgame_rush":
        if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
            bonus += 2000.0
        if option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER}:
            bonus += 1800.0

    return bonus


def crustle_endgame_bonus(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    state = safe_getattr(obs, "current")
    if state is None:
        return 0.0
    your_index = safe_getattr(state, "yourIndex", 0)
    opponent_index = 1 - your_index
    if prize_remaining(obs, your_index) > 2 and prize_remaining(obs, opponent_index) > 2:
        return 0.0

    option_name = option_type_name(option)
    card_id = card_id_for_option(obs, option)
    active_id = my_active_card_id(obs)
    bonus = 0.0
    if option_name == "ATTACK" and active_id in CRUSTLE_ATTACKERS:
        bonus += 2000.0
    elif option_name == "PLAY" and card_id in {BOSS, PRIME_CATCHER}:
        bonus += 1600.0
    elif option_name == "ATTACK" and active_id == MEGA_KANGASKHAN:
        bonus -= 800.0
    return bonus


def iron_thorns_score_option(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    state = safe_getattr(obs, "current")
    your_index = safe_getattr(state, "yourIndex", 0) if state is not None else 0
    counts = board_counts(obs, your_index)
    turn = turn_count(obs)
    score = 0.0

    if option_name == "PLAY":
        if card_id == ULTRA_BALL:
            score += 2600.0
        elif card_id == CRISPIN:
            score += 2400.0
        elif card_id == HILDA:
            score += 1900.0 if turn <= 6 or hand_size(obs) <= 4 else 900.0
        elif card_id == POKE_PAD:
            score += 1300.0
        elif card_id == NIGHT_STRETCHER:
            score += 900.0
        elif card_id == RARE_CANDY:
            score -= 900.0
        elif card_id in {BOSS, PRIME_CATCHER}:
            score += 2000.0
        elif card_id in {HAND_TRIMMER, XEROSIC}:
            score += 700.0

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
        elif ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"} and selected_id == IRON_THORNS:
            score += 2600.0 if counts.get(IRON_THORNS, 0) < 2 else -1200.0
        elif ctx in {"SETUP_BENCH_POKEMON", "TO_BENCH"} and selected_id != IRON_THORNS:
            score -= 1500.0
        elif ctx in {"DAMAGE", "DAMAGE_COUNTER", "EFFECT_TARGET"} and selected_id in ALAKAZAM_ENGINE:
            score += 2800.0
        elif ctx in DAMAGE_CONTEXTS and selected_id in FAST_SETUP_TARGETS:
            score += 1800.0

    if counts.get(IRON_THORNS, 0) == 0 and option_name in {"PLAY", "CARD", "EVOLVE"}:
        score += 600.0
    if option_name == "END":
        score -= 300.0

    return score


def going_first_tempo_bonus(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    state = safe_getattr(obs, "current")
    if state is None:
        return 0.0
    your_index = safe_getattr(state, "yourIndex", 0)
    if safe_getattr(state, "firstPlayer", None) != your_index:
        return 0.0
    turn = int(safe_getattr(state, "turn", 0) or 0)
    if turn > 4:
        return 0.0

    option_name = option_type_name(option)
    card_id = card_id_for_option(obs, option)
    bonus = 0.0
    if option_name == "PLAY" and card_id in {ULTRA_BALL, POFFIN, CRISPIN, HILDA, POKE_PAD, POKEGEAR, JUMBO_ICE_CREAM}:
        bonus += 1400.0
    if option_name == "ATTACH":
        target_id = safe_getattr(selected_card(obs, option), "id")
        if target_id == IRON_THORNS:
            bonus += 1200.0
        elif target_id in {345, 533, 756, 344}:
            bonus += 1100.0
    if option_name == "CARD":
        selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
        if context_name(obs) in {"SETUP_ACTIVE_POKEMON", "TO_ACTIVE", "SWITCH"} and selected_id == IRON_THORNS:
            bonus += 1000.0
        elif selected_id in {344, 345, 533}:
            bonus += 900.0
    return bonus


def play_mode_bonus(
    obs: Any,
    option: Any,
    registry: dict[int, CardFeature],
    play_mode: str,
    opponent_archetype: str,
    opponent_confidence: float = 0.0,
) -> float:
    """Targeted matchup nudges only — never override anti-control on Alakazam."""
    if opponent_confidence < 0.2:
        return 0.0
    if opponent_archetype in {"alakazam_control", "unknown"}:
        return 0.0
    if "psychic_control" in opponent_archetype_tags(obs, registry):
        return 0.0

    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
    state = safe_getattr(obs, "current")
    turn = int(safe_getattr(state, "turn", 0) or 0) if state is not None else 0
    gust_cards = {BOSS, PRIME_CATCHER, 1124}
    bonus = 0.0

    if opponent_archetype == "abomasnow":
        if option_name == "PLAY" and card_id in gust_cards and turn <= 10:
            bonus += 1600.0
        if option_name == "PLAY" and card_id == ENHANCED_HAMMER:
            bonus += 1400.0
        if option_name == "ATTACK" and turn <= 8:
            bonus += 900.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ABOMA_LINE | KYOGRE_LINE:
            bonus += 1800.0

    elif opponent_archetype == "lucario":
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 1400.0
        if ctx in DAMAGE_CONTEXTS and selected_id in LUCARIO_LINE:
            bonus += 1600.0

    elif opponent_archetype == "archaludon_metal":
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 1200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ARCHALUDON_LINE | ZACIAN_LINE:
            bonus += 1400.0

    elif opponent_archetype == "mega_poison":
        if option_name == "PLAY" and card_id in {HAND_TRIMMER, XEROSIC}:
            bonus += 1200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in POISON_LINE:
            bonus += 1400.0

    elif opponent_archetype == "starmie":
        if option_name == "PLAY" and card_id in gust_cards and turn <= 10:
            bonus += 1500.0
        if ctx in DAMAGE_CONTEXTS and selected_id in STARMIE_LINE | FROSLASS_LINE:
            bonus += 1800.0

    elif opponent_archetype == "crustle_wall":
        if option_name == "PLAY" and card_id in gust_cards and turn <= 8:
            bonus += 2200.0
        if option_name == "PLAY" and card_id == ENHANCED_HAMMER:
            bonus += 2000.0
        if option_name == "ATTACK":
            bonus -= 1400.0
        if ctx in DAMAGE_CONTEXTS and selected_id in CRUSTLE_LINE:
            bonus += 2800.0

    elif opponent_archetype == "rocket_spidops":
        if option_name == "PLAY" and card_id in gust_cards and turn <= 10:
            bonus += 2000.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ROCKET_LINE:
            bonus += 2400.0

    elif opponent_archetype in {"zacian_box", "xerneas_box", "cynthia_box"}:
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 1200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ZACIAN_LINE | XERNEAS_LINE | CYNTHIA_LINE:
            bonus += 1600.0

    return bonus


def ladder_matchup_bonus(obs: Any, option: Any, registry: dict[int, CardFeature]) -> float:
    """Iron Thorns scoring for common ladder decks beyond Alakazam control."""
    opp_tags = opponent_archetype_tags(obs, registry)
    if not opp_tags or opp_tags == {"fallback"}:
        return 0.0

    option_name = option_type_name(option)
    ctx = context_name(obs)
    card_id = card_id_for_option(obs, option)
    selected_id = safe_getattr(selected_card(obs, option), "id") or card_id
    bonus = 0.0
    gust_cards = {BOSS, PRIME_CATCHER, 1124}

    if "bench_damage" in opp_tags or "stage2_clock" in opp_tags:
        if option_name == "ATTACK":
            bonus += 1400.0
        if ctx in DAMAGE_CONTEXTS and selected_id in DRAGA_STAGING:
            bonus += 3800.0
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2200.0

    if "fighting_pressure" in opp_tags or "high_damage" in opp_tags:
        if option_name == "ATTACK":
            bonus += 2000.0
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2600.0
        if ctx in DAMAGE_CONTEXTS and selected_id in LUCARIO_LINE:
            bonus += 2400.0

    if "slow_pressure" in opp_tags or opp_tags & {"hammer_special_energy"}:
        if option_name == "ATTACK":
            bonus += 1800.0
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2400.0
        if option_name == "PLAY" and card_id == ENHANCED_HAMMER and visible_opponent_energy_ids(obs):
            bonus += 2000.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ABOMA_LINE | KYOGRE_LINE:
            bonus += 2600.0

    if "item_lock" in opp_tags or "energy_denial" in opp_tags:
        if option_name == "ATTACK":
            bonus += 2200.0
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2800.0

    if "metal_wall" in opp_tags:
        if option_name == "ATTACK":
            bonus += 1600.0
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2400.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ARCHALUDON_LINE | ZACIAN_LINE:
            bonus += 2200.0

    if "energy_acceleration" in opp_tags or "gust_engine" in opp_tags:
        if option_name == "ATTACK":
            bonus += 1800.0
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in OGERPON_LINE:
            bonus += 2600.0

    if "fast_attacker" in opp_tags or "spread_pressure" in opp_tags:
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2800.0
        if option_name == "ATTACK":
            bonus += 2000.0
        if ctx in DAMAGE_CONTEXTS and selected_id in STARMIE_LINE | FROSLASS_LINE | XERNEAS_LINE | ZACIAN_LINE:
            bonus += 3200.0

    if "rush_pressure" in opp_tags:
        if option_name == "ATTACK":
            bonus += 2000.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ETHAN_FIRE_LINE:
            bonus += 2800.0

    if "poison_pressure" in opp_tags or "disruption" in opp_tags:
        if option_name == "ATTACK":
            bonus += 1600.0
        if option_name == "PLAY" and card_id in {HAND_TRIMMER, XEROSIC}:
            bonus += 1800.0
        if ctx in DAMAGE_CONTEXTS and selected_id in POISON_LINE:
            bonus += 1600.0

    if "target_engine_basics" in opp_tags:
        if ctx in DAMAGE_CONTEXTS and selected_id in ALAKAZAM_ENGINE:
            bonus += 2400.0

    if "ex_damage_wall" in opp_tags:
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2400.0
        if option_name == "PLAY" and card_id == ENHANCED_HAMMER and visible_opponent_energy_ids(obs):
            bonus += 2200.0
        if option_name == "ATTACK":
            bonus -= 1200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in CRUSTLE_LINE:
            bonus += 3200.0

    if "gust_engine" in opp_tags and "disruption" in opp_tags:
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 2000.0
        if ctx in DAMAGE_CONTEXTS and selected_id in ROCKET_LINE:
            bonus += 2600.0

    if "setup_shell" in opp_tags:
        if option_name == "PLAY" and card_id in gust_cards:
            bonus += 1200.0
        if ctx in DAMAGE_CONTEXTS and selected_id in CYNTHIA_LINE:
            bonus += 2200.0

    return bonus


def counter_option_score(
    obs: Any,
    option: Any,
    registry: dict[int, CardFeature],
    deck: list[int],
    scorer,
    play_mode: str = "standard",
    opponent_archetype: str = "unknown",
    opponent_confidence: float = 0.0,
) -> float:
    score = (
        scorer(obs, option, registry)
        + anti_control_bonus(obs, option, registry)
        + sneaky_bonus(obs, option, registry)
        + exploit_bonus(obs, option, registry)
        + hail_mary_bonus(obs, option, registry)
    )
    if is_iron_thorns_deck(deck):
        score += ladder_matchup_bonus(obs, option, registry)
        score += going_first_tempo_bonus(obs, option, registry)
        score += play_mode_bonus(
            obs, option, registry, play_mode, opponent_archetype, opponent_confidence
        )
    elif is_crustle_kangaskhan_deck(deck):
        score += crustle_matchup_bonus(
            obs, option, registry, opponent_archetype, opponent_confidence
        )
        score += crustle_play_mode_bonus(
            obs, option, registry, play_mode, opponent_archetype, opponent_confidence
        )
        score += crustle_endgame_bonus(obs, option, registry)
        score += going_first_tempo_bonus(obs, option, registry)
    return score


def choose_counter_indices(
    obs: Any,
    deck: list[int],
    registry: dict[int, CardFeature],
    imitation_profile: dict[str, Any] | None = None,
    play_mode: str = "standard",
    opponent_archetype: str = "unknown",
    opponent_confidence: float = 0.0,
) -> list[int]:
    if is_dragapult_deck(deck):
        scorer = dragapult_score_option
    elif is_ogerpon_wall_deck(deck):
        scorer = ogerpon_score_option
    elif is_crustle_kangaskhan_deck(deck):
        scorer = crustle_kangaskhan_score_option
    elif is_iron_thorns_deck(deck):
        scorer = iron_thorns_score_option
    else:
        return choose_indices(obs, registry, imitation_profile)

    select = safe_getattr(obs, "select")
    options = list(safe_getattr(select, "option", []) or [])
    min_count = int(safe_getattr(select, "minCount", 0) or 0)
    max_count = int(safe_getattr(select, "maxCount", 0) or 0)
    if not options:
        return []
    ranked = sorted(
        range(len(options)),
        key=lambda index: counter_option_score(
            obs,
            options[index],
            registry,
            deck,
            scorer,
            play_mode=play_mode,
            opponent_archetype=opponent_archetype,
            opponent_confidence=opponent_confidence,
        ),
        reverse=True,
    )
    count = max(min_count, max_count)
    return ranked[: min(count, len(ranked))]
