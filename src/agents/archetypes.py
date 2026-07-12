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
    "crustle_wall": ("dwebble", "crustle", "kangaskhan", "jumbo ice cream"),
    "rocket_spidops": (
        "team rocket's tarountula",
        "team rocket's spidops",
        "team rocket's transceiver",
        "team rocket's ariana",
        "team rocket's proton",
    ),
    "dragapult": ("dreepy", "drakloak", "dragapult"),
    "ogerpon_toolbox": ("teal mask ogerpon", "ogerpon", "raging bolt"),
    "lucario": ("riolu", "lucario", "solrock", "lunatone"),
    "starmie": ("staryu", "starmie", "snorunt", "froslass"),
    "noctowl_shell": ("hoothoot", "noctowl", "fan rotom"),
    "rogue_box": ("kangaskhan", "clefairy", "mewtwo", "absol"),
    "abomasnow": ("snover", "abomasnow", "kyogre"),
    "walrein_lock": ("spheal", "walrein", "crushing hammer"),
    "archaludon_metal": ("archaludon", "duraludon"),
    "ethan_fire": ("ethan's cyndaquil", "ethan's typhlosion", "ethan's adventure"),
    "mega_poison": ("mega absol", "okidogi", "munkidori", "fezandipiti", "impidimp", "spikemuth"),
    "zacian_box": ("zacian", "cyrano", "waitress"),
    "xerneas_box": ("xerneas", "smoochum"),
    "cynthia_box": ("cynthia's gible", "cynthia's gabite", "cynthia's garchomp"),
}

ARCHETYPE_TAGS: dict[str, tuple[str, ...]] = {
    "alakazam_control": ("psychic_control", "target_engine_basics", "hammer_special_energy", "limit_bench"),
    "crustle_wall": ("ex_damage_wall", "prefer_non_ex_attacker", "avoid_ex_into_crustle", "energy_acceleration"),
    "rocket_spidops": ("disruption", "gust_engine", "setup_shell", "poison_pressure"),
    "dragapult": ("bench_damage", "avoid_low_hp_bench", "stage2_clock"),
    "ogerpon_toolbox": ("energy_acceleration", "track_energy_types", "gust_engine"),
    "lucario": ("fighting_pressure", "mega_ex", "high_damage"),
    "starmie": ("spread_pressure", "fast_attacker"),
    "noctowl_shell": ("search_engine", "setup_shell"),
    "rogue_box": ("unknown_attackers", "dynamic_thresholds"),
    "abomasnow": ("slow_pressure", "hammer_special_energy", "high_hp"),
    "walrein_lock": ("item_lock", "energy_denial", "slow_pressure"),
    "archaludon_metal": ("metal_wall", "high_hp", "energy_acceleration"),
    "ethan_fire": ("rush_pressure", "stage2_clock"),
    "mega_poison": ("poison_pressure", "disruption", "mega_ex"),
    "zacian_box": ("fast_attacker", "mega_ex", "gust_engine"),
    "xerneas_box": ("fast_attacker", "energy_acceleration", "gust_engine"),
    "cynthia_box": ("stage2_clock", "high_damage", "setup_shell"),
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

    # Dunsparce appears in several shells. Do not call it Alakazam control
    # unless the Abra/Kadabra/Alakazam line is actually visible.
    if "alakazam_control" in scores:
        has_psychic_line = any(
            "abra" in card_name or "kadabra" in card_name or "alakazam" in card_name
            for card_name in normalized
        )
        if not has_psychic_line:
            scores.pop("alakazam_control", None)
            if not scores:
                return ArchetypeRead("unknown", 0.0, ARCHETYPE_TAGS["unknown"])

    if "crustle_wall" in scores:
        has_crustle_line = any("dwebble" in card_name or "crustle" in card_name for card_name in normalized)
        if not has_crustle_line:
            scores.pop("crustle_wall", None)

    if "rogue_box" in scores:
        has_rogue_core = any(
            "clefairy" in card_name or "mewtwo" in card_name or "absol" in card_name
            for card_name in normalized
        )
        if not has_rogue_core:
            scores.pop("rogue_box", None)

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

