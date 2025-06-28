import os
import tempfile
from uuid import uuid4

from src.utilities.config import str_to_bool
from src.utilities.decklist import Decklist
from src.utilities.text_to_pdf import make_pdf
from src.utilities.text_to_webp import make_webp


def _process_deck_data(deck_data: str, deck_type: str, bypass_assertions: bool = False):
    """
    Internal utility to process deck data into a Decklist JSON format.

    Args:
        deck_data: Raw deck data string
        deck_type: Type of deck being processed
        bypass_assertions: Whether to bypass assertions in Decklist creation

    Returns:
        tuple: (unique_filename, processed_deck_data_json)
    """
    unique_filename = f"{str(uuid4())}"

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
        temp_file.write(deck_data)
        temp_file.flush()  # Ensure all data is written
        processed_deck_data = Decklist(
            temp_file.name, deck_type=deck_type, bypass_assertions=bypass_assertions
        ).to_json()

    return unique_filename, processed_deck_data


def generate_webp(
    deck_data: str,
    deck_type: str,
    n_card_columns: int = 10,
):
    """
    Generate a WebP image from deck data.

    Args:
        deck_data: Raw deck data string
        deck_type: Type of deck being processed
        n_card_columns: Number of card columns in the image

    Returns:
        tuple: (filename_with_extension, file_path)
    """
    # Process deck data using internal utility
    unique_filename, processed_deck_data = _process_deck_data(
        deck_data, deck_type, bypass_assertions=True
    )

    # Call make_webp and get the actual file path
    webp_file_path = make_webp(
        deck_type,
        processed_deck_data,
        filename=unique_filename,
        n_card_columns=n_card_columns,
    )

    if not webp_file_path or not os.path.exists(webp_file_path):
        raise ValueError("Failed to generate deck image")

    # Return filename with extension and the actual file path
    return (
        f"{unique_filename}.webp",
        webp_file_path,
    )


def generate_pdf(
    deck_data: str,
    deck_type: str,
    name: str,
    event: str,
    show_alignment: bool,
):
    """
    Generate a PDF from deck data.

    Args:
        deck_data: Raw deck data string
        deck_type: Type of deck being processed
        name: Player name for the PDF
        event: Event name for the PDF
        show_alignment: Whether to show alignment in the PDF

    Returns:
        tuple: (filename, file_path)
    """
    # Process deck data using internal utility
    unique_filename, processed_deck_data = _process_deck_data(deck_data, deck_type)

    make_pdf(
        deck_type,
        processed_deck_data,
        filename=unique_filename,
        name=name,
        event=event,
        show_alignment=show_alignment,
    )

    if str_to_bool(os.getenv("DEBUG")):
        output_dir = "tmp"
    else:
        output_dir = "/tmp"

    return (
        unique_filename,
        f"{output_dir}/{unique_filename}.pdf",
    )
