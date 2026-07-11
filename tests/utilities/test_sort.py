"""Tests for the canonical "default" card sort order (sort_cards(..., "default"))."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.utilities.sort import default_sort_key, sort_cards


def card(
    type="",
    brigade="",
    alignment="",
    strength="",
    reference="",
):
    """Build a minimal card dict shaped like Decklist._map_card_metadata output."""
    return {
        "type": type,
        "raw_brigade": brigade,
        "brigade": [],  # normalized list; the default sort must use raw_brigade
        "alignment": alignment,
        "strength": strength,
        "reference": reference,
        "quantity": 1,
    }


def sorted_names(cards_dict):
    return [name for name, _ in sort_cards(cards_dict, "default")]


def test_full_section_ordering():
    cards = {
        "Zeal Token": card(type="Hero Token"),
        "Emperor Nero": card(
                type="Evil Character",
                brigade="Gold",
                alignment="Evil",
                strength="10",
            ),
        "King David": card(type="Hero", brigade="Red", alignment="Good", strength="9"),
        "Abandoned": card(
                type="GE/EE",
                brigade="Green/Purple (Pale Green)",
                alignment="Neutral",
                strength="4 (0)",
            ),
        "Lost Soul [Romans 3:23]": card(type="Lost Soul", reference="Romans 3:23"),
        "Jerusalem Tower": card(type="Site", brigade="Purple"),
        "City of Enoch": card(type="City", brigade="White", alignment="Good"),
        "Raamses": card(type="Fortress", brigade="Black", alignment="Evil"),
        "Burial Shroud": card(type="Curse", alignment="Evil"),
        "Solomon's Temple Covenant": card(type="Covenant", alignment="Good"),
        "Ark of the Covenant": card(type="Artifact", alignment="Neutral"),
        "Son of God": card(type="Dominant", alignment="Good"),
    }
    assert sorted_names(cards) == [
        "Son of God",
        "Ark of the Covenant",
        "Solomon's Temple Covenant",
        "Burial Shroud",
        "City of Enoch",
        "Raamses",
        "Jerusalem Tower",
        "Lost Soul [Romans 3:23]",
        "Abandoned",
        "King David",
        "Emperor Nero",
        "Zeal Token",
    ]


def test_dominants_dual_then_good_then_evil_alpha_within():
    cards = {
        "Son of God": card(type="Dominant", alignment="Good"),
        "Christian Martyr": card(type="Dominant", alignment="Evil"),
        "Angel of the Lord": card(type="Dominant", alignment="Good"),
        "Falling Away": card(type="Dominant", alignment="Evil"),
        "Grapes of Wrath": card(type="Dominant", alignment="Neutral"),
    }
    assert sorted_names(cards) == [
        "Grapes of Wrath",
        "Angel of the Lord",
        "Son of God",
        "Christian Martyr",
        "Falling Away",
    ]


def test_artifacts_covenants_curses_each_alpha():
    cards = {
        "Withered Hand": card(type="Curse"),
        "Noah's Covenant": card(type="Covenant"),
        "Altar of Dagon": card(type="Curse"),
        "Golden Cherubim": card(type="Artifact"),
        "Ark of the Covenant": card(type="Artifact"),
        "Davidic Covenant": card(type="Covenant"),
    }
    assert sorted_names(cards) == [
        "Ark of the Covenant",
        "Golden Cherubim",
        "Davidic Covenant",
        "Noah's Covenant",
        "Altar of Dagon",
        "Withered Hand",
    ]


def test_fortresses_and_cities_interleave_then_sites():
    cards = {
        "Nazareth": card(type="City"),
        "Babel": card(type="Fortress"),
        "Zerubbabel's Temple": card(type="Fortress"),
        "City of Refuge": card(type="City"),
        "Abraham's Bosom": card(type="Site"),
        "Damascus": card(type="Site"),
    }
    assert sorted_names(cards) == [
        "Babel",
        "City of Refuge",
        "Nazareth",
        "Zerubbabel's Temple",
        "Abraham's Bosom",
        "Damascus",
    ]


def test_fortress_slash_evil_character_lands_in_fortress_section():
    cards = {
        "Rulers over Earth": card(
                type="Fortress / Evil Character",
                brigade="Brown",
                alignment="Evil",
                strength="4",
            ),
        "Babel": card(type="Fortress"),
        "Emperor Nero": card(
                type="Evil Character",
                brigade="Gold",
                alignment="Evil",
                strength="10",
            ),
    }
    assert sorted_names(cards) == ["Babel", "Rulers over Earth", "Emperor Nero"]


def test_lost_souls_biblical_reference_order():
    cards = {
        "LS John": card(type="Lost Soul", reference="John 3:16"),
        "LS II John": card(type="Lost Soul", reference="II John 1:9"),
        "LS I John": card(type="Lost Soul", reference="I John 1:8"),
        "LS II Kings": card(type="Lost Soul", reference="II Kings 4:8-37"),
        "LS I Kings": card(type="Lost Soul", reference="I Kings 20:42"),
        "LS Genesis": card(type="Lost Soul", reference="Genesis 6:5"),
        "LS Psalm": card(type="Lost Soul", reference="Psalm 22:1"),
        "LS Revelation": card(type="Lost Soul", reference="Revelation 20:15"),
        "LS Empty Ref": card(type="Lost Soul", reference=""),
    }
    assert sorted_names(cards) == [
        "LS Genesis",
        "LS I Kings",
        "LS II Kings",
        "LS Psalm",
        "LS John",
        "LS I John",
        "LS II John",
        "LS Revelation",
        "LS Empty Ref",  # unknown/empty reference sorts after all known books
    ]


def test_lost_souls_same_book_by_chapter_then_verse():
    cards = {
        "LS Rom 3:23": card(type="Lost Soul", reference="Romans 3:23"),
        "LS Rom 3:10": card(type="Lost Soul", reference="Romans 3:10"),
        "LS Rom 1:20": card(type="Lost Soul", reference="Romans 1:20"),
    }
    assert sorted_names(cards) == ["LS Rom 1:20", "LS Rom 3:10", "LS Rom 3:23"]


def test_dual_cards_sort_between_lost_souls_and_good_brigades():
    cards = {
        "Zebulun Banner": card(type="Hero", brigade="White", alignment="Good", strength="5"),
        "Eternal Judgment": card(
                type="GE/EE",
                brigade="Green/White and Brown/Crimson",
                alignment="Neutral",
            ),
        "Abandoned": card(
                type="GE/EE",
                brigade="Green/Purple (Pale Green)",
                alignment="Neutral",
                strength="4 (0)",
            ),
        "Abijah, the Conqueror": card(
                type="Hero/Evil Character",
                brigade="Purple/Red/Brown",
                alignment="Neutral",
                strength="4(3)",
            ),
        "Lost Soul [Romans 3:23]": card(type="Lost Soul", reference="Romans 3:23"),
    }
    assert sorted_names(cards) == [
        "Lost Soul [Romans 3:23]",
        "Abandoned",
        "Abijah, the Conqueror",
        "Eternal Judgment",
        "Zebulun Banner",
    ]


def test_and_brigade_marks_single_type_character_as_dual():
    # Brigade spanning good and evil ("Crimson and White/Purple") makes an
    # Evil Character dual even though its type is single-sided.
    cards = {
        "Nebuchadnezzar": card(
                type="Evil Character",
                brigade="Crimson and White/Purple",
                alignment="Evil",
                strength="4/11",
            ),
        "Emperor Nero": card(
                type="Evil Character",
                brigade="Gold",
                alignment="Evil",
                strength="10",
            ),
        "King David": card(type="Hero", brigade="Red", alignment="Good", strength="9"),
    }
    assert sorted_names(cards) == ["Nebuchadnezzar", "King David", "Emperor Nero"]


def test_good_brigade_order():
    order = ["Blue", "Clay", "Gold", "Green", "Multi", "Purple", "Red", "Silver", "Teal", "White"]
    cards = {
        "Hero %s" % brigade: card(type="Hero", brigade=brigade, alignment="Good", strength="5")
        for brigade in order
    }
    assert sorted_names(cards) == ["Hero %s" % brigade for brigade in order]


def test_evil_brigade_order():
    order = ["Black", "Brown", "Crimson", "Gold", "Gray", "Multi", "Orange", "Pale Green"]
    cards = {
        "EC %s" % brigade: card(
                type="Evil Character",
                brigade=brigade,
                alignment="Evil",
                strength="5",
            )
        for brigade in order
    }
    assert sorted_names(cards) == ["EC %s" % brigade for brigade in order]


def test_within_brigade_characters_then_enhancements_strength_desc():
    cards = {
        "Weak Hero": card(type="Hero", brigade="Red", alignment="Good", strength="3"),
        "Strong Hero": card(type="Hero", brigade="Red", alignment="Good", strength="9"),
        "Strong GE": card(type="GE", brigade="Red", alignment="Good", strength="6"),
        "Weak GE": card(type="GE", brigade="Red", alignment="Good", strength="2"),
        "Next Brigade Hero": card(type="Hero", brigade="Silver", alignment="Good", strength="12"),
    }
    assert sorted_names(cards) == [
        "Strong Hero",
        "Weak Hero",
        "Strong GE",
        "Weak GE",
        "Next Brigade Hero",
    ]


def test_strength_parsing_x_empty_and_parenthesized():
    cards = {
        "Paren Strength": card(type="Hero", brigade="Red", alignment="Good", strength="4 (0)"),
        "X Strength": card(type="Hero", brigade="Red", alignment="Good", strength="X"),
        "No Strength": card(type="Hero", brigade="Red", alignment="Good", strength=""),
        "Negative": card(type="Hero", brigade="Red", alignment="Good", strength="-1"),
        "Big": card(type="Hero", brigade="Red", alignment="Good", strength="10"),
    }
    # 10, 4, -1 (descending), then the strengthless cards alphabetically.
    assert sorted_names(cards) == [
        "Big",
        "Paren Strength",
        "Negative",
        "No Strength",
        "X Strength",
    ]


def test_gold_disambiguated_by_alignment():
    cards = {
        "Good Gold Hero": card(type="Hero", brigade="Gold", alignment="Good", strength="5"),
        "Blue Hero": card(type="Hero", brigade="Blue", alignment="Good", strength="5"),
        "Green Hero": card(type="Hero", brigade="Green", alignment="Good", strength="5"),
        "Evil Gold EC": card(
                type="Evil Character",
                brigade="Gold",
                alignment="Evil",
                strength="5",
            ),
        "Crimson EC": card(
                type="Evil Character",
                brigade="Crimson",
                alignment="Evil",
                strength="5",
            ),
        "Gray EC": card(type="Evil Character", brigade="Gray", alignment="Evil", strength="5"),
    }
    # Good: Blue < Gold < Green; Evil: Crimson < Gold < Gray.
    assert sorted_names(cards) == [
        "Blue Hero",
        "Good Gold Hero",
        "Green Hero",
        "Crimson EC",
        "Evil Gold EC",
        "Gray EC",
    ]


def test_explicit_good_gold_and_evil_gold_tokens():
    cards = {
        "Good Gold Hero": card(type="Hero", brigade="Good Gold", strength="5"),
        "Blue Hero": card(type="Hero", brigade="Blue", strength="5"),
        "Green Hero": card(type="Hero", brigade="Green", strength="5"),
        "Evil Gold EC": card(type="Evil Character", brigade="Evil Gold", strength="5"),
        "Brown EC": card(type="Evil Character", brigade="Brown", strength="5"),
        "Gray EC": card(type="Evil Character", brigade="Gray", strength="5"),
    }
    assert sorted_names(cards) == [
        "Blue Hero",
        "Good Gold Hero",
        "Green Hero",
        "Brown EC",
        "Evil Gold EC",
        "Gray EC",
    ]


def test_paren_brigade_uses_prefix_and_multi_brigade_uses_first_token():
    cards = {
        "Gold Paren Hero": card(
                type="Hero",
                brigade="Gold (Gold/Red)",
                alignment="Good",
                strength="5",
            ),
        "Green Teal Hero": card(type="Hero", brigade="Green/Teal", alignment="Good", strength="5"),
        "Blue Hero": card(type="Hero", brigade="Blue", alignment="Good", strength="5"),
    }
    # Blue < Gold < Green (primary brigade of "Green/Teal" is Green).
    assert sorted_names(cards) == ["Blue Hero", "Gold Paren Hero", "Green Teal Hero"]


def test_unknown_brigade_sorts_after_known():
    cards = {
        "Mystery Hero": card(type="Hero", brigade="Fuchsia", alignment="Good", strength="9"),
        "White Hero": card(type="Hero", brigade="White", alignment="Good", strength="1"),
    }
    assert sorted_names(cards) == ["White Hero", "Mystery Hero"]


def test_misc_sorts_by_type_then_name():
    cards = {
        "B Lost Soul Token": card(type="Lost Soul Token"),
        "A Warrior Token": card(type="Warrior Token"),
        "Z Hero Token": card(type="Hero Token"),
        "A Hero Token": card(type="Hero Token"),
    }
    assert sorted_names(cards) == [
        "A Hero Token",
        "Z Hero Token",
        "B Lost Soul Token",
        "A Warrior Token",
    ]


def test_default_sort_key_direct_call():
    dominant = card(type="Dominant", alignment="Good")
    hero = card(type="Hero", brigade="Blue", alignment="Good", strength="5")
    assert default_sort_key("Son of God", dominant) < default_sort_key("Noble Hero", hero)


def test_existing_field_list_path_unchanged():
    cards = {
        "B Card": card(type="Hero", alignment="Good"),
        "A Card": card(type="Evil Character", alignment="Evil"),
    }
    assert [n for n, _ in sort_cards(cards, "name")] == ["A Card", "B Card"]
    assert [n for n, _ in sort_cards(cards, ["alignment", "name"])] == ["B Card", "A Card"]
