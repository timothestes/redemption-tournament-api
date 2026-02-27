import os
import re
from typing import List, Union

from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from src.utilities.config import str_to_bool
from src.utilities.sort import sort_cards

load_dotenv()

# Precompile regex patterns for efficiency.
SET_NAME_PATTERN = re.compile(r"(\([^)]*\))\s*$")
LOST_SOUL_PREFIX_PATTERN = re.compile(r"^Lost Soul\s+")
BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")
HYPHEN_PATTERN = re.compile(r"\s*-\s*[^]]+")

NON_MISC_TYPES = [
    "Dominant",
    "Hero",
    "GE",
    "Lost Soul",
    "Evil Character",
    "EE",
    "Artifact",
    "Fortress",
    "Site",
    "Curse",
    "Covenant",
    "City",
]

T1_SECTION_LIMITS = {
    "Dominant": 21,
    "Hero": 20,
    "GE": 13,
    "Lost Soul": 21,
    "Evil Character": 20,
    "EE": 13,
    "Artifact": 16,  # Combined: Artifact, Covenant, Curse
    "Fortress": 13,  # Combined: Fortress, Site, City
    "Misc": 10,
}

T2_SECTION_LIMITS = {
    "Dominant": 23,
    "Hero": 20,
    "GE": 11,
    "Lost Soul": 23,
    "Evil Character": 20,
    "EE": 11,
    "Artifact": 16,  # Combined: Artifact, Covenant, Curse
    "Fortress": 11,  # Combined: Fortress, Site, City
    "Misc": 10,
}


def clean_card_name(card_name, card_data):
    """
    Clean the card name.
    - If the name contains a '/', use the part before it and append any
      trailing set name in parentheses.
    - For Lost Soul cards:
        - Keep quoted nicknames (without quotes)
        - Keep first verse reference only
        - Remove set information in brackets
    """
    # Special handling for Lost Souls
    if card_data.get("type") == "Lost Soul" and "Lost Soul" in card_name:
        nickname_match = re.search(r'"([^"]+)"', card_name)
        if nickname_match:
            nickname = nickname_match.group(1)  # group(1) gets content without quotes
            verse_match = re.search(r"\[([^/\]]+)", card_name)
            if verse_match:
                verse = f"[{verse_match.group(1)}]"
                return f"{nickname} {verse}"
        return card_name.split("[")[0].strip()

    # Handle cards with set information, special case for (I/J+)
    if "/" in card_name and "(I/J+)" not in card_name:
        base_name = card_name.split("/")[0].strip()
        match = SET_NAME_PATTERN.search(card_name)
        if match:
            return f"{base_name} {match.group(1).strip()}"
        return base_name

    return card_name


def filter_section(deck, card_types):
    """Filter deck by card type specification, handling 'misc', 'all', and list cases."""
    if card_types == "misc":
        return {k: v for k, v in deck.items() if v.get("type") not in NON_MISC_TYPES}
    elif card_types == "all":
        return dict(deck)
    elif isinstance(card_types, str):
        return {k: v for k, v in deck.items() if v.get("type") == card_types}
    else:
        return {k: v for k, v in deck.items() if v.get("type") in card_types}


