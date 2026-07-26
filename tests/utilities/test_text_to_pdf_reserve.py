"""Tests for split_reserve_by_line_count, the helper that prevents the T2
deck-check PDF from silently drawing reserve cards off the bottom of the
page. The T2 template's Reserve box only has room for a fixed number of
printed lines (T2_RESERVE_LINE_LIMIT); anything beyond that must be routed
to the OVERFLOW page instead of being lost past the physical page edge.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.utilities.text_to_pdf import split_reserve_by_line_count


def card(quantity=1):
    return {"quantity": quantity}


def make_reserve(names_and_quantities):
    """Build a reserve dict of {name: card_data} preserving insertion order."""
    return {name: card(qty) for name, qty in names_and_quantities}


def test_reserve_at_or_under_limit_is_fully_visible_with_empty_overflow():
    # 15 single-quantity cards, max_lines=15: everything fits exactly.
    names = [f"A{i:02d}" for i in range(1, 16)]
    reserve = make_reserve([(n, 1) for n in names])

    visible, overflow = split_reserve_by_line_count(reserve, "name", max_lines=15)

    assert set(visible.keys()) == set(names)
    assert overflow == {}


def test_reserve_over_limit_splits_at_the_line_boundary():
    # 18 single-quantity cards, max_lines=15: first 15 (alphabetically) stay
    # visible, the last 3 overflow.
    names = [f"A{i:02d}" for i in range(1, 19)]
    reserve = make_reserve([(n, 1) for n in names])

    visible, overflow = split_reserve_by_line_count(reserve, "name", max_lines=15)

    assert list(visible.keys()) == names[:15]
    assert list(overflow.keys()) == names[15:]
    assert len(visible) == 15
    assert len(overflow) == 3


def test_card_whose_quantity_would_straddle_the_boundary_moves_entirely_to_overflow():
    # 14 single-quantity cards (A01..A14, using 14 of 15 lines) followed by
    # one card with quantity=3 (would need lines 15-17, exceeding max_lines
    # of 15). That card must NOT be split 1-in/2-out; it goes to overflow
    # whole, per the docstring's "kept whole" guarantee.
    singles = [(f"A{i:02d}", 1) for i in range(1, 15)]  # 14 cards, 14 lines
    straddler = ("Z-Straddler", 3)
    reserve = make_reserve(singles + [straddler])

    visible, overflow = split_reserve_by_line_count(reserve, "name", max_lines=15)

    assert list(visible.keys()) == [name for name, _ in singles]
    assert sum(c["quantity"] for c in visible.values()) == 14
    assert overflow == {"Z-Straddler": card(3)}
