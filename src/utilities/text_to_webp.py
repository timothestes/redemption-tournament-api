import os

import dotenv
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw

from src.utilities.config import str_to_bool

dotenv.load_dotenv()
DECKLIST_IMAGES_FOLDER = "assets/setimages/general"


def make_webp(
    deck_type: str,
    deck_data: dict,
    filename: str,
    n_card_columns: int = 10,
):
    """
    Create a WebP image from deck data.

    Args:
        deck_type (str): Type of deck ('type_1' or 'type_2')
        deck_data (dict): Dictionary containing deck data with 'main_deck' and 'reserve' keys
        n_card_columns (int): Number of card columns per row (default: 10)
        filename (str): Base filename for output (default: "deck_output")

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
        deck_data, "main_deck", main_deck_filename, cards_per_row, output_dir
    )

    # Generate reserve deck image
    reserve_deck_image_path = _generate_deck_image(
        deck_data, "reserve", reserve_deck_filename, cards_per_row, output_dir
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
) -> str:
    """Generate an image for the specified deck (either 'main_deck' or 'reserve')."""
    if cards_per_row == 0:
        cards_per_row = 10

    # Get the deck data
    deck = deck_data.get(deck_key, {})
    if not deck:
        print(f"No data found for '{deck_key}' deck.")
        return None

    # Expand deck items by quantity
    expanded_deck_items = []
    for card_key, card_data in deck.items():
        for _ in range(card_data.get("quantity", 1)):
            expanded_deck_items.append((card_key, card_data))

    if not expanded_deck_items:
        print(f"No cards found in '{deck_key}' deck.")
        return None

    # Sort the deck by 'type' alphabetically
    sorted_deck_items = sorted(
        expanded_deck_items, key=lambda item: item[1].get("type", "")
    )

    # Load the first card image to determine the size for consistent dimensions
    sample_image_path = os.path.join(
        DECKLIST_IMAGES_FOLDER, sorted_deck_items[0][1]["imagefile"]
    )

    # Ensure the image has the correct extension
    if not sample_image_path.lower().endswith(".jpg"):
        sample_image_path += ".jpg"

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

    for card_key, card_data in sorted_deck_items:
        image_file = card_data.get("imagefile", "")
        if not image_file:
            print(f"Warning: No image file specified for card '{card_key}'")
            continue

        # Ensure the image file has the correct extension
        if not image_file.lower().endswith(".jpg"):
            image_file += ".jpg"
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