def place_section(
    c,
    section_data,
    x,
    y,
    line_spacing,
    add_quantity=True,
    color_alignment=False,
    sort_by: Union[str, List[str]] = "name",
    max_items: int = None,
):
    """
    Place sorted items from section_data at (x, y) on the canvas.
    If add_quantity is False, list each card multiple times based on quantity.
    If color_alignment is True, cards are colored based on their alignment.
    If max_items is set, only draw that many unique cards; returns remaining as overflow dict.
    """
    sorted_items = sort_cards(section_data, sort_by)

    if max_items is not None and len(sorted_items) > max_items:
        overflow_items = dict(sorted_items[max_items:])
        sorted_items = sorted_items[:max_items]
    else:
        overflow_items = {}

    for card_name, card_data in sorted_items:
        display_name = clean_card_name(card_name, card_data)

        # Set color based on alignment if enabled
        if color_alignment:
            alignment = card_data.get("alignment", "Neutral")
            if alignment == "Good":
                c.setFillColorRGB(0, 0.5, 0)  # Green
            elif alignment == "Evil":
                c.setFillColorRGB(0.8, 0, 0)  # Red
            elif alignment == "Neutral":
                c.setFillColorRGB(
                    0.3, 0.3, 0.3
                )  # Darker Gray (changed from 0.5, 0.5, 0.5)

        if add_quantity:
            display_text = f"{card_data.get('quantity', 1)}x {display_name}"
            c.drawString(x, y, display_text)
            y -= line_spacing
        else:
            # List the card multiple times based on quantity
            quantity = card_data.get("quantity", 1)
            for _ in range(quantity):
                c.drawString(x, y, display_name)
                y -= line_spacing

        # Reset color to black after drawing
        if color_alignment:
            c.setFillColorRGB(0, 0, 0)

    return overflow_items


def place_section_by_type(
    c,
    deck,
    height_points,
    card_types,
    x,
    y,
    add_quantity=True,
    color_alignment=False,
    sort_by: Union[str, List[str]] = "name",
    max_items: int = None,
):
    """
    Filter main_deck by card_types and place the section.
    Returns a dict of overflow items (empty if no overflow).
    """
    y = height_points - y
    line_spacing = 16
    filtered = filter_section(deck, card_types)
    return place_section(
        c,
        filtered,
        x,
        y,
        line_spacing,
        add_quantity,
        color_alignment,
        sort_by,
        max_items,
    )


def draw_count(
    c, cards, height_points, card_types, x, y, font="Helvetica", font_size=12
):
    """Draw just the total count (number) for cards at (x, y)."""
    y = height_points - y
    total = 0
    for card_data in cards.values():
        if card_types == "misc":
            if card_data.get("type") not in [
                "Dominant",
                "Hero",
                "GE",
                "Lost Soul",
                "Evil Character",
                "EE",
                "Artifact",
                "Fortress",
                "Site",
                "Curse",
                "Covenant",
                "City",
            ]:
                total += card_data.get("quantity", 1)
        elif card_data.get("type") == card_types or card_data.get("type") in card_types:
            total += card_data.get("quantity", 1)
        elif card_types == "all":
            total += card_data.get("quantity", 1)

    c.setFont(font, font_size)
    c.drawString(x, y, str(total))


def draw_overflow_page(
    c, overflow_sections, width_points, height_points, name="", event=""
):
    """
    Draw a plain overflow page onto the canvas.
    Caller must call c.showPage() before this to start a fresh page,
    and c.showPage() after to finalize it.
    overflow_sections: list of (label, items_dict) tuples (only non-empty sections).
    """
    margin_x = 50
    margin_y = 50
    col_gap = 20
    col_width = (width_points - 2 * margin_x - col_gap) / 2
    line_spacing = 14
    section_gap = 10
    header_h = 18

    header_text = "OVERFLOW"
    if name:
        header_text += f"  —  {name}"
    if event:
        header_text += f"  |  {event}"

    def draw_page_header():
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(margin_x, height_points - margin_y, header_text)
        c.line(
            margin_x,
            height_points - margin_y - 5,
            width_points - margin_x,
            height_points - margin_y - 5,
        )

    draw_page_header()
    content_top = height_points - margin_y - 26
    bottom_limit = margin_y

    col = 0
    x = margin_x
    y = content_top

    def advance():
        nonlocal col, x, y
        if col == 0:
            col = 1
            x = margin_x + col_width + col_gap
            y = content_top
        else:
            c.showPage()
            draw_page_header()
            col = 0
            x = margin_x
            y = content_top

    for label, items in overflow_sections:
        if not items:
            continue

        # Ensure room for at least the section header + one card line
        if y - header_h - line_spacing < bottom_limit:
            advance()

        # Section header
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y, label.upper())
        y -= header_h

        # Cards
        c.setFont("Helvetica", 9)
        for card_name, card_data in items.items():
            if y - line_spacing < bottom_limit:
                advance()
                c.setFont("Helvetica-Bold", 10)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x, y, label.upper() + " (cont.)")
                y -= header_h
                c.setFont("Helvetica", 9)

            display_name = clean_card_name(card_name, card_data)
            qty = card_data.get("quantity", 1)
            c.drawString(x + 8, y, f"{qty}x {display_name}")
            y -= line_spacing

        y -= section_gap


