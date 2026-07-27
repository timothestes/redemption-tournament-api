"""Measure the printable geometry of a deck-check template PDF.

The section limits in text_to_pdf.py must equal the number of ruled writing
lines each section actually has on the template. This module recovers those
counts straight from the PDF so a test can assert the two agree, instead of
the constants being hand-maintained against a binary asset.

Uses PyPDF2 only (already a dependency) — no rendering, no system binaries.
Each ruled line is drawn as a thin filled rectangle, i.e. two horizontal
path segments ~1pt apart, so near-duplicate segments are merged.
"""

import re
from typing import Dict, List, Tuple

from PyPDF2 import PdfReader

_NUM = r"-?\d+\.?\d*"
_TOKEN = re.compile(rf"({_NUM})|([A-Za-z'\"*]+)")

RULE_WIDTH = 221.5  # inner width of every body column rule
WIDTH_TOL = 3.0
SECTION_GAP = 25.0  # vertical gap that separates one section from the next
LINE_MERGE = 2.0  # segments closer than this are the same printed rule

# Sections in top-to-bottom order within each column.
COLUMN_SECTIONS = [
    ["Dominant", "Hero", "GE"],
    ["Lost Soul", "Evil Character", "EE"],
    ["Artifact", "Fortress", "Misc", "Reserve"],
]


def _mul(a, b):
    return (a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5])


def _apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def horizontal_rules(pdf_path: str) -> List[Tuple[float, float]]:
    """(y_from_top, x_start) for every ruled writing line, top-down."""
    page = PdfReader(pdf_path).pages[0]
    height = float(page.mediabox.height)
    data = page.get_contents().get_data().decode("latin-1")

    ctm, stack, operands, cur = (1, 0, 0, 1, 0, 0), [], [], None
    found = []
    for match in _TOKEN.finditer(data):
        if match.group(1) is not None:
            operands.append(float(match.group(1)))
            continue
        op = match.group(2)
        if op == "q":
            stack.append(ctm)
        elif op == "Q":
            ctm = stack.pop() if stack else (1, 0, 0, 1, 0, 0)
        elif op == "cm" and len(operands) >= 6:
            ctm = _mul(tuple(operands[-6:]), ctm)
        elif op == "m" and len(operands) >= 2:
            cur = _apply(ctm, operands[-2], operands[-1])
        elif op == "l" and len(operands) >= 2:
            point = _apply(ctm, operands[-2], operands[-1])
            if cur is not None and abs(point[1] - cur[1]) < 0.4:
                width = abs(point[0] - cur[0])
                if abs(width - RULE_WIDTH) <= WIDTH_TOL:
                    found.append((height - cur[1], min(cur[0], point[0])))
            cur = point
        operands = []

    return sorted(found)


def section_line_counts(pdf_path: str) -> Dict[str, int]:
    """Section name -> number of ruled writing lines on this template."""
    rules = horizontal_rules(pdf_path)
    if not rules:
        raise AssertionError(
            f"No ruled lines detected in {pdf_path}. The template's drawing "
            "style likely changed; re-verify the section limits by hand."
        )

    # Split into columns by x position.
    columns: List[List[float]] = []
    for x_start in sorted({round(x) for _, x in rules}):
        if columns and x_start - columns[-1][0] < 20:
            continue
        columns.append([x_start])
    column_x = [c[0] for c in columns]

    grouped: Dict[str, int] = {}
    for index, x_ref in enumerate(column_x):
        ys = sorted(y for y, x in rules if abs(x - x_ref) < 20)
        # Each printed rule is a thin rectangle: two edges ~1pt apart. Merge
        # them here, per column, since all columns share the same y values.
        lines = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > LINE_MERGE]
        sections: List[List[float]] = []
        for y in lines:
            if sections and y - sections[-1][-1] <= SECTION_GAP:
                sections[-1].append(y)
            else:
                sections.append([y])
        # A lone rule is a header underline (e.g. beneath "Reserve:"), not a
        # writing line.
        sections = [s for s in sections if len(s) > 1]
        names = COLUMN_SECTIONS[index] if index < len(COLUMN_SECTIONS) else []
        for name, section in zip(names, sections):
            grouped[name] = len(section)
    return grouped
