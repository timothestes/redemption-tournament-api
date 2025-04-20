import tempfile
from uuid import uuid4

from src.utilities.decklist import Decklist
from src.utilities.text_to_pdf import generate_decklist


def generate_pdf(deck_data: str, deck_type: str):
    unique_filename = f"{str(uuid4())}"

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
        temp_file.write(deck_data)
        temp_file.flush()  # Ensure all data is written
        deck_data = Decklist(temp_file.name, deck_type=deck_type).to_json()

    generate_decklist(deck_type, deck_data, filename=unique_filename)

    return (
        unique_filename,
        f"tmp/{unique_filename}.pdf",
    )
