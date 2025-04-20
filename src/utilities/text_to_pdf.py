import os
import re

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

# Precompile regex patterns for efficiency.
SET_NAME_PATTERN = re.compile(r"(\([^)]*\))\s*$")
LOST_SOUL_PREFIX_PATTERN = re.compile(r"^Lost Soul\s+")
BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")
HYPHEN_PATTERN = re.compile(r"\s*-\s*[^]]+")


def clean_card_name(card_name, card_data):
    """
    Clean the card name.
    - If the name contains a '/', use the part before it and append any trailing set name in parentheses.
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


def place_section(c, section_data, x, y, line_spacing, add_quantity=True):
    """
    Place sorted items from section_data at (x, y) on the canvas.
    """
    for card_name, card_data in sorted(section_data.items(), key=lambda item: item[0]):
        display_name = clean_card_name(card_name, card_data)
        display_text = (
            f"{card_data.get('quantity', 1)}x {display_name}"
            if add_quantity
            else display_name
        )
        c.drawString(x, y, display_text)
        y -= line_spacing


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


def place_section_by_type(c, deck, height_points, card_types, x, y, add_quantity=True):
    """
    Filter main_deck by card_types and place the section.
    """
    y = height_points - y
    line_spacing = 16
    if isinstance(card_types, str):
        filtered = {k: v for k, v in deck.items() if v.get("type") == card_types}
    else:
        filtered = {k: v for k, v in deck.items() if v.get("type") in card_types}
    if card_types == "misc":
        filtered = {}
        for key, value in deck.items():
            if value.get("type") not in [
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
                filtered[key] = value
    elif card_types == "all":
        filtered = deck
    place_section(c, filtered, x, y, line_spacing, add_quantity)


def generate_decklist_pdf(deck_type: str, deck_data, filename: str):
    """
    Generate a deck check sheet overlay with card listings, section counts,
    and a total card count.
    """
    if deck_type == "type_1":
        template_path = "assets/pdfs/t1_deck_check.pdf"
    elif deck_type == "type_2":
        template_path = "assets/pdfs/t2_deck_check.pdf"

    # Create output directory if it doesn't exist
    os.makedirs("/tmp", exist_ok=True)

    # Use system temp directory for all temporary files
    output_path = os.path.join("/tmp", f"{filename}.pdf")
    temp_overlay = os.path.join("/tmp", f"temp_{filename}.pdf")

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

    # Draw card listings
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "Dominant",
        x=section_mappings["lists"]["Dominant"]["x"],
        y=section_mappings["lists"]["Dominant"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "Hero",
        x=section_mappings["lists"]["Hero"]["x"],
        y=section_mappings["lists"]["Hero"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "GE",
        x=section_mappings["lists"]["GE"]["x"],
        y=section_mappings["lists"]["GE"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "Lost Soul",
        x=section_mappings["lists"]["Lost Soul"]["x"],
        y=section_mappings["lists"]["Lost Soul"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "Evil Character",
        x=section_mappings["lists"]["Evil Character"]["x"],
        y=section_mappings["lists"]["Evil Character"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "EE",
        x=section_mappings["lists"]["EE"]["x"],
        y=section_mappings["lists"]["EE"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        ["Artifact", "Covenant", "Curse"],
        x=section_mappings["lists"]["Artifact"]["x"],
        y=section_mappings["lists"]["Artifact"]["y"],
    )
    place_section_by_type(
        c,
        main_deck,
        height_points,
        ["Fortress", "Site", "City"],
        x=section_mappings["lists"]["Fortress"]["x"],
        y=section_mappings["lists"]["Fortress"]["y"],
    )

    # Misc section (cards not fitting other types)
    place_section_by_type(
        c,
        main_deck,
        height_points,
        "misc",
        x=section_mappings["lists"]["Misc"]["x"],
        y=section_mappings["lists"]["Misc"]["y"],
    )
    # Reserve section (without quantity)
    place_section_by_type(
        c,
        reserve,
        height_points,
        card_types="all",
        x=section_mappings["lists"]["Reserve"]["x"],
        y=section_mappings["lists"]["Reserve"]["y"],
        add_quantity=False,
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

    # Draw good count
    box_width = 50
    box_height = 30
    right_margin = 85
    top_margin = 29
    total_good = 0
    for card in main_deck.values():
        if card.get("alignment") == "Good":
            total_good += card.get("quantity")
    c.setFont("Helvetica", 10)
    c.drawString(
        width_points - right_margin - box_width + 5,
        height_points - top_margin - box_height + 10,
        f"Good Count: {total_good}",
    )

    # Draw evil count
    box_width = 50
    box_height = 30
    right_margin = 85
    top_margin = 42
    total_evil = 0
    for card in main_deck.values():
        if card.get("alignment") == "Evil":
            total_evil += card.get("quantity")
    c.setFont("Helvetica", 10)
    c.drawString(
        width_points - right_margin - box_width + 5,
        height_points - top_margin - box_height + 10,
        f"Evil Count: {total_evil}",
    )

    # Draw neutral count
    box_width = 50
    box_height = 30
    right_margin = 85
    top_margin = 53
    total_neutral = 0
    for card in main_deck.values():
        if card.get("alignment") == "Neutral":
            total_neutral += card.get("quantity")
    c.setFont("Helvetica", 10)
    c.drawString(
        width_points - right_margin - box_width + 5,
        height_points - top_margin - box_height + 10,
        f"Neutral Count: {total_neutral}",
    )

    c.showPage()
    c.save()

    overlay_pdf = PdfReader(temp_overlay)
    if overlay_pdf.pages:
        page.merge_page(overlay_pdf.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)

    # Clean up temp file
    if os.path.exists(temp_overlay):
        os.remove(temp_overlay)


if __name__ == "__main__":
    import json

    with open("tmp/deck_data.json", "r") as f:
        deck_data = json.load(f)
    generate_decklist("type_1", deck_data, "output_decklist")
