"""
Utility functions for sorting cards by various criteria.

This module provides a flexible sorting system for Redemption card data,
allowing for customizable sort orders based on alignment, brigade, name, and other attributes.
"""

import re
from typing import Any, Dict, List, Tuple, Union


# Sort field extractors
def _get_alignment_priority(card_data: Dict[str, Any]) -> int:
    """Get sorting priority for card alignment (Good > Evil > Neutral)."""
    alignment_order = {"Good": 0, "Evil": 1, "Neutral": 2}
    return alignment_order.get(card_data.get("alignment"), 3)


def _get_brigade(card_data: Dict[str, Any]) -> str:
    """Get brigade for alphabetical sorting."""
    return card_data.get("raw_brigade", "")


def _get_type(card_data: Dict[str, Any]) -> str:
    """Get card type for sorting."""
    return card_data.get("type", "")


def _get_name(card_name: str) -> str:
    """Get card name for alphabetical sorting."""
    return card_name.lower()


# Field mapping for sort criteria
SORT_FIELDS = {
    "alignment": _get_alignment_priority,
    "brigade": _get_brigade,
    "type": _get_type,
    "name": lambda card_data: None,  # Special case handled in sort_cards
}


# ---------------------------------------------------------------------------
# "default" sort order (canonical spec)
# ---------------------------------------------------------------------------

_GOOD_SIDE_TYPES = {"hero", "ge", "good enhancement"}
_EVIL_SIDE_TYPES = {"evil character", "ee", "evil enhancement"}
_GOOD_CHARACTER_TYPES = {"hero"}
_EVIL_CHARACTER_TYPES = {"evil character"}

# Alphabetical-by-color brigade orders ("Gold" = the alignment's Gold brigade).
_GOOD_BRIGADE_ORDER = [
    "blue", "clay", "gold", "green", "multi",
    "purple", "red", "silver", "teal", "white",
]
_EVIL_BRIGADE_ORDER = [
    "black", "brown", "crimson", "gold",
    "gray", "multi", "orange", "pale green",
]

# Brigade tokens that belong to exactly one alignment (for dual detection).
_GOOD_ONLY_BRIGADES = {
    "blue", "clay", "green", "purple", "red",
    "silver", "teal", "white", "good gold", "goodgold",
}
_EVIL_ONLY_BRIGADES = {
    "black", "brown", "crimson", "gray",
    "orange", "pale green", "evil gold", "evilgold",
}

# Biblical book order (as book names appear in card data, Roman numerals).
_BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "I Samuel", "II Samuel", "I Kings", "II Kings",
    "I Chronicles", "II Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "I Corinthians", "II Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "I Thessalonians", "II Thessalonians",
    "I Timothy", "II Timothy", "Titus", "Philemon", "Hebrews", "James",
    "I Peter", "II Peter", "I John", "II John", "III John", "Jude",
    "Revelation",
]
# (lowercased prefix, index), longest prefixes first so "II Kings" beats
# "I Kings" and "I/II/III John" beat "John". "Psalm" accepted for Psalms.
_BOOK_PREFIXES = sorted(
    [(book.lower(), i) for i, book in enumerate(_BIBLE_BOOKS)]
    + [("psalm", _BIBLE_BOOKS.index("Psalms"))],
    key=lambda pair: len(pair[0]),
    reverse=True,
)

_PAREN_PATTERN = re.compile(r"\([^)]*\)")
_INT_PATTERN = re.compile(r"-?\d+")
_CHAPTER_VERSE_PATTERN = re.compile(r"(\d+)\s*:\s*(\d+)")

# Section ranks
_SEC_DOMINANT = 0
_SEC_ARTIFACT = 1
_SEC_COVENANT = 2
_SEC_CURSE = 3
_SEC_FORTRESS = 4
_SEC_SITE = 5
_SEC_LOST_SOUL = 6
_SEC_DUAL = 7
_SEC_GOOD = 8
_SEC_EVIL = 9
_SEC_MISC = 10

_FIRST_PART_SECTIONS = {
    "dominant": _SEC_DOMINANT,
    "artifact": _SEC_ARTIFACT,
    "covenant": _SEC_COVENANT,
    "curse": _SEC_CURSE,
    "fortress": _SEC_FORTRESS,
    "city": _SEC_FORTRESS,
    "site": _SEC_SITE,
    "lost soul": _SEC_LOST_SOUL,
}


