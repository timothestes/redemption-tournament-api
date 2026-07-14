"""Tests for Decklist.calculate_aod_count.

All decks here are built so every simulation iteration produces the same
count, so the Monte Carlo average is exact and the assertions are not flaky.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.utilities.decklist import Decklist


def make_decklist(cards: dict) -> Decklist:
    """Build a Decklist without running __init__ (no deck file needed)."""
    decklist = Decklist.__new__(Decklist)
    decklist.mapped_main_deck_list = cards
    return decklist


def card(reference="", type="", quantity=1):
    return {"reference": reference, "type": type, "quantity": quantity}


def test_all_daniel_heroes_count_fully():
    decklist = make_decklist(
        {"Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=9)}
    )
    assert decklist.calculate_aod_count() == 9.0


def test_daniel_lost_souls_do_not_score():
    # Every card is a Daniel Lost Soul: the chain always triggers, but Lost
    # Souls are excluded from the number itself.
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=9
            )
        }
    )
    assert decklist.calculate_aod_count() == 0.0


def test_daniel_lost_soul_still_triggers_the_chain():
    # 4 Daniel Lost Souls + 5 Daniel heroes in a 9-card deck: the first 3 are
    # always Daniel cards (chain always goes), and the scored top 9 is always
    # exactly the 5 non-Lost Soul Daniel cards.
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=4
            ),
            "Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=5),
        }
    )
    assert decklist.calculate_aod_count() == 5.0


def test_daniel_lost_souls_alone_cannot_score():
    # Daniel Lost Souls trigger the chain but nothing scoreable exists, so the
    # count is 0 (previously these souls inflated the number).
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=3
            ),
            "Plain Hero": card(reference="Genesis 1:1", type="Hero", quantity=6),
        }
    )
    assert decklist.calculate_aod_count() == 0.0


def test_no_daniel_cards_means_zero():
    decklist = make_decklist(
        {"Plain Hero": card(reference="Genesis 1:1", type="Hero", quantity=9)}
    )
    assert decklist.calculate_aod_count() == 0.0


def test_fewer_than_nine_cards_returns_zero():
    decklist = make_decklist(
        {"Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=8)}
    )
    assert decklist.calculate_aod_count() == 0.0


def test_ancient_of_days_itself_is_excluded():
    # AoD is skipped from the pool, leaving only 8 cards -> 0.0.
    decklist = make_decklist(
        {
            "The Ancient of Days": card(reference="Daniel 7:9", type="Dominant"),
            "Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=8),
        }
    )
    assert decklist.calculate_aod_count() == 0.0
