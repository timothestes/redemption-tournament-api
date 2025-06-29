"""
Utility functions for sorting cards by various criteria.

This module provides a flexible sorting system for Redemption card data,
allowing for customizable sort orders based on alignment, brigade, name, and other attributes.
"""

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


def sort_cards(
    cards_dict: Dict[str, Dict[str, Any]], sort_by: Union[str, List[str]] = "name"
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Sort cards by specified criteria.

    Args:
        cards_dict: Dictionary of card_name -> card_data
        sort_by: Single field or list of fields to sort by.
                Available fields: 'alignment', 'brigade', 'type', 'name'

    Returns:
        List of (card_name, card_data) tuples sorted by specified criteria

    Examples:
        sort_cards(cards, "name")  # Sort by name only
        sort_cards(cards, ["alignment", "brigade", "name"])  # Multi-field sort
        sort_cards(cards, ["type", "alignment", "brigade", "name"])  # Full sort
    """
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
