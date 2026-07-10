"""Kaggle entry point for the PokeMayne CABT agent."""

from __future__ import annotations

import os
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
for candidate in (HERE, HERE.parent):
    if (candidate / "src").exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from cg.api import all_card_data, to_observation_class
from src.agents.cards import (
    CardFeature,
    alakazam_control_deck,
    dragapult_snipe_deck,
    iron_thorns_counter_deck,
    lucario_deck,
    ogerpon_wall_deck,
)
from src.agents.control_policy import choose_control_indices, is_alakazam_deck
from src.agents.counter_policy import choose_counter_indices, is_dragapult_deck, is_iron_thorns_deck, is_ogerpon_wall_deck
from src.agents.evaluator import choose_indices, context_value, match_phase, option_type_name, safe_getattr
from src.agents.anti_psychic_control import check_anti_alakazam_overrides
from src.agents.simulator_exploits import execute_advanced_simulator_exploits, update_match_signals
from src.agents.state_tracker import GameStateTracker
from src.agents.telemetry_logger import log_decision


_REGISTRY: dict[int, CardFeature] | None = None
_DECK: list[int] | None = None
_IMITATION_PROFILE: dict | None = None
_TRACKER: GameStateTracker | None = None
_LOOP_GUARD: "LoopGuard | None" = None
SOFT_DEADLINE_SECONDS = 4.5
LOOP_GUARD_THRESHOLD = 3


@dataclass
class LoopGuard:
    """Detects repeated non-progress board states across our turns."""

    last_signature: tuple | None = None
    last_prize_pair: tuple[int, int] | None = None
    last_turn_seen: int | None = None
    stable_turns: int = 0

    def observe(self, obs) -> bool:
        state = safe_getattr(obs, "current")
        if state is None:
            return False
        turn = int(safe_getattr(state, "turn", 0) or 0)
        if self.last_turn_seen == turn:
            return self.stable_turns >= LOOP_GUARD_THRESHOLD
        self.last_turn_seen = turn

        signature = board_signature(obs)
        prize_pair = prize_pair_signature(obs)
        if self.last_prize_pair is not None and prize_pair != self.last_prize_pair:
            self.stable_turns = 0
        elif signature == self.last_signature:
            self.stable_turns += 1
        else:
            self.stable_turns = 1

        self.last_signature = signature
        self.last_prize_pair = prize_pair
        return self.stable_turns >= LOOP_GUARD_THRESHOLD


def read_deck_csv() -> list[int]:
    global _DECK
    if _DECK is not None:
        return _DECK
    deck_mode = os.environ.get("POKEMAYNE_DECK", "lucario").lower()
    if deck_mode == "lucario":
        _DECK = lucario_deck()
        return _DECK
    if deck_mode == "alakazam":
        _DECK = alakazam_control_deck()
        return _DECK
    if deck_mode == "dragapult":
        _DECK = dragapult_snipe_deck()
        return _DECK
    if deck_mode == "ogerpon":
        _DECK = ogerpon_wall_deck()
        return _DECK
    if deck_mode == "iron_thorns":
        _DECK = iron_thorns_counter_deck()
        return _DECK
    for path in (HERE / "deck.csv", Path("deck.csv"), Path("/kaggle_simulations/agent/deck.csv")):
        if path.exists():
            _DECK = [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()][:60]
            return _DECK
    _DECK = lucario_deck()
    return _DECK


def build_registry() -> dict[int, CardFeature]:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY

    registry: dict[int, CardFeature] = {}
    try:
        for card in all_card_data():
            tags: set[str] = set()
            name = card.name or ""
            name_lower = name.lower()
            if getattr(card, "ex", False):
                tags.add("multi_prize")
            if getattr(card, "megaEx", False):
                tags.add("mega")
            if getattr(card, "skills", None):
                skill_text = " ".join(f"{s.name} {s.text}" for s in card.skills).lower()
                if "draw" in skill_text:
                    tags.add("draw")
                if "search" in skill_text:
                    tags.add("search")
            if "boss" in name_lower or "catcher" in name_lower:
                tags.add("gust")
            if "energy" in name_lower:
                tags.add("energy")
            if getattr(card, "hp", 0) and card.hp <= 70 and getattr(card, "basic", False):
                tags.add("poffin_target")
            registry[card.cardId] = CardFeature(
                card_id=card.cardId,
                name=name,
                card_type=getattr(getattr(card, "cardType", ""), "name", ""),
                stage_or_type="",
                hp=getattr(card, "hp", 0) or 0,
                rule="",
                tags=tuple(sorted(tags)),
            )
    except Exception:
        registry = {}

    _REGISTRY = registry
    return registry