def _type_parts(type_str: str) -> List[str]:
    """Split a raw type string on '/', trimming each part (handles 'Fortress / Evil Character')."""
    return [part.strip().lower() for part in (type_str or "").split("/")]


def _raw_brigade(card_data: Dict[str, Any]) -> str:
    """Original brigade string; falls back to 'brigade' (joining a normalized list)."""
    raw = card_data.get("raw_brigade")
    if raw is None:
        raw = card_data.get("brigade", "")
    if isinstance(raw, list):
        raw = "/".join(raw)
    return raw or ""


def _strip_parens(brigade: str) -> str:
    """Remove parenthesized segments; if that empties the string, use the paren content."""
    remainder = _PAREN_PATTERN.sub("", brigade).strip().strip("/").strip()
    if not remainder:
        paren_content = re.findall(r"\(([^)]*)\)", brigade)
        remainder = "/".join(part.strip() for part in paren_content).strip()
    return remainder


def _brigade_tokens(brigade: str) -> List[str]:
    """All individual brigade tokens (paren segments stripped, ' and ' treated as a separator)."""
    remainder = _strip_parens(brigade)
    remainder = remainder.replace(" and ", "/")
    return [token.strip().lower() for token in remainder.split("/") if token.strip()]


def _is_dual(card_data: Dict[str, Any]) -> bool:
    """Card spans good AND evil via its type parts or its brigades."""
    parts = _type_parts(card_data.get("type", ""))
    has_good = any(part in _GOOD_SIDE_TYPES for part in parts)
    has_evil = any(part in _EVIL_SIDE_TYPES for part in parts)
    if has_good and has_evil:
        return True
    if not (has_good or has_evil):
        return False
    brigade = _strip_parens(_raw_brigade(card_data))
    if " and " in brigade:
        return True
    tokens = _brigade_tokens(_raw_brigade(card_data))
    return any(t in _GOOD_ONLY_BRIGADES for t in tokens) and any(
        t in _EVIL_ONLY_BRIGADES for t in tokens
    )


def _primary_brigade_rank(card_data: Dict[str, Any], is_good_section: bool) -> Tuple[int, str]:
    """
    (rank, tiebreak) of the card's primary brigade within its section's brigade
    order. Unknown/empty brigades rank after all known ones, tie-broken by the
    raw brigade string.
    """
    raw = _raw_brigade(card_data)
    order = _GOOD_BRIGADE_ORDER if is_good_section else _EVIL_BRIGADE_ORDER
    unknown = (len(order), raw.lower())

    tokens = _brigade_tokens(raw)
    if not tokens:
        return unknown
    primary = tokens[0]

    # Normalize Gold variants to the "gold" bucket of the matching alignment.
    if primary in ("good gold", "goodgold"):
        return (order.index("gold"), "") if is_good_section else unknown
    if primary in ("evil gold", "evilgold"):
        return (order.index("gold"), "") if not is_good_section else unknown
    if primary == "gold":
        alignment = card_data.get("alignment")
        if alignment == "Good":
            gold_is_good = True
        elif alignment == "Evil":
            gold_is_good = False
        else:
            first_part = _type_parts(card_data.get("type", ""))[0]
            gold_is_good = first_part not in _EVIL_SIDE_TYPES  # default good
        return (order.index("gold"), "") if gold_is_good == is_good_section else unknown

    if primary in order:
        return (order.index(primary), "")
    return unknown


def _character_or_enhancement(card_data: Dict[str, Any]) -> int:
    """0 = character (Hero / Evil Character first part), 1 = enhancement."""
    first_part = _type_parts(card_data.get("type", ""))[0]
    return 0 if first_part in _GOOD_CHARACTER_TYPES | _EVIL_CHARACTER_TYPES else 1


def _strength_key(card_data: Dict[str, Any]) -> Tuple[int, int]:
    """
    (has_strength, -strength): cards with a parseable strength sort first,
    strength descending. 'X'/'*'/'' have no strength.
    """
    match = _INT_PATTERN.search(str(card_data.get("strength", "") or ""))
    if match:
        return (0, -int(match.group()))
    return (1, 0)


