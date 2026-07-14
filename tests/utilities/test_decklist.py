"""Tests for Decklist.calculate_aod_count and calculate_aod_breakdown.

Most decks here are built so every simulation iteration produces the same
result, so the Monte Carlo value is exact and the assertions are not flaky.
The one probabilistic breakdown case seeds the RNG and asserts within a wide
tolerance.
"""

import os
import random
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


# --- calculate_aod_breakdown ------------------------------------------------
# Returns {"aod_count", "soul_aod_count", "whiff_percentage"} from one
# simulation. aod_count is the non-Lost Soul Daniel count (the default number),
# soul_aod_count is the Daniel Lost Soul count, and whiff_percentage is the
# share of draws with no Daniel reference in the top 3 (chain never triggers).


def test_breakdown_all_daniel_heroes():
    decklist = make_decklist(
        {"Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=9)}
    )
    result = decklist.calculate_aod_breakdown()
    assert result["aod_count"] == 9.0
    assert result["soul_aod_count"] == 0.0
    assert result["whiff_percentage"] == 0.0


def test_breakdown_all_daniel_souls_score_only_as_souls():
    # A Daniel Lost Soul in the top 3 still triggers (whiff 0), but the souls
    # land in soul_aod_count, never in the non-soul aod_count.
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=9
            )
        }
    )
    result = decklist.calculate_aod_breakdown()
    assert result["aod_count"] == 0.0
    assert result["soul_aod_count"] == 9.0
    assert result["whiff_percentage"] == 0.0


def test_breakdown_mixed_souls_and_heroes():
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=4
            ),
            "Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=5),
        }
    )
    result = decklist.calculate_aod_breakdown()
    assert result["aod_count"] == 5.0
    assert result["soul_aod_count"] == 4.0
    assert result["whiff_percentage"] == 0.0


def test_breakdown_no_daniel_cards_always_whiffs():
    decklist = make_decklist(
        {"Plain Hero": card(reference="Genesis 1:1", type="Hero", quantity=9)}
    )
    result = decklist.calculate_aod_breakdown()
    assert result["aod_count"] == 0.0
    assert result["soul_aod_count"] == 0.0
    assert result["whiff_percentage"] == 100.0


def test_breakdown_aod_count_matches_standalone_method():
    # The breakdown's aod_count is the same statistic calculate_aod_count
    # returns, so a deterministic deck agrees exactly.
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=4
            ),
            "Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=5),
        }
    )
    assert (
        decklist.calculate_aod_breakdown()["aod_count"]
        == decklist.calculate_aod_count()
    )


def test_breakdown_probabilistic_soul_count_and_whiff():
    # 3 Daniel souls + 6 non-Daniel (9-card deck). The chain triggers only when
    # a soul is in the top 3: analytic whiff = C(6,3)/C(9,3) = 20/84 = 23.81%.
    # When triggered, all 3 souls are in the top 9, so
    # soul_aod = 3 * (1 - 0.2381) = 2.29. aod_count is always 0 (no non-soul
    # Daniel exists). Seeded so the assertion is deterministic.
    decklist = make_decklist(
        {
            "Lost Soul [Daniel 3:6]": card(
                reference="Daniel 3:6", type="Lost Soul", quantity=3
            ),
            "Plain Hero": card(reference="Genesis 1:1", type="Hero", quantity=6),
        }
    )
    random.seed(12345)
    result = decklist.calculate_aod_breakdown()
    assert result["aod_count"] == 0.0
    assert abs(result["whiff_percentage"] - 23.81) < 2.0
    assert abs(result["soul_aod_count"] - 2.29) < 0.2


def test_breakdown_fewer_than_nine_cards_returns_zeros():
    decklist = make_decklist(
        {"Daniel Hero": card(reference="Daniel 1:8", type="Hero", quantity=8)}
    )
    assert decklist.calculate_aod_breakdown() == {
        "aod_count": 0.0,
        "soul_aod_count": 0.0,
        "whiff_percentage": 0.0,
    }
