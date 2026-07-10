"""Early opponent archetype classification."""

from __future__ import annotations

from dataclasses import dataclass

from .cards import CardFeature, normalize_name


@dataclass(frozen=True)
class ArchetypeRead:
    name: str
    confidence: float
    tags: tuple[str, ...]


ARCHETYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "alakazam_control": ("abra", "kadabra", "alakazam", "dunsparce", "dudunsparce"),
    "crustle_wall": ("dwebble", "crustle"),
    "dragapult": ("dreepy", "drakloak", "dragapult"),
    "ogerpon_toolbox": ("teal mask ogerpon", "ogerpon", "raging bolt"),
    "lucario": ("riolu", "lucario", "solrock", "lunatone"),
    "starmie": ("staryu", "starmie"),
    "noctowl_shell": ("hoothoot", "noctowl", "fan rotom"),
    "rogue_box": ("kangaskhan", "clefairy", "mewtwo", "absol"),
}

ARCHETYPE_TAGS: dict[str, tuple[str, ...]] = {
    "alakazam_control": ("psychic_control", "target_engine_basics", "hammer_special_energy", "limit_bench"),
    "crustle_wall": ("ex_damage_wall", "prefer_non_ex_attacker", "avoid_ex_into_crustle"),
    "dragapult": ("bench_damage", "avoid_low_hp_bench", "stage2_clock"),
    "ogerpon_toolbox": ("energy_acceleration", "track_energy_types", "gust_engine"),
    "lucario": ("fighting_pressure", "mega_ex", "high_damage"),
    "starmie": ("spread_pressure", "fast_attacker"),
    "noctowl_shell": ("search_engine", "setup_shell"),
    "rogue_box": ("unknown_attackers", "dynamic_thresholds"),
    "unknown": ("fallback",),
}


def classify_from_names(names: list[str]) -> ArchetypeRead:
    normalized = [normalize_name(name) for name in names if name]
    scores: dict[str, int] = {}
    for archetype, keywords in ARCHETYPE_KEYWORDS.items():
        score = 0
        for card_name in normalized:
            if any(keyword in card_name for keyword in keywords):
                score += 1
        if score:
            scores[archetype] = score

    if not scores:
        return ArchetypeRead("unknown", 0.0, ARCHETYPE_TAGS["unknown"])

    best_name, best_score = max(scores.items(), key=lambda item: item[1])
    confidence = min(1.0, best_score / max(2, len(normalized)))
    return ArchetypeRead(best_name, confidence, ARCHETYPE_TAGS[best_name])


def classify_from_card_ids(card_ids: list[int], registry: dict[int, CardFeature]) -> ArchetypeRead:
    names = [registry[card_id].name for card_id in card_ids if card_id in registry]
    return classify_from_names(names)


def tempo_clock_for_name(name: str) -> int:
    """Estimate turns before a visible setup piece becomes a live threat."""
    norm = normalize_name(name)
    if "dreepy" in norm:
        return 2
    if "drakloak" in norm:
        return 1
    if "dragapult" in norm:
        return 0
    if "riolu" in norm:
        return 1
    if "hoothoot" in norm:
        return 1
    return 1

