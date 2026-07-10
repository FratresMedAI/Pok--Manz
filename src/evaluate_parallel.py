"""Parallel CABT evaluation runner for CPU pods."""

from __future__ import annotations

import argparse
import importlib.util
import multiprocessing as mp
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SDK_DIR = ROOT / "vendor" / "cabt_sample_submission"
DEFAULT_WORKERS = 32

_AGENT_A: Any = None
_AGENT_B: Any = None
_DECK_A: list[int] = []
_DECK_B: list[int] = []


def load_agent(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load agent from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module.agent


def read_deck(path: Path) -> list[int]:
    return [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()][:60]


def with_deck(agent_func, deck: list[int], deck_mode: str | None = None):
    def wrapped(obs_dict):
        if deck_mode:
            os.environ["POKEMAYNE_DECK"] = deck_mode
        if obs_dict.get("select") is None:
            return deck
        return agent_func(obs_dict)

    return wrapped


def final_result(env) -> int | None:
    try:
        last = env.steps[-1]
        statuses = [getattr(step, "status", None) for step in last]
        if any(status == "ERROR" for status in statuses):
            return None
        rewards = [getattr(step, "reward", None) for step in last]
        if rewards[0] is not None and rewards[1] is not None:
            if rewards[0] > rewards[1]:
                return 0
            if rewards[1] > rewards[0]:
                return 1
            return 2
    except Exception:
        pass

    try:
        last = env.steps[-1][0]
        observation = last.observation
        current = observation.get("current") if isinstance(observation, dict) else None
        if current and current.get("result") in (0, 1, 2):
            return current.get("result")
    except Exception:
        return None
    return None


def init_worker(
    agent_a: str,
    agent_b: str,
    deck_a: str,
    deck_b: str,
    deck_mode_a: str,
    deck_mode_b: str,
) -> None:
    global _AGENT_A, _AGENT_B, _DECK_A, _DECK_B
    os.environ.setdefault("POKEMAYNE_TELEMETRY", "0")
    sys.path.insert(0, str(SDK_DIR))
    _DECK_A = read_deck(ROOT / deck_a)
    _DECK_B = read_deck(ROOT / deck_b)
    _AGENT_A = with_deck(load_agent(ROOT / agent_a), _DECK_A, deck_mode_a)
    _AGENT_B = with_deck(load_agent(ROOT / agent_b), _DECK_B, deck_mode_b)


def termination_info(env) -> tuple[str, bool]:
    """Return (tag, opponent_timed_out). opponent is player index 1 (deck B)."""
    try:
        last = env.steps[-1]
        for player_index, step in enumerate(last):
            status = str(getattr(step, "status", "") or "").upper()
            info = getattr(step, "info", None)
            info_blob = str(info).upper() if info is not None else ""
            blob = f"{status} {info_blob}"
            if any(token in blob for token in ("TIMEOUT", "DISQUAL", "OVERAGE")):
                return (f"TIMEOUT_P{player_index}", player_index == 1)
    except Exception:
        pass
    return ("NORMAL", False)


def run_game(game_index: int) -> tuple[int, int | None, str | None, int, str, bool]:
    try:
        from kaggle_environments import make

        env = make("cabt", configuration={"decks": [_DECK_A, _DECK_B]})
        env.run([_AGENT_A, _AGENT_B])
        turns = len(getattr(env, "steps", []) or [])
        result = final_result(env)
        term_tag, opponent_timeout = termination_info(env)
        return (game_index, result, None, turns, term_tag, opponent_timeout)
    except Exception as exc:
        return (game_index, None, str(exc), 0, "ERROR", False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=310)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--agent-a", default="submission/main.py")
    parser.add_argument("--agent-b", default="vendor/cabt_sample_submission/main.py")
    parser.add_argument("--deck-a", default="submission/deck.csv")
    parser.add_argument("--deck-b", default="vendor/cabt_sample_submission/deck.csv")
    parser.add_argument("--deck-mode-a", default="lucario")
    parser.add_argument("--deck-mode-b", default="baseline")
    args = parser.parse_args()

    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    workers = max(1, min(args.workers, DEFAULT_WORKERS))
    wins = losses = draws = errors = 0
    loss_turns: list[int] = []
    error_samples: list[str] = []
    opponent_timeout_wins = 0
    timeout_tags: dict[str, int] = {}
    with mp.Pool(
        processes=workers,
        maxtasksperchild=8,
        initializer=init_worker,
        initargs=(
            args.agent_a,
            args.agent_b,
            args.deck_a,
            args.deck_b,
            args.deck_mode_a,
            args.deck_mode_b,
        ),
    ) as pool:
        for game_index, result, error, turns, term_tag, opponent_timeout in pool.imap_unordered(
            run_game, range(1, args.games + 1)
        ):
            timeout_tags[term_tag] = timeout_tags.get(term_tag, 0) + 1
            if result == 0:
                wins += 1
                if opponent_timeout:
                    opponent_timeout_wins += 1
            elif result == 1:
                losses += 1
                if turns:
                    loss_turns.append(turns)
            elif result == 2:
                draws += 1
            else:
                errors += 1
                if error and len(error_samples) < 5:
                    error_samples.append(error[:200])
            if error:
                print(f"game={game_index} error={error}", flush=True)
            else:
                print(
                    f"game={game_index} result={result} turns={turns} term={term_tag}",
                    flush=True,
                )

    total = max(1, args.games)
    avg_loss_turns = (sum(loss_turns) / len(loss_turns)) if loss_turns else 0.0
    print(
        f"workers={workers} wins={wins} losses={losses} draws={draws} errors={errors} "
        f"win_rate={wins / total:.3f} avg_loss_turns={avg_loss_turns:.1f} "
        f"opponent_timeout_wins={opponent_timeout_wins}",
        flush=True,
    )
    print(f"termination_tags={timeout_tags}", flush=True)
    if error_samples:
        print(f"error_samples={error_samples}", flush=True)


if __name__ == "__main__":
    main()
