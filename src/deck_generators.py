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
        tuple: (unique_filename, processed_deck_data_json, decklist_object)
    """
    unique_filename = f"{str(uuid4())}"

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
        temp_file.write(deck_data)
        temp_file.flush()  # Ensure all data is written
        decklist_object = Decklist(
            temp_file.name, deck_type=deck_type, bypass_assertions=bypass_assertions
        )
        processed_deck_data = decklist_object.to_json()

    return unique_filename, processed_deck_data, decklist_object


def generate_webp(
    deck_data: str,
    deck_type: str,
    n_card_columns: int = 10,
    m_count: bool = False,
    aod_count: bool = False,
):
    """
    Generate a WebP image from deck data.

    Args:
        deck_data: Raw deck data string
        deck_type: Type of deck being processed
        n_card_columns: Number of card columns in the image
        m_count: Whether to include m_count in the image
        aod_count: Whether to include aod_count in the image

    Returns:
        tuple: (filename_with_extension, file_path)
    """
    # Process deck data using internal utility
    unique_filename, processed_deck_data, decklist_object = _process_deck_data(
        deck_data, deck_type, bypass_assertions=True
    )

    # Calculate M count if requested
    m_count_value = None
    if m_count:
        m_count_value = decklist_object.calculate_m_count()

    # Calculate AoD count if requested
    aod_count_value = None
    if aod_count:
        aod_count_value = decklist_object.calculate_aod_count()

    # Call make_webp and get the actual file path
    webp_file_path = make_webp(
        deck_type,
        processed_deck_data,
        filename=unique_filename,
        n_card_columns=n_card_columns,
        m_count_value=m_count_value,
        aod_count_value=aod_count_value,
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
    m_count: bool = False,
    aod_count: bool = False,
):
    """
    Generate a PDF from deck data.

    Args:
        deck_data: Raw deck data string
        deck_type: Type of deck being processed
        name: Player name for the PDF
        event: Event name for the PDF
        show_alignment: Whether to show alignment in the PDF
        m_count: Whether to include m_count in the PDF
        aod_count: Whether to include aod_count in the PDF

    Returns:
        tuple: (filename, file_path)
    """
    # Process deck data using internal utility
    unique_filename, processed_deck_data, decklist_object = _process_deck_data(
        deck_data, deck_type
    )

    # Calculate M count if requested
    m_count_value = None
    if m_count:
        m_count_value = decklist_object.calculate_m_count()

    # Calculate AoD count if requested
    aod_count_value = None
    if aod_count:
        aod_count_value = decklist_object.calculate_aod_count()

    make_pdf(
        deck_type,
        processed_deck_data,
        filename=unique_filename,
        name=name,
        event=event,
        show_alignment=show_alignment,
        m_count_value=m_count_value,
        aod_count_value=aod_count_value,
    )

    if str_to_bool(os.getenv("DEBUG")):
        output_dir = "tmp"
    else:
        output_dir = "/tmp"

    return (
        unique_filename,
        f"{output_dir}/{unique_filename}.pdf",
    )
