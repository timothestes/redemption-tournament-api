#!/usr/bin/env python3
"""
Script to convert carddata.txt (TSV format) to JSONL format.

This script reads the carddata.txt file and converts each row to a JSON object,
writing one JSON object per line to create a JSONL file.
"""

import csv
import json
import os
from typing import Any, Dict

# Get the project root directory (two levels up from this script)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
CARDDATA_INPUT_DIR = "/Applications/LackeyCCG/plugins/Redemption/sets/"
JSONL_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "carddata")


def normalize_apostrophes(text: str) -> str:
    """Replaces curly apostrophes with straight ones in the provided text."""
    return text.replace("\u2019", "'")


def convert_to_jsonl(input_path: str = None, output_path: str = None) -> None:
    """
    Convert the TSV carddata file to JSONL format.
    Each line in the output file will be a JSON object representing one card.

    Args:
        input_path: Path to the carddata.txt file (defaults to CARDDATA_INPUT_DIR/carddata.txt)
        output_path: Path where the JSONL file will be saved
                    (defaults to JSONL_OUTPUT_DIR/carddata.jsonl)
    """
    if input_path is None:
        input_path = os.path.join(CARDDATA_INPUT_DIR, "carddata.txt")
    if output_path is None:
        output_path = os.path.join(JSONL_OUTPUT_DIR, "carddata.jsonl")

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
        jsonl_path = os.path.join(JSONL_OUTPUT_DIR, "carddata.jsonl")

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

    # Show a sample card
    # if card_dict:
    # sample_card_name = next(iter(card_dict))
    # print(f"\nSample card ({sample_card_name}):")
    # print(json.dumps(card_dict[sample_card_name], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
