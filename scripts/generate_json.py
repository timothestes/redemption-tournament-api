#!/usr/bin/env python3
"""
Script to convert carddata.txt (TSV format) to JSONL format.

This script reads the carddata.txt file and converts each row to a JSON object,
writing one JSON object per line to create a JSONL file.
"""

import csv
import json
from typing import Any, Dict

from src.utilities.vars import CARD_DATA_JSON_FILE, CARDDATA_FILE


def normalize_apostrophes(text: str) -> str:
    """Replaces curly apostrophes with straight ones in the provided text."""
    return text.replace("\u2019", "'")


def convert_to_jsonl() -> None:
    """
    Convert the TSV carddata file to JSONL format.
    Each line in the output file will be a JSON object representing one card.
    """
    input_path = CARDDATA_FILE
    output_path = CARD_DATA_JSON_FILE

    cards_processed = 0

    try:
        with open(input_path, "r", newline="", encoding="utf-8") as input_file:
            with open(output_path, "w", encoding="utf-8") as output_file:
                reader = csv.DictReader(input_file, delimiter="\t")

                for row in reader:
                    # Process the row similar to how it's done in decklist.py
                    card_data = {}

                    for key, value in row.items():
                        # Convert keys to lowercase and strip whitespace from values
                        clean_key = key.lower().strip()
                        clean_value = value.strip() if value else ""

                        # Normalize apostrophes in text fields
                        if isinstance(clean_value, str):
                            clean_value = normalize_apostrophes(clean_value)

                        card_data[clean_key] = clean_value

                    # Write the JSON object as a single line
                    json.dump(card_data, output_file, ensure_ascii=False)
                    output_file.write("\n")
                    cards_processed += 1

    except FileNotFoundError:
        print(f"Error: Could not find input file at {input_path}")
        return
    except Exception as e:
        print(f"Error processing file: {e}")
        return

    print(f"Successfully converted {cards_processed} cards to JSONL format.")
    print(f"Output saved to: {output_path}")


def load_jsonl_as_dict(jsonl_path: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Load the JSONL file and return it as a dictionary keyed by card name.
    This function can be used to verify the conversion or for other processing.

    Args:
        jsonl_path: Path to the JSONL file (defaults to JSONL_OUTPUT_DIR/carddata.jsonl)

    Returns:
        Dictionary where keys are card names and values are card data dictionaries
    """
    if jsonl_path is None:
        jsonl_path = CARD_DATA_JSON_FILE

    card_database = {}

    try:
        with open(jsonl_path, "r", encoding="utf-8") as file:
            for line in file:
                card_data = json.loads(line.strip())
                if "name" in card_data:
                    normalized_name = normalize_apostrophes(card_data["name"])
                    card_database[normalized_name] = card_data

    except FileNotFoundError:
        print(f"Error: Could not find JSONL file at {jsonl_path}")
        return {}
    except Exception as e:
        print(f"Error reading JSONL file: {e}")
        return {}

    return card_database


def main():
    """Main function to run the converter."""
    print("Converting carddata.txt to JSONL format...")

    # Convert the file
    convert_to_jsonl()

    # Optional: Load and verify the conversion
    print("\nVerifying conversion...")
    card_dict = load_jsonl_as_dict()
    print(f"Loaded {len(card_dict)} cards from JSONL file.")


if __name__ == "__main__":
    main()