def make_pdf(
    deck_type: str,
    deck_data: dict,
    filename: str,
    name: str,
    event: str,
    show_alignment: bool = False,
    sort_by: Union[str, List[str]] = ["type", "alignment", "brigade", "name"],
    m_count_value: float = None,
    aod_count_value: float = None,
):
    """
    Generate a deck check sheet overlay with card listings, section counts,
    and a total card count.

    Args:
        deck_type: Type of deck ('type_1' or 'type_2')
        deck_data: Dictionary containing deck data
        filename: Output filename
        name: Player name
        event: Event name
        show_alignment: Whether to show alignment colors and counts
        sort_by: Single field or list of fields to sort by.
                Available fields: 'alignment', 'brigade', 'type', 'name'
        m_count_value: The calculated M count value to display (default: None)
        aod_count_value: The calculated AoD count value to display (default: None)
    """
    if show_alignment:
        color_alignment = True
    else:
        color_alignment = False
    if deck_type == "type_1":
        template_path = "assets/pdfs/t1_deck_check.pdf"
    elif deck_type == "type_2":
        template_path = "assets/pdfs/t2_deck_check.pdf"

    # Create output directory if it doesn't exist
    if str_to_bool(os.getenv("DEBUG")):
        deck_directory = "tmp"
    else:
        deck_directory = "/tmp"
    os.makedirs(deck_directory, exist_ok=True)

    # Use system temp directory for all temporary files
    output_path = os.path.join(deck_directory, f"{filename}.pdf")
    temp_overlay = os.path.join(deck_directory, f"temp_{filename}.pdf")

    reader = PdfReader(template_path)
    page = reader.pages[0]
    width_points = float(page.mediabox.width)
    height_points = float(page.mediabox.height)

    c = canvas.Canvas(temp_overlay, pagesize=(width_points, height_points))
    main_deck = deck_data.get("main_deck", {})
    reserve = deck_data.get("reserve", {})

    if deck_type == "type_1":
        section_mappings = {
            "lists": {
                "Dominant": {"x": 57, "y": 180},
                "Hero": {"x": 57, "y": 548},
                "GE": {"x": 57, "y": 895},
                "Lost Soul": {"x": 310, "y": 180},
                "Evil Character": {"x": 310, "y": 548},
                "EE": {"x": 310, "y": 895},
                "Artifact": {"x": 560, "y": 181},
                "Fortress": {"x": 560, "y": 474},
                "Misc": {"x": 560, "y": 700},
                "Reserve": {"x": 580, "y": 913},
            },
            "numbers": {
                "Dominant": {"x": 124, "y": 153},
                "Hero": {"x": 97, "y": 532},
                "GE": {"x": 189, "y": 877},
                "Lost Soul": {"x": 381, "y": 154},
                "Evil Character": {"x": 408, "y": 532},
                "EE": {"x": 439, "y": 877},
                "Artifact": {"x": 741, "y": 153},
                "Fortress": {"x": 710, "y": 454},
                "Misc": {"x": 596, "y": 687},
                "Reserve": {"x": 617, "y": 875},
            },
        }
    elif deck_type == "type_2":
        section_mappings = section_mappings = {
            "lists": {
                "Dominant": {"x": 57, "y": 178},
                "Hero": {"x": 57, "y": 575},
                "GE": {"x": 57, "y": 920},
                "Lost Soul": {"x": 310, "y": 178},
                "Evil Character": {"x": 310, "y": 572},
                "EE": {"x": 310, "y": 920},
                "Artifact": {"x": 560, "y": 178},
                "Fortress": {"x": 560, "y": 474},
                "Misc": {"x": 560, "y": 668},
                "Reserve": {"x": 580, "y": 858},
            },
            "numbers": {
                "Dominant": {"x": 124, "y": 150},
                "Hero": {"x": 96, "y": 557},
                "GE": {"x": 188, "y": 901},
                "Lost Soul": {"x": 380, "y": 150},
                "Evil Character": {"x": 408, "y": 556},
                "EE": {"x": 435, "y": 902},
                "Artifact": {"x": 744, "y": 151},
                "Fortress": {"x": 710, "y": 451},
                "Misc": {"x": 596, "y": 655},
                "Reserve": {"x": 612, "y": 836},
            },
        }

    # Draw card listings with color_alignment option.
    # Enforce per-section limits on main deck only; reserve has no limit.
    limits = T1_SECTION_LIMITS if deck_type == "type_1" else T2_SECTION_LIMITS
    overflow_sections = []

    def _draw_section(label, card_types, section_key, **kwargs):
        overflow = place_section_by_type(
            c,
            main_deck,
            height_points,
            card_types,
            x=section_mappings["lists"][section_key]["x"],
            y=section_mappings["lists"][section_key]["y"],
            color_alignment=color_alignment,
            sort_by=sort_by,
            max_items=limits.get(label),
            **kwargs,
        )
        if overflow:
            overflow_sections.append((label, overflow))

    _draw_section("Dominant", "Dominant", "Dominant")
    _draw_section("Hero", "Hero", "Hero")
    _draw_section("GE", "GE", "GE")
    _draw_section("Lost Soul", "Lost Soul", "Lost Soul")
    _draw_section("Evil Character", "Evil Character", "Evil Character")
    _draw_section("EE", "EE", "EE")
    _draw_section("Artifact", ["Artifact", "Covenant", "Curse"], "Artifact")
    _draw_section("Fortress", ["Fortress", "Site", "City"], "Fortress")
    _draw_section("Misc", "misc", "Misc")

    place_section_by_type(
        c,
        reserve,
        height_points,
        card_types="all",
        x=section_mappings["lists"]["Reserve"]["x"],
        y=section_mappings["lists"]["Reserve"]["y"],
        add_quantity=False,
        color_alignment=color_alignment,
        sort_by=sort_by,
    )

    # Draw section counts (numbers only; positions are fully controlled)
    draw_count(
        c,
        main_deck,
        height_points,
        "Dominant",
        x=section_mappings["numbers"]["Dominant"]["x"],
        y=section_mappings["numbers"]["Dominant"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        "Hero",
        x=section_mappings["numbers"]["Hero"]["x"],
        y=section_mappings["numbers"]["Hero"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        "GE",
        x=section_mappings["numbers"]["GE"]["x"],
        y=section_mappings["numbers"]["GE"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        "Lost Soul",
        x=section_mappings["numbers"]["Lost Soul"]["x"],
        y=section_mappings["numbers"]["Lost Soul"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        "Evil Character",
        x=section_mappings["numbers"]["Evil Character"]["x"],
        y=section_mappings["numbers"]["Evil Character"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        "EE",
        x=section_mappings["numbers"]["EE"]["x"],
        y=section_mappings["numbers"]["EE"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        ["Artifact", "Covenant", "Curse"],
        x=section_mappings["numbers"]["Artifact"]["x"],
        y=section_mappings["numbers"]["Artifact"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        ["Fortress", "Site", "City"],
        x=section_mappings["numbers"]["Fortress"]["x"],
        y=section_mappings["numbers"]["Fortress"]["y"],
    )
    draw_count(
        c,
        main_deck,
        height_points,
        "misc",
        x=section_mappings["numbers"]["Misc"]["x"],
        y=section_mappings["numbers"]["Misc"]["y"],
    )
    draw_count(
        c,
        reserve,
        height_points,
        card_types="all",
        x=section_mappings["numbers"]["Reserve"]["x"],
        y=section_mappings["numbers"]["Reserve"]["y"],
    )

    # Draw total card count in the top right corner
    box_width = 50
    box_height = 30
    right_margin = 41
    top_margin = 97
    total_main = sum(int(card.get("quantity", 1)) for card in main_deck.values())
    c.setFont("Helvetica-Bold", 18)
    c.drawString(
        width_points - right_margin - box_width + 5,
        height_points - top_margin - box_height + 10,
        f"{total_main}",
    )

    # Display M count above alignment area if provided
    if m_count_value is not None:
        box_width = 50
        box_height = 30
        right_margin = 85
        top_margin = 14
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(
            width_points - right_margin - box_width + 5,
            height_points - top_margin - box_height + 10,
            f"M Count: {m_count_value}",
        )

    # Display AoD count above M count if provided
    if aod_count_value is not None:
        box_width = 50
        box_height = 30
        right_margin = 85
        top_margin = 4  # Higher up, above M count
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(
            width_points - right_margin - box_width + 5,
            height_points - top_margin - box_height + 10,
            f"AoD Count: {aod_count_value}",
        )

    # Draw alignment counts only if show_alignment is True
    if show_alignment:
        # Draw good count in green
        box_width = 50
        box_height = 30
        right_margin = 85
        top_margin = 34
        total_good = 0
        for card in main_deck.values():
            if card.get("alignment") == "Good":
                total_good += card.get("quantity", 0)
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0, 0.5, 0)  # Green
        c.drawString(
            width_points - right_margin - box_width + 5,
            height_points - top_margin - box_height + 10,
            f"Good Count: {total_good}",
        )

        # Draw evil count in red
        box_width = 50
        box_height = 30
        right_margin = 85
        top_margin = 44
        total_evil = 0
        for card in main_deck.values():
            if card.get("alignment") == "Evil":
                total_evil += card.get("quantity", 0)
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.8, 0, 0)  # Red
        c.drawString(
            width_points - right_margin - box_width + 5,
            height_points - top_margin - box_height + 10,
            f"Evil Count: {total_evil}",
        )

        # Draw neutral count in gray
        box_width = 50
        box_height = 30
        right_margin = 85
        top_margin = 54
        total_neutral = 0
        for card in main_deck.values():
            if card.get("alignment") == "Neutral":
                total_neutral += card.get("quantity", 0)
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.3, 0.3, 0.3)  # Darker Gray (changed from 0.5, 0.5, 0.5)
        c.drawString(
            width_points - right_margin - box_width + 5,
            height_points - top_margin - box_height + 10,
            f"Neutral Count: {total_neutral}",
        )

        # Reset color to black for remaining text
        c.setFillColorRGB(0, 0, 0)

    # Add player name
    box_width = 50
    box_height = 30
    right_margin = 290
    top_margin = 16
    c.setFont("Times-Roman", 24)
    c.drawString(
        width_points - right_margin - box_width + 5,
        height_points - top_margin - box_height + 10,
        name,
    )

    # add event name
    box_width = 50
    box_height = 30
    right_margin = 290
    top_margin = 56
    c.setFont("Times-Roman", 20)  # Changed from Times-Bold to Times-Roman
    c.drawString(
        width_points - right_margin - box_width + 5,
        height_points - top_margin - box_height + 10,
        event,
    )

    c.showPage()

    if overflow_sections:
        draw_overflow_page(
            c, overflow_sections, width_points, height_points, name, event
        )
        c.showPage()

    c.save()

    overlay_pdf = PdfReader(temp_overlay)
    if overlay_pdf.pages:
        page.merge_page(overlay_pdf.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    # Append any overflow pages (they don't need template merging)
    for i in range(1, len(overlay_pdf.pages)):
        writer.add_page(overlay_pdf.pages[i])
    with open(output_path, "wb") as f:
        writer.write(f)

    # Clean up temp file
    if os.path.exists(temp_overlay):
        os.remove(temp_overlay)


if __name__ == "__main__":
    from src.utilities.decklist import Decklist

    deck_data = Decklist("tmp/decklist.txt", deck_type="type_2").to_json()
    make_pdf(
        "type_2",
        deck_data,
        "output_decklist",
        "Player Name",
        "Event Name",
        True,
        m_count_value=3.14,  # Example M count value
    )
    print("PDF generated successfully.")