def _reference_key(card_data: Dict[str, Any], card_name: str) -> Tuple:
    """(book_index, chapter, verse, raw_reference, name) — biblical order for Lost Souls."""
    reference = (card_data.get("reference") or "").strip()
    ref_lower = reference.lower()
    for prefix, index in _BOOK_PREFIXES:
        if ref_lower.startswith(prefix):
            match = _CHAPTER_VERSE_PATTERN.search(reference[len(prefix):])
            chapter, verse = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
            return (index, chapter, verse, ref_lower, card_name.lower())
    return (len(_BIBLE_BOOKS), 0, 0, ref_lower, card_name.lower())


def _section_rank(card_data: Dict[str, Any]) -> int:
    """Top-level section rank per the canonical default sort spec."""
    first_part = _type_parts(card_data.get("type", ""))[0]
    if first_part in _FIRST_PART_SECTIONS:
        return _FIRST_PART_SECTIONS[first_part]
    if first_part in _GOOD_SIDE_TYPES or first_part in _EVIL_SIDE_TYPES:
        if _is_dual(card_data):
            return _SEC_DUAL
        return _SEC_GOOD if first_part in _GOOD_SIDE_TYPES else _SEC_EVIL
    return _SEC_MISC


def default_sort_key(card_name: str, card_data: Dict[str, Any]) -> Tuple:
    """
    Canonical "default" comparator key:
    Dominants (dual/Good/Evil, alpha) -> Artifacts -> Covenants -> Curses ->
    Fortresses+Cities -> Sites -> Lost Souls (biblical reference order) ->
    dual-alignment characters/enhancements -> good brigades -> evil brigades ->
    everything else (type alpha, name alpha).
    """
    section = _section_rank(card_data)
    name = card_name.lower()

    if section == _SEC_DOMINANT:
        alignment_rank = {"Neutral": 0, "Good": 1, "Evil": 2}.get(
            card_data.get("alignment"), 3
        )
        return (section, alignment_rank, name)
    if section == _SEC_LOST_SOUL:
        return (section,) + _reference_key(card_data, card_name)
    if section in (_SEC_GOOD, _SEC_EVIL):
        brigade_rank, brigade_tiebreak = _primary_brigade_rank(
            card_data, is_good_section=(section == _SEC_GOOD)
        )
        return (
            (section, brigade_rank, brigade_tiebreak, _character_or_enhancement(card_data))
            + _strength_key(card_data)
            + (name,)
        )
    if section == _SEC_MISC:
        return (section, (card_data.get("type") or "").lower(), name)
    # Artifacts, Covenants, Curses, Fortresses+Cities, Sites, Duals: name only.
    return (section, name)


def sort_cards(
    cards_dict: Dict[str, Dict[str, Any]], sort_by: Union[str, List[str]] = "name"
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Sort cards by specified criteria.

    Args:
        cards_dict: Dictionary of card_name -> card_data
        sort_by: Single field or list of fields to sort by.
                Available fields: 'alignment', 'brigade', 'type', 'name'.
                The string "default" applies the canonical default card sort
                order (see default_sort_key).

    Returns:
        List of (card_name, card_data) tuples sorted by specified criteria

    Examples:
        sort_cards(cards, "default")  # Canonical default card sort order
        sort_cards(cards, "name")  # Sort by name only
        sort_cards(cards, ["alignment", "brigade", "name"])  # Multi-field sort
        sort_cards(cards, ["type", "alignment", "brigade", "name"])  # Full sort
    """
    if sort_by == "default":
        return sorted(
            cards_dict.items(), key=lambda item: default_sort_key(item[0], item[1])
        )

    if isinstance(sort_by, str):
        sort_by = [sort_by]

    def sort_key(item):
        card_name, card_data = item
        key_parts = []

        for field in sort_by:
            if field == "name":
                key_parts.append(_get_name(card_name))
            elif field in SORT_FIELDS:
                key_parts.append(SORT_FIELDS[field](card_data))
            else:
                raise ValueError(f"Unknown sort field: {field}")

        return tuple(key_parts)

    return sorted(cards_dict.items(), key=sort_key)


# Convenience functions for common patterns
def sort_by_alignment_brigade_name(
    cards_dict: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """Sort by alignment, then brigade, then name."""
    return sort_cards(cards_dict, ["alignment", "brigade", "name"])


def sort_by_brigade_name(
    cards_dict: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """Sort by brigade, then name."""
    return sort_cards(cards_dict, ["brigade", "name"])


def sort_by_name_only(
    cards_dict: Dict[str, Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """Sort by name only."""
    return sort_cards(cards_dict, "name")
