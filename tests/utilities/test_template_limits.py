"""Guard the section limits against template drift.

T1_SECTION_LIMITS / T2_SECTION_LIMITS must equal the number of ruled writing
lines each section physically has on the deck-check template. Those constants
are hand-maintained against a binary PDF, so nothing otherwise catches the
case where a new template is dropped in and the numbers are not re-measured —
the failure mode is silent: cards either vanish off the page or get pushed to
an overflow page that was not needed.

These tests read the geometry back out of the templates themselves, so
swapping in a new sheet fails loudly here instead of in a player's hands.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest

from src.utilities.text_to_pdf import (
    T1_RESERVE_LINE_LIMIT,
    T1_SECTION_LIMITS,
    T1_TEMPLATE,
    T2_RESERVE_LINE_LIMIT,
    T2_SECTION_LIMITS,
    T2_TEMPLATE,
)
from tests.utilities.template_geometry import section_line_counts

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def _measure(template):
    return section_line_counts(os.path.join(REPO_ROOT, template))


@pytest.fixture(scope="module")
def t1_geometry():
    return _measure(T1_TEMPLATE)


@pytest.fixture(scope="module")
def t2_geometry():
    return _measure(T2_TEMPLATE)


def test_t1_templates_exist():
    for template in (T1_TEMPLATE, T2_TEMPLATE):
        assert os.path.exists(os.path.join(REPO_ROOT, template)), template


@pytest.mark.parametrize("section", sorted(T1_SECTION_LIMITS))
def test_t1_section_limit_matches_template(section, t1_geometry):
    """Every T1 limit equals the ruled lines that section has on the sheet."""
    assert t1_geometry[section] == T1_SECTION_LIMITS[section], (
        f"T1 '{section}': template has {t1_geometry[section]} ruled lines but "
        f"T1_SECTION_LIMITS says {T1_SECTION_LIMITS[section]}. Re-measure the "
        f"template and update the constant."
    )


@pytest.mark.parametrize("section", sorted(T2_SECTION_LIMITS))
def test_t2_section_limit_matches_template(section, t2_geometry):
    """Every T2 limit equals the ruled lines that section has on the sheet."""
    assert t2_geometry[section] == T2_SECTION_LIMITS[section], (
        f"T2 '{section}': template has {t2_geometry[section]} ruled lines but "
        f"T2_SECTION_LIMITS says {T2_SECTION_LIMITS[section]}. Re-measure the "
        f"template and update the constant."
    )


def test_reserve_line_limits_match_templates(t1_geometry, t2_geometry):
    """The Reserve boxes hold exactly the number of lines the code assumes."""
    assert t1_geometry["Reserve"] == T1_RESERVE_LINE_LIMIT
    assert t2_geometry["Reserve"] == T2_RESERVE_LINE_LIMIT


def test_reserve_boxes_hold_a_full_legal_reserve(t1_geometry, t2_geometry):
    """
    A legal reserve must fit on the sheet: 10 cards for T1/paragon, 20 for T2.
    If a template ever shrinks these, reserve cards get routed to an overflow
    page (T2) or drawn off the bottom edge (T1).
    """
    assert t1_geometry["Reserve"] >= 10
    assert t2_geometry["Reserve"] >= 20


def test_every_section_is_measurable(t1_geometry, t2_geometry):
    """A silently-empty measurement would make the assertions above vacuous."""
    for geometry, limits in ((t1_geometry, T1_SECTION_LIMITS),
                             (t2_geometry, T2_SECTION_LIMITS)):
        assert set(limits).issubset(geometry)
        assert all(geometry[section] > 0 for section in limits)