def load_imitation_profile() -> dict:
    global _IMITATION_PROFILE
    if _IMITATION_PROFILE is not None:
        return _IMITATION_PROFILE
    if os.environ.get("POKEMAYNE_USE_IMITATION", "0") != "1":
        _IMITATION_PROFILE = {}
        return _IMITATION_PROFILE
    for path in (HERE / "imitation_profile.json", Path("imitation_profile.json"), Path("/kaggle_simulations/agent/imitation_profile.json")):
        if path.exists():
            try:
                _IMITATION_PROFILE = json.loads(path.read_text(encoding="utf-8"))
                return _IMITATION_PROFILE
            except Exception:
                break
    _IMITATION_PROFILE = {}
    return _IMITATION_PROFILE


def legal_fallback(obs) -> list[int]:
    select = obs.select
    if select is None:
        return read_deck_csv()
    options = list(select.option or [])
    max_count = int(select.maxCount or 0)
    min_count = int(select.minCount or 0)
    count = max(min_count, max_count)
    return list(range(min(count, len(options))))


def card_state(card) -> tuple[int | None, int | None]:
    return (safe_getattr(card, "id"), safe_getattr(card, "hp"))


def player_board_signature(player) -> tuple:
    active = tuple(card_state(card) for card in (safe_getattr(player, "active", []) or []))
    bench = tuple(card_state(card) for card in (safe_getattr(player, "bench", []) or []))
    return (
        int(safe_getattr(player, "handCount", 0) or 0),
        active,
        bench,
    )


def prize_pair_signature(obs) -> tuple[int, int]:
    state = safe_getattr(obs, "current")
    players = safe_getattr(state, "players", []) if state is not None else []
    if len(players) < 2:
        return (6, 6)
    return (
        len(safe_getattr(players[0], "prize", []) or []),
        len(safe_getattr(players[1], "prize", []) or []),
    )


def board_signature(obs) -> tuple:
    state = safe_getattr(obs, "current")
    players = safe_getattr(state, "players", []) if state is not None else []
    if len(players) < 2:
        return ()
    your_index = int(safe_getattr(state, "yourIndex", 0) or 0)
    opponent_index = 1 - your_index
    return (
        player_board_signature(players[your_index]),
        player_board_signature(players[opponent_index]),
    )


def loop_guard() -> LoopGuard:
    global _LOOP_GUARD
    if _LOOP_GUARD is None:
        _LOOP_GUARD = LoopGuard()
    return _LOOP_GUARD


def force_attack_choice(obs) -> list[int] | None:
    """Break repeated non-progress loops by selecting a direct attack line."""
    select = safe_getattr(obs, "select")
    options = list(safe_getattr(select, "option", []) or [])
    if not options:
        return None
    for index, option in enumerate(options):
        if option_type_name(option) == "ATTACK":
            return [index]
    if context_value(obs) == 35:  # SelectContext.ATTACK
        return [0]
    return None


def verify_and_submit_action(choice: list[int], obs) -> list[int]:
    """Final safety gate: return only legal option indices for this prompt."""
    select = safe_getattr(obs, "select")
    if select is None:
        return read_deck_csv()
    options = list(safe_getattr(select, "option", []) or [])
    min_count = int(safe_getattr(select, "minCount", 0) or 0)
    max_count = int(safe_getattr(select, "maxCount", 0) or 0)
    if max_count <= 0 or not options:
        return []

    deduped: list[int] = []
    for index in choice or []:
        if isinstance(index, int) and 0 <= index < len(options) and index not in deduped:
            deduped.append(index)
    if min_count <= len(deduped) <= max_count:
        return deduped

    fallback = velocity_fallback(obs)
    legal_fallback_indices = [index for index in fallback if isinstance(index, int) and 0 <= index < len(options)]
    if min_count <= len(legal_fallback_indices) <= max_count:
        return legal_fallback_indices
    count = max(min_count, max_count)
    return list(range(min(count, len(options))))


