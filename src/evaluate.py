"""Repeated local evaluation for CABT agents."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SDK_DIR = ROOT / "vendor" / "cabt_sample_submission"


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


def with_deck(agent_func, deck: list[int]):
    def wrapped(obs_dict):
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--agent-a", default="submission/main.py")
    parser.add_argument("--agent-b", default="vendor/cabt_sample_submission/main.py")
    parser.add_argument("--deck-a", default="submission/deck.csv")
    parser.add_argument("--deck-b", default="vendor/cabt_sample_submission/deck.csv")
    args = parser.parse_args()

    sys.path.insert(0, str(SDK_DIR))
    from kaggle_environments import make

    deck_a = read_deck(ROOT / args.deck_a)
    deck_b = read_deck(ROOT / args.deck_b)
    agent_a = with_deck(load_agent(ROOT / args.agent_a), deck_a)
    agent_b = with_deck(load_agent(ROOT / args.agent_b), deck_b)

    wins = losses = draws = errors = 0
    for game_index in range(args.games):
        try:
            env = make("cabt", configuration={"decks": [deck_a, deck_b]})
            env.run([agent_a, agent_b])
            result = final_result(env)
            if result == 0:
                wins += 1
            elif result == 1:
                losses += 1
            elif result == 2:
                draws += 1
            else:
                errors += 1
            print(f"game={game_index + 1} result={result}")
        except Exception as exc:
            errors += 1
            print(f"game={game_index + 1} error={exc}")

    total = max(1, args.games)
    print(
        f"wins={wins} losses={losses} draws={draws} errors={errors} "
        f"win_rate={wins / total:.3f}"
    )


if __name__ == "__main__":
    main()

