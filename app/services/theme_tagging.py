"""
theme_tagging.py
----------------
Ultra-lean utility for tagging prose with high-level narrative themes.
Designed for large-scale text pipelines: no heavyweight NLP, just
lower-casing, regex tokenization, and constant-time set membership.
"""

import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# ────────────────────────────────────────────────────────────────────────────────
# 1. Theme → keyword mapping
#       • Keep sets small; expand via corpus-driven stats when needed.
#       • ALL TERMS MUST BE LOWERCASE.
# ────────────────────────────────────────────────────────────────────────────────
THEME_KEYWORDS: Dict[str, Set[str]] = {
    "love_romance": {
        "love", "passion", "desire", "courtship", "heart",
        "affection", "soulmate", "devotion"
    },
    "conflict_war": {
        "battle", "siege", "rebellion", "enemy", "clash",
        "troops", "victory", "defeat"
    },
    "betrayal_deceit": {
        "treachery", "conspiracy", "secret", "double-cross",
        "lie", "spy", "backstab"
    },
    "coming_of_age": {
        "adolescence", "growth", "rite", "mentor", "trial",
        "discovery", "maturity"
    },
    "quest_journey": {
        "voyage", "pilgrimage", "odyssey", "road", "expedition",
        "map", "destination", "guide"
    },
    "survival_endurance": {
        "struggle", "starvation", "shelter", "wilderness",
        "escape", "resilience", "peril"
    },
    "identity_self_discovery": {
        "mask", "reflection", "heritage", "transformation",
        "purpose", "inner", "voice"
    },
    "power_ambition": {
        "throne", "crown", "dominance", "conquest",
        "empire", "influence", "authority"
    },
    "justice_revenge": {
        "judgment", "trial", "retribution", "vengeance",
        "reckoning", "debt", "atonement"
    },
    "loss_grief": {
        "mourning", "funeral", "tomb", "absence", "widow",
        "sorrow", "memory"
    },
    "redemption_forgiveness": {
        "penance", "absolution", "salvation", "repent",
        "mercy", "clean", "slate"
    },
    "good_vs_evil": {
        "virtue", "corruption", "temptation", "sin",
        "righteousness", "sacrifice"
    },
    "chaos_apocalypse": {
        "plague", "cataclysm", "ruin", "collapse",
        "extinction", "doom", "aftermath"
    },
    "hope_renewal": {
        "dawn", "rebirth", "seed", "phoenix",
        "resurgence", "healing", "promise"
    },
    # Additional narrative elements specific to common plot points
    "social_ceremony": {
        "wedding", "ceremony", "witness", "church", "marriage",
        "bride", "groom", "celebration", "vow", "officiate"
    },
    "investigation": {
        "detective", "clue", "mystery", "evidence", "witness",
        "crime", "suspect", "investigate", "puzzle", "case"
    }
}

# pre-compiled token regex (letters and apostrophes)
_TOKEN_RE = re.compile(r"[A-Za-z']+")


# ────────────────────────────────────────────────────────────────────────────────
# 2. Public API
# ────────────────────────────────────────────────────────────────────────────────
def tokenize(text: str) -> List[str]:
    """Lower-case and split into alpha tokens."""
    return _TOKEN_RE.findall(text.lower())


def tag_themes(text: str) -> Dict[str, List[str]]:
    """
    Return a mapping {theme: [trigger_words]} for every theme
    that appears at least once in *text*.

    Example
    -------
    >>> tag_themes("Love and battle in the shadow of the throne.")
    {'love_romance': ['love'],
     'conflict_war': ['battle'],
     'power_ambition': ['throne']}
    """
    tokens = set(tokenize(text))
    hits: Dict[str, List[str]] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        overlap = tokens & keywords
        if overlap:
            hits[theme] = sorted(overlap)
    return hits


def analyze_query(query: str) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Helper function to analyze a query for themes and narrative elements.
    Returns both the theme mapping and a list of narrative keywords found.

    Example
    -------
    >>> analyze_query("Tell me about the protagonist being a witness at a wedding")
    ({'social_ceremony': ['wedding', 'witness']}, ['witness', 'wedding'])
    """
    themes = tag_themes(query)

    # Check for specific narrative elements
    narrative_elements = ["witness", "wedding", "church", "bride", "ceremony",
                         "investigation", "detective", "evidence", "crime"]

    query_lower = query.lower()
    found_elements = [elem for elem in narrative_elements if elem in query_lower]

    return themes, found_elements


def simulate_theme_boost(query: str, document: str) -> float:
    """
    Simulate the theme-based boosting for a query and document pair.
    Returns the calculated boost factor.

    Example
    -------
    >>> simulate_theme_boost(
    ...     "Tell me about the protagonist being a witness at a wedding",
    ...     "The protagonist stood at the church as a witness to the wedding ceremony."
    ... )
    1.05  # Example boost value
    """
    # Extract themes from query and document
    query_themes = tag_themes(query)
    doc_themes = tag_themes(document)

    if not query_themes or not doc_themes:
        return 0.0

    # Calculate theme overlap
    theme_overlap = set(query_themes.keys()) & set(doc_themes.keys())

    # Calculate keyword overlap within matching themes
    keyword_overlap_count = 0

    for theme in theme_overlap:
        query_keywords = set(query_themes[theme])
        doc_keywords = set(doc_themes[theme])
        keyword_overlap = query_keywords & doc_keywords
        keyword_overlap_count += len(keyword_overlap)

    # Check for narrative elements
    narrative_elements = ["witness", "wedding", "church", "bride", "ceremony", "chapel"]
    query_lower = query.lower()
    doc_lower = document.lower()
    narrative_matches = sum(1 for elem in narrative_elements if elem in doc_lower and elem in query_lower)

    # Calculate boost components (using typical values)
    theme_boost = 0.2 * len(theme_overlap)
    keyword_boost = 0.15 * keyword_overlap_count
    narrative_boost = 0.5 * narrative_matches

    # Calculate total boost
    total_boost = theme_boost + keyword_boost + narrative_boost

    return total_boost


# ────────────────────────────────────────────────────────────────────────────────
# 3. Quick-and-dirty smoke test
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = (
        "Amid the ruins of empire, a young widow embarks on a pilgrimage. "
        "Her heart still aches with love, yet vengeance whispers louder."
    )
    print(tag_themes(sample))

    # Test the narrative query
    narrative_query = "Tell me about the protagonist being a witness at a wedding"
    narrative_doc = "The protagonist stood at the church as a witness to the wedding ceremony in the chapel."

    print("\nQuery Theme Analysis:")
    themes, elements = analyze_query(narrative_query)
    print(f"Themes: {themes}")
    print(f"Narrative elements: {elements}")

    print("\nDocument Theme Analysis:")
    print(tag_themes(narrative_doc))

    print("\nSimulated Boost:")
    boost = simulate_theme_boost(narrative_query, narrative_doc)
    print(f"Boost factor: {boost:.2f} ({boost*100:.0f}% increase in score)")