def velocity_fallback(obs) -> list[int]:
    """Fast deterministic fallback used for errors or clock pressure."""
    select = obs.select
    if select is None:
        return read_deck_csv()
    options = list(select.option or [])
    max_count = int(select.maxCount or 0)
    min_count = int(select.minCount or 0)
    count = max(min_count, max_count)
    if count <= 0 or not options:
        return []

    priority = {
        "ATTACK": 100,
        "PLAY": 90,
        "EVOLVE": 80,
        "ATTACH": 70,
        "ABILITY": 60,
        "RETREAT": 40,
        "CARD": 30,
        "YES": 20,
        "NUMBER": 10,
        "END": -100,
    }
    ranked = sorted(
        range(len(options)),
        key=lambda index: priority.get(option_type_name(options[index]), 0),
        reverse=True,
    )
    return ranked[: min(count, len(ranked))]


def choose_going_second(obs) -> list[int] | None:
    """Prefer going second when the simulator asks whether to go first."""
    if context_value(obs) != 41:  # SelectContext.IS_FIRST
        return None
    options = list(obs.select.option or [])
    for index, option in enumerate(options):
        if option_type_name(option) == "NO":
            return [index]
    return None


def tracker() -> GameStateTracker:
    global _TRACKER
    if _TRACKER is None:
        _TRACKER = GameStateTracker(read_deck_csv())
    return _TRACKER


def agent(obs_dict: dict) -> list[int]:
    """Return legal option indices for the current CABT observation."""
    started = time.perf_counter()
    try:
        obs = to_observation_class(obs_dict)
        if obs.select is None:
            return read_deck_csv()
        if float(obs_dict.get("remainingOverageTime", 999.0) or 999.0) < 30.0:
            choice = verify_and_submit_action(velocity_fallback(obs), obs)
            log_decision("clock_fallback", {"phase": match_phase(obs), "choice": choice})
            return choice
        go_second_choice = choose_going_second(obs)
        if go_second_choice is not None:
            choice = verify_and_submit_action(go_second_choice, obs)
            log_decision("choose_second", {"choice": choice})
            return choice
        tracker().observe(obs)
        update_match_signals(obs)
        update_runtime_context(obs_dict)
        if loop_guard().observe(obs):
            attack_choice = force_attack_choice(obs)
            if attack_choice is not None:
                choice = verify_and_submit_action(attack_choice, obs)
                log_decision(
                    "loop_break_attack",
                    {"phase": match_phase(obs), "stable_turns": loop_guard().stable_turns, "choice": choice},
                )
                return choice
        deck = read_deck_csv()
        if is_alakazam_deck(deck):
            choice = choose_control_indices(obs, build_registry(), load_imitation_profile())
        elif is_dragapult_deck(deck) or is_ogerpon_wall_deck(deck) or is_iron_thorns_deck(deck):
            choice = choose_counter_indices(obs, deck, build_registry(), load_imitation_profile())
        else:
            choice = choose_indices(obs, build_registry(), load_imitation_profile())
        if time.perf_counter() - started > SOFT_DEADLINE_SECONDS:
            choice = verify_and_submit_action(velocity_fallback(obs), obs)
            log_decision("soft_deadline_fallback", {"phase": match_phase(obs), "choice": choice})
            return choice
        if choice:
            verified = verify_and_submit_action(choice, obs)
            log_decision(
                "policy_choice",
                {
                    "phase": match_phase(obs),
                    "choice": verified,
                    "exploit": execute_advanced_simulator_exploits(obs, build_registry()),
                    "hail_mary": evaluate_hail_mary_tactics(obs, build_registry()),
                    "anti_alakazam": check_anti_alakazam_overrides(obs, build_registry()),
                },
            )
            return verified
        choice = verify_and_submit_action(velocity_fallback(obs), obs)
        log_decision("empty_choice_fallback", {"phase": match_phase(obs), "choice": choice})
        return choice
    except Exception:
        try:
            obs = to_observation_class(obs_dict)
            return verify_and_submit_action(velocity_fallback(obs), obs)
        except Exception:
            return read_deck_csv()

