import os
import tempfile
from uuid import uuid4

from src.utilities.config import str_to_bool
from src.utilities.decklist import Decklist
from src.utilities.text_to_pdf import make_pdf


def generate_pdf(
    deck_data: str,
    deck_type: str,
    name: str,
    event: str,
    show_alignment: bool,
):
    unique_filename = f"{str(uuid4())}"

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
        temp_file.write(deck_data)
        temp_file.flush()  # Ensure all data is written
        deck_data = Decklist(temp_file.name, deck_type=deck_type).to_json()

    make_pdf(
        deck_type,
        deck_data,
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
