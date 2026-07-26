"""Tests for Decklist reserve-size validation in __init__.

Type 2's reserve cap is 20 (raised from 15 for the Aug 2026 rules change).
Type 1/Paragon stays at 10.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.utilities.decklist import Decklist

MAIN_DECK_CARD = "A Look Back"  # any real card in assets/carddata/carddata.jsonl


def make_deck_file(main_deck_qty: int, reserve_qty: int) -> str:
    """Write a temporary .txt decklist with the given main deck and reserve sizes."""
    fd, path = tempfile.mkstemp(suffix=".txt")
    lines = [f"{main_deck_qty}\t{MAIN_DECK_CARD}"]
    if reserve_qty:
        lines.append("Reserve:")
        lines.append(f"{reserve_qty}\t{MAIN_DECK_CARD}")
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def test_type_2_reserve_of_20_is_accepted():
    path = make_deck_file(main_deck_qty=40, reserve_qty=20)
    try:
        decklist = Decklist(path, deck_type="type_2")
        assert decklist.reserve_size == 20
    finally:
        os.remove(path)


def test_type_2_reserve_of_21_is_rejected():
    path = make_deck_file(main_deck_qty=40, reserve_qty=21)
    try:
        with pytest.raises(AssertionError, match="20 or less"):
            Decklist(path, deck_type="type_2")
    finally:
        os.remove(path)


def test_type_1_reserve_of_10_is_still_accepted():
    path = make_deck_file(main_deck_qty=40, reserve_qty=10)
    try:
        decklist = Decklist(path, deck_type="type_1")
        assert decklist.reserve_size == 10
    finally:
        os.remove(path)


def test_type_1_reserve_of_11_is_still_rejected():
    path = make_deck_file(main_deck_qty=40, reserve_qty=11)
    try:
        with pytest.raises(AssertionError, match="10 or less"):
            Decklist(path, deck_type="type_1")
    finally:
        os.remove(path)
