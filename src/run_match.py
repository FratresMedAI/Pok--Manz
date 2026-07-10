"""Run a local CABT match using kaggle-environments."""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-a", default="submission/main.py")
    parser.add_argument("--agent-b", default="vendor/cabt_sample_submission/main.py")
    parser.add_argument("--deck-a", default="submission/deck.csv")
    parser.add_argument("--deck-b", default="vendor/cabt_sample_submission/deck.csv")
    parser.add_argument("--html", default="artifacts/replays/latest.html")
    args = parser.parse_args()

    sys.path.insert(0, str(SDK_DIR))
    from kaggle_environments import make

    deck_a = read_deck(ROOT / args.deck_a)
    deck_b = read_deck(ROOT / args.deck_b)
    agent_a = with_deck(load_agent(ROOT / args.agent_a), deck_a)
    agent_b = with_deck(load_agent(ROOT / args.agent_b), deck_b)

    env = make("cabt", configuration={"decks": [deck_a, deck_b]})
    env.run([agent_a, agent_b])

    html_path = ROOT / args.html
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(env.render(mode="html"), encoding="utf-8")
    print(f"Match complete. Replay written to {html_path}")


if __name__ == "__main__":
    main()

