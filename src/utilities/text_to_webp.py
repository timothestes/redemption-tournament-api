import json
import os
from typing import List, Union

import dotenv
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw

from src.utilities.config import str_to_bool
from src.utilities.sort import sort_cards
from src.utilities.vars import CARD_DATA_JSON_FILE

dotenv.load_dotenv()
DECKLIST_IMAGES_FOLDER = "assets/cardimages"


def load_carddata_filenames() -> set:
    """
    Load all image filenames from carddata.jsonl to preserve original naming.

    Returns:
        set: Set of original image filenames from carddata.jsonl
    """
    carddata_filenames = set()

    try:
        with open(CARD_DATA_JSON_FILE, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():  # Skip empty lines
                    continue

                # Parse JSON line and get the imagefile field
                try:
                    card_data = json.loads(line.strip())
                    image_filename = card_data.get("imagefile", "")
                    if image_filename:  # Only add non-empty filenames
                        carddata_filenames.add(image_filename)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {line[:50]}... - {e}")
                    continue

    except FileNotFoundError:
        print(f"Warning: {CARD_DATA_JSON_FILE} not found. Using fallback logic.")
    except Exception as e:
        print(f"Error reading {CARD_DATA_JSON_FILE}: {e}")

    return carddata_filenames


def normalize_filename_for_webp(original_filename: str, carddata_filenames: set) -> str:
    """
    Convert filename to WebP format, preserving original naming from carddata.jsonl.

    Args:
        original_filename (str): The original filename from deck data
            (e.g., "The-Judean-Mediums-Regional" or "The_Jeering_Youths_(RA)")
        carddata_filenames (set): Set of filenames from carddata.jsonl

    Returns:
        str: The WebP filename (e.g., "The-Judean-Mediums-Regional.jpg.webp" or
             "The_Jeering_Youths_(RA).webp")
    """
    # Look for this filename in carddata
    for carddata_name in carddata_filenames:
        # Check if the carddata name matches our original filename
        if carddata_name == original_filename:
            # Found exact match - this could be either case
            return f"{carddata_name}.webp"
        elif carddata_name == f"{original_filename}.jpg":
            # Edge case: carddata has the .jpg version
            return f"{carddata_name}.webp"

    # Fallback: if not found in carddata, just add .webp
    return f"{original_filename}.webp"


def make_webp(
    deck_type: str,
    deck_data: dict,
    filename: str,
    n_card_columns: int = 10,
    sort_by: Union[str, List[str]] = ["type", "alignment", "brigade", "name"],
):
    """
    Create a WebP image from deck data.

    Args:
        deck_type (str): Type of deck ('type_1' or 'type_2')
        deck_data (dict): Dictionary containing deck data with 'main_deck' and 'reserve' keys
        filename (str): Base filename for output
        n_card_columns (int): Number of card columns per row (default: 10)
        sort_by: Single field or list of fields to sort by.
                Available fields: 'alignment', 'brigade', 'type', 'name' (default: "type")

    Returns:
        str: Path to the generated WebP file
    """
    # Determine output directory based on DEBUG environment variable
    if str_to_bool(os.getenv("DEBUG")):
        output_dir = "tmp"
    else:
        output_dir = "/tmp"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set cards per row based on deck type
    cards_per_row = 15 if deck_type == "type_2" else n_card_columns

    # Generate individual deck images
    main_deck_filename = f"{filename}_main"
    reserve_deck_filename = f"{filename}_reserve"

    # Generate main deck image
    main_deck_image_path = _generate_deck_image(
        deck_data, "main_deck", main_deck_filename, cards_per_row, output_dir, sort_by
    )

    # Generate reserve deck image
    reserve_deck_image_path = _generate_deck_image(
        deck_data, "reserve", reserve_deck_filename, cards_per_row, output_dir, sort_by
    )

    # Combine images into final WebP
    combined_image_path = _combine_deck_images(
        main_deck_image_path, reserve_deck_image_path, filename, output_dir
    )

    # Clean up individual images
    _cleanup_individual_images(main_deck_image_path, reserve_deck_image_path)

    return combined_image_path


def _generate_deck_image(
    deck_data: dict,
    deck_key: str,
    output_filename: str,
    cards_per_row: int,
    output_dir: str,
    sort_by: Union[str, List[str]] = ["type", "alignment", "brigade", "name"],
) -> str:
    """Generate an image for the specified deck (either 'main_deck' or 'reserve')."""
    if cards_per_row == 0:
        cards_per_row = 10

    # Get the deck data
    deck = deck_data.get(deck_key, {})
    if not deck:
        print(f"No data found for '{deck_key}' deck.")
        return None

    # Use the sorting utility to sort cards
    sorted_deck_items = sort_cards(deck, sort_by)

    # Expand deck items by quantity
    expanded_deck_items = []
    for card_key, card_data in sorted_deck_items:
        for _ in range(card_data.get("quantity", 1)):
            expanded_deck_items.append((card_key, card_data))

    if not expanded_deck_items:
        print(f"No cards found in '{deck_key}' deck.")
        return None

    # Load carddata filenames for proper filename handling
    carddata_filenames = load_carddata_filenames()

    # Load the first card image to determine the size for consistent dimensions
    sample_image_filename = expanded_deck_items[0][1]["imagefile"]
    normalized_sample_filename = normalize_filename_for_webp(
        sample_image_filename, carddata_filenames
    )
    sample_image_path = os.path.join(DECKLIST_IMAGES_FOLDER, normalized_sample_filename)

    try:
        sample_image = Image.open(sample_image_path)
        card_width, card_height = sample_image.size
    except Exception as e:
        print(f"Error loading sample image {sample_image_path}: {e}")
        # Use default dimensions if sample image fails
        card_width, card_height = 315, 441

    # Set overlap amount to 10% of card height
    card_overlap = int(card_height * 0.10)

    # Calculate output image dimensions based on the number of cards, considering the overlap
    num_cards = len(expanded_deck_items)
    rows = (num_cards + cards_per_row - 1) // cards_per_row
    output_width = card_width * cards_per_row
    output_height = (card_height * rows) - (card_overlap * (rows - 1))

    # Create a blank canvas of the correct size with the background color
    background_color = (30, 32, 43)  # RGB for #1e202b
    output_image = Image.new("RGB", (output_width, output_height), background_color)

    # Track positioning for placing card images on the canvas
    x_offset, y_offset = 0, 0

    for card_key, card_data in expanded_deck_items:
        image_file = card_data.get("imagefile", "")
        if not image_file:
            print(f"Warning: No image file specified for card '{card_key}'")
            continue

        # Normalize the image filename using carddata information
        image_file = normalize_filename_for_webp(image_file, carddata_filenames)

        card_image_path = os.path.join(DECKLIST_IMAGES_FOLDER, image_file)

        try:
            card_image = Image.open(card_image_path)

            # Ensure the card image has the same mode as the output canvas
            if card_image.mode != output_image.mode:
                card_image = card_image.convert(output_image.mode)

            # Paste the card image directly without resizing to preserve quality
            output_image.paste(card_image, (x_offset, y_offset))

            # Update x_offset, and wrap to the next row if necessary
            x_offset += card_width
            if x_offset >= output_width:
                x_offset = 0
                y_offset += card_height - card_overlap
        except FileNotFoundError:
            print(
                f"Warning: Image for card '{card_key}' not found at {card_image_path}"
            )
        except Exception as e:
            print(f"Error processing card '{card_key}': {e}")

    # Save the generated deck image as WebP
    output_image_path = os.path.join(output_dir, f"{output_filename}.webp")
    output_image.save(output_image_path, format="WEBP", quality=80, optimize=True)
    print(f"Deck image saved to {output_image_path}")
    return output_image_path


def _combine_deck_images(
    main_deck_image_path: str,
    reserve_deck_image_path: str,
    output_filename: str,
    output_dir: str,
) -> str:
    """
    Combine the main deck and reserve deck images into a single image,
    adding a line and padding between them.
    """
    if not main_deck_image_path or not os.path.exists(main_deck_image_path):
        print("Warning: Main deck image not found")
        return None

    # Load the main deck image
    main_deck_image = Image.open(main_deck_image_path)

    # Check if reserve deck image exists
    reserve_deck_image = None
    if reserve_deck_image_path and os.path.exists(reserve_deck_image_path):
        reserve_deck_image = Image.open(reserve_deck_image_path)

    # If no reserve deck, just return the main deck image
    if not reserve_deck_image:
        combined_image_path = os.path.join(output_dir, f"{output_filename}.webp")
        main_deck_image.save(
            combined_image_path, format="WEBP", quality=80, optimize=True
        )
        return combined_image_path

    # Set line height for the separator line
    line_height = 50
    # Set padding between main deck and reserve deck
    padding = 50

    # Calculate the combined image size
    combined_width = max(main_deck_image.width, reserve_deck_image.width)
    combined_height = (
        main_deck_image.height + reserve_deck_image.height + line_height + padding
    )

    # Create a blank canvas for the combined image with the background color
    background_color = (30, 32, 43)  # RGB for #1e202b
    combined_image = Image.new(
        "RGB", (combined_width, combined_height), background_color
    )

    # Paste the main deck image at the top
    combined_image.paste(main_deck_image, (0, 0))

    # Draw a separator line below the main deck image
    draw = ImageDraw.Draw(combined_image)
    line_color = (20, 22, 33)
    line_y_start = main_deck_image.height + (line_height // 2)
    draw.line(
        (0, line_y_start, combined_width, line_y_start),
        fill=line_color,
        width=line_height,
    )

    # Paste the reserve deck image below the line, with added padding
    reserve_y_offset = main_deck_image.height + line_height + padding
    combined_image.paste(reserve_deck_image, (0, reserve_y_offset))

    # Save the combined image using WebP optimization
    combined_image_path = os.path.join(output_dir, f"{output_filename}.webp")
    combined_image.save(combined_image_path, format="WEBP", quality=80, optimize=True)

    file_size_mb = os.path.getsize(combined_image_path) / (1024 * 1024)
    print(f"Combined deck image saved to {combined_image_path}")
    print(f"File size: {file_size_mb:.2f}MB")

    return combined_image_path


def _cleanup_individual_images(main_deck_image_path: str, reserve_deck_image_path: str):
    """Delete the individual deck images after combining."""
    try:
        if main_deck_image_path and os.path.exists(main_deck_image_path):
            os.remove(main_deck_image_path)
            print(f"Deleted main deck image: {main_deck_image_path}")
        if reserve_deck_image_path and os.path.exists(reserve_deck_image_path):
            os.remove(reserve_deck_image_path)
            print(f"Deleted reserve deck image: {reserve_deck_image_path}")
    except OSError as e:
        print(f"Error deleting individual deck images: {e}")


def normalize_image_filename(filename: str) -> str:
    """
    Normalize an image filename to find the correct WebP file.
    Handles cases where filenames might have .jpg extensions that need to be removed.

    Examples:
        'The-Judean-Mediums-Regional.jpg' -> 'The-Judean-Mediums-Regional.webp'
        'Holy-Grail' -> 'Holy-Grail.webp'
        '006-Holy-Grail.jpg' -> '006-Holy-Grail.webp'

    Args:
        filename (str): The original filename from the card data

    Returns:
        str: Normalized filename with .webp extension
    """
    # Remove common image extensions
    extensions_to_remove = [
        ".jpg",
        ".jpeg",
        ".JPG",
        ".JPEG",
        ".png",
        ".PNG",
        ".webp",
        ".WEBP",
    ]

    normalized = filename
    for ext in extensions_to_remove:
        if normalized.endswith(ext):
            normalized = normalized[: -len(ext)]
            break

    # Add .webp extension
    return f"{normalized}.webp"
