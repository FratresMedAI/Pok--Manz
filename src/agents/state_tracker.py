"""Lightweight hidden-information tracker for CABT observations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


def card_id(card: Any) -> int | None:
    if card is None:
        return None
    return getattr(card, "id", None)


def ids_from_cards(cards: list[Any] | None) -> list[int]:
    if not cards:
        return []
    return [cid for cid in (card_id(card) for card in cards) if cid is not None]


@dataclass
class GameStateTracker:
    """Tracks our known deck/prize state across a single match."""

    master_deck: list[int]
    known_prizes: Counter[int] = field(default_factory=Counter)
    last_deck_count: int = 60
    saw_deck_search: bool = False

    def __post_init__(self) -> None:
        self.master_counts = Counter(self.master_deck)

    def observe(self, obs: Any) -> None:
        current = getattr(obs, "current", None)
        if current is None:
            return
        your_index = getattr(current, "yourIndex", 0)
        player = current.players[your_index]
        self.last_deck_count = getattr(player, "deckCount", self.last_deck_count)

        select = getattr(obs, "select", None)
        exposed_deck = getattr(select, "deck", None) if select is not None else None
        if exposed_deck:
            self.saw_deck_search = True
            self.known_prizes = self.deduce_prizes(obs, ids_from_cards(exposed_deck))

    def deduce_prizes(self, obs: Any, exposed_deck_ids: list[int]) -> Counter[int]:
        current = obs.current
        your_index = current.yourIndex
        player = current.players[your_index]
        known = Counter(exposed_deck_ids)
        known.update(ids_from_cards(player.hand))
        known.update(ids_from_cards(player.discard))
        known.update(ids_from_cards(player.active))
        known.update(ids_from_cards(player.bench))
        known.update(ids_from_cards(current.stadium))

        hidden = Counter()
        for card, count in self.master_counts.items():
            remaining = count - known.get(card, 0)
            if remaining > 0:
                hidden[card] = remaining
        return hidden

    def prized_count(self, card_id_value: int) -> int:
        return self.known_prizes.get(card_id_value, 0)

    def deck_density(self, important_cards: set[int]) -> float:
        if self.last_deck_count <= 0:
            return 0.0
        available = 0
        for card in important_cards:
            available += max(0, self.master_counts.get(card, 0) - self.known_prizes.get(card, 0))
        return min(1.0, available / self.last_deck_count)

