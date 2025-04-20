import csv
import json
import xml.etree.ElementTree as ET

from src.utilities.brigades import normalize_brigade_field


class Decklist:

    def __init__(self, deck_file_path: str, deck_type: str):
        self.card_data_path = "assets/carddata/carddata.txt"
        self.deck_file_path = deck_file_path
        self.main_deck_list = []
        self.reserve_list = []
        self.has_reserve = False
        self._load_file()
        self.card_data = self._load_card_data()
        self.mapped_main_deck_list = self._map_card_metadata(self.main_deck_list)
        self.mapped_reserve_list = self._map_card_metadata(self.reserve_list)
        self.deck_size = self._get_size_of(self.mapped_main_deck_list)
        self.reserve_size = self._get_size_of(self.mapped_reserve_list)
        self.deck_type = deck_type

        # self._save_json("tmp_reserve_list.json", self.mapped_reserve_list)
        # self._save_json("tmp_main_deck_list.json", self.mapped_main_deck_list)
        if self.deck_size < 50:
            raise AssertionError(
                "Please load a deck_file that contains at least 50 cards in the main deck."
            )
        if self.reserve_size > 10 and deck_type == "type_1":
            raise AssertionError(
                "Please load a deck that contains 10 or less cards in the reserve for type 1"
            )
        elif self.reserve_size > 15 and deck_type == "type_2":
            raise AssertionError(
                "Please load a deck that contains 15 or less cards in the reserve for type 2"
            )

    def _get_size_of(self, card_list: dict) -> int:
        n_cards = 0
        for card in card_list.values():
            n_cards += card["quantity"]
        return n_cards

    @staticmethod
    def normalize_apostrophes(text):
        """Replaces curly apostrophes with straight ones in the provided text."""
        return text.replace("\u2019", "'")

    def _save_json(self, filename: str, dictionary_to_save: dict):
        """Debugging tool used to inspect json file.s"""
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(dictionary_to_save, file, ensure_ascii=False, indent=4)

    def _load_file(self):
        """Parse the .txt or .dek file into internal variables."""
        if self.deck_file_path.endswith(".dek"):
            self._load_dek_file()
        else:
            self._load_txt_file()

    def _load_dek_file(self):
        """Parse the .dek file into internal variables."""
        tree = ET.parse(self.deck_file_path)
        root = tree.getroot()

        for superzone in root.findall("superzone"):
            zone_name = superzone.get("name")
            if zone_name == "Tokens":
                continue  # Skip the Tokens superzone
            for card in superzone.findall("card"):
                card_name = card.find("name").text
                card_info = {
                    "quantity": 1,
                    "name": self.normalize_apostrophes(card_name.strip()),
                }
                if zone_name == "Reserve":
                    self.reserve_list.append(card_info)
                    self.has_reserve = True
                else:
                    self.main_deck_list.append(card_info)

        if len(self.main_deck_list) == 0:
            raise AssertionError(
                "Please load a deck_file that contains at least one card in the main deck."
            )

    def _load_txt_file(self):
        """Parse the .txt file into internal variables."""
        with open(self.deck_file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("Tokens:"):
                    break
                if line.startswith("Reserve:"):
                    self.has_reserve = True
                    continue

                parts = line.split("\t", 1)
                if len(parts) > 1:
                    card_info = {
                        "quantity": int(parts[0].strip()),
                        "name": self.normalize_apostrophes(parts[1].strip()),
                    }
                    if self.has_reserve:
                        self.reserve_list.append(card_info)
                    else:
                        self.main_deck_list.append(card_info)

        if len(self.main_deck_list) == 0:
            raise AssertionError(
                "Please load a deck_file that contains at least one card in the main deck."
            )

    def _load_card_data(self) -> dict:
        """Take the data found in 'card_data_path' and load it into a csv."""
        card_database = {}
        with open(self.card_data_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                # Create a new dictionary with all keys converted to lower case
                row_with_lower_keys = {key.lower(): value for key, value in row.items()}
                normalized_name = self.normalize_apostrophes(
                    row_with_lower_keys["name"]
                )
                card_database[normalized_name] = row_with_lower_keys

        return card_database

    def _map_card_metadata(self, card_list: list[dict]) -> dict:
        """
        Maps the names of each card to the full card data from the loaded card database.

        Parameters:
            cards (list of dict): List of dictionaries where each dict contains the 'quantity' and
              'name' of the card.

        Returns:
            dict: Dictionary where keys are card names and values are dictionaries of card data
            including quantity.
        """
        result = {}
        for card in card_list:
            card_name = card["name"].replace('""', '"').strip('"')
            quantity = card["quantity"]
            if card_name in self.card_data:
                if card_name in result:
                    result[card_name]["quantity"] += quantity
                else:
                    # Copy the card data to avoid mutating the original data.
                    card_details = self.card_data[card_name].copy()
                    card_details["quantity"] = quantity
                    # brigade normalization
                    card_details["brigade"] = normalize_brigade_field(
                        brigade=card_details.get("brigade", ""),
                        alignment=card_details.get("alignment", ""),
                        card_name=card["name"],
                    )
                    result[card_name] = card_details
            else:
                print(f"Could not find {card['name']}. Skipping loading it.")

        return result

    def to_json(self) -> dict:
        return {
            "main_deck": self.mapped_main_deck_list,
            "deck_size": self._get_size_of(self.mapped_main_deck_list),
            "reserve": self.mapped_reserve_list,
            "reserve_size": self._get_size_of(self.mapped_reserve_list),
        }
