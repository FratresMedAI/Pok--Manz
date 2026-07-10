"""Small card/deck helpers shared by local tooling and agents."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CardFeature:
    card_id: int
    name: str
    card_type: str = ""
    stage_or_type: str = ""
    hp: int = 0
    rule: str = ""
    category: str = ""
    weakness: str = ""
    resistance: str = ""
    retreat: int = 0
    tags: tuple[str, ...] = field(default_factory=tuple)


def parse_int(value: str | None, default: int = 0) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def normalize_name(name: str) -> str:
    return " ".join(name.lower().replace("'", "").replace("`", "").split())


def load_card_csv(path: str | Path) -> dict[int, CardFeature]:
    cards: dict[int, CardFeature] = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            card_id = parse_int(row.get("Card ID"))
            if not card_id:
                continue
            name = row.get("Card Name", "")
            rule = row.get("Rule", "") or ""
            stage_or_type = row.get("Stage (Pokemon)/Type (Energy and Trainer)", "")
            card_type = row.get("Category", "") or stage_or_type
            hp = parse_int(row.get("HP"))
            tags = infer_tags(name, rule, card_type, stage_or_type, hp, row.get("Effect Explanation", "") or "")
            cards[card_id] = CardFeature(
                card_id=card_id,
                name=name,
                card_type=card_type,
                stage_or_type=stage_or_type,
                hp=hp,
                rule=rule,
                category=row.get("Category", "") or "",
                weakness=row.get("Weakness", "") or "",
                resistance=row.get("Resistance (Type)", "") or "",
                retreat=parse_int(row.get("Retreat")),
                tags=tuple(sorted(tags)),
            )
    return cards


def infer_tags(name: str, rule: str, card_type: str, stage_or_type: str, hp: int, text: str) -> set[str]:
    text_blob = f"{name} {rule} {card_type} {stage_or_type} {text}".lower()
    tags: set[str] = set()
    if "ex" in text_blob:
        tags.add("multi_prize")
    if "mega" in text_blob:
        tags.add("mega")
    if "draw" in text_blob:
        tags.add("draw")
    if "search your deck" in text_blob or "search" in text_blob:
        tags.add("search")
    if "switch" in text_blob or "active" in text_blob and "bench" in text_blob:
        tags.add("switch")
    if "boss" in text_blob or "catcher" in text_blob:
        tags.add("gust")
    if "energy" in text_blob:
        tags.add("energy")
    if hp and hp <= 70 and "pokemon" in card_type.lower():
        tags.add("poffin_target")
    return tags


def count_cards(deck: list[int]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for card_id in deck:
        counts[card_id] = counts.get(card_id, 0) + 1
    return counts


def lucario_deck() -> list[int]:
    """Deck from the public Mega Lucario ex rule-based notebook."""
    return (
        [673] * 2
        + [674] * 2
        + [675] * 2
        + [676] * 3
        + [677] * 3
        + [678] * 4
        + [1102] * 4
        + [1123] * 2
        + [1141] * 4
        + [1142] * 4
        + [1152] * 4
        + [1159]
        + [1182] * 2
        + [1192] * 4
        + [1227] * 4
        + [1252] * 2
        + [6] * 13
    )


def alakazam_control_deck() -> list[int]:
    """Alakazam/Dunsparce control deck mined from top replay batch."""
    return (
        [5] * 2
        + [13]
        + [19] * 4
        + [66] * 2
        + [140]
        + [305] * 3
        + [343]
        + [741] * 4
        + [742] * 4
        + [743] * 4
        + [1079] * 3
        + [1081] * 3
        + [1086] * 4
        + [1097]
        + [1129]
        + [1152] * 4
        + [1182] * 3
        + [1184]
        + [1197] * 3
        + [1225] * 4
        + [1231] * 4
        + [1266] * 3
    )




def ogerpon_wall_deck() -> list[int]:
    """Cornerstone Mask Ogerpon immunity wall using legal CABT card IDs."""
    return (
        [117] * 3
        + [96] * 3
        + [677] * 2
        + [140]
        + [1081] * 2
        + [1116] * 3
        + [1088]
        + [1264] * 2
        + [1121] * 4
        + [1152] * 4
        + [1182] * 3
        + [1225] * 4
        + [1231] * 2
        + [1198] * 2
        + [1097] * 2
        + [1087]
        + [1197]
        + [11] * 2
        + [6] * 12
        + [1] * 6
    )


def iron_thorns_counter_deck() -> list[int]:
    """Quad Iron Thorns ability-lock list with zero-bench pilot support."""
    return (
        [37] * 4
        + [1121] * 4
        + [1079] * 2
        + [1088]
        + [1182] * 2
        + [1225] * 3
        + [1198] * 2
        + [1097] * 2
        + [1087] * 2
        + [1197] * 2
        + [1152] * 2
        + [11] * 2
        + [4] * 28
        + [6] * 4
    )


def dragapult_snipe_deck() -> list[int]:
    """Bench-sniping Dragapult with gust-trap and poison checkup tech."""
    return (
        [119] * 4
        + [120] * 4
        + [121] * 3
        + [986] * 2
        + [112]
        + [1086] * 3
        + [1121] * 4
        + [1079] * 3
        + [1088]
        + [1182] * 3
        + [1124] * 2
        + [1225] * 4
        + [1231]
        + [1198] * 2
        + [1097]
        + [1152] * 3
        + [1087] * 2
        + [1197] * 2
        + [11] * 2
        + [2] * 3
        + [5] * 10
    )


def write_deck_csv(deck: list[int], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(str(card_id) for card_id in deck) + "\n", encoding="utf-8")
    return target

