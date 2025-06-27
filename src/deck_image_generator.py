import os
import tempfile
from uuid import uuid4

from src.utilities.config import str_to_bool
from src.utilities.decklist import Decklist
from src.utilities.text_to_webp import make_webp


def generate_webp(
    deck_data: str,
    deck_type: str,
    n_card_columns: int = 10,
):
    unique_filename = f"{str(uuid4())}"

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
        temp_file.write(deck_data)
        temp_file.flush()  # Ensure all data is written
        deck_data = Decklist(
            temp_file.name, deck_type=deck_type, bypass_assertions=True
        ).to_json()

    # Call make_webp and get the actual file path
    webp_file_path = make_webp(
        deck_type,
        deck_data,
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
