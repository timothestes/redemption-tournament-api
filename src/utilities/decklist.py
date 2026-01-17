import json
import random
import xml.etree.ElementTree as ET

from src.utilities.brigades import normalize_brigade_field
from src.utilities.vars import CARD_DATA_JSON_FILE


class Decklist:

    def __init__(
        self, deck_file_path: str, deck_type: str, bypass_assertions: bool = False
    ):
        self.card_data_path = CARD_DATA_JSON_FILE
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

        if bypass_assertions:
            # still keep some assertions
            if self.deck_size > 252:
                raise AssertionError(
                    "Please load a deck that contains 252 or less cards in the main deck."
                )
            if self.reserve_size > 20:
                raise AssertionError(
                    "Please load a deck that contains 20 or less cards in the reserve."
                )
            return
        if self.deck_size < 50:
            raise AssertionError(
                "Please load a deck that contains at least 50 cards in the main deck."
            )
        if self.deck_size > 252 and deck_type == "type_2":
            raise AssertionError(
                "Please load a deck that contains 252 or less cards in the main deck for type 2"
            )
        elif self.deck_size > 154 and deck_type == "type_1":
            raise AssertionError(
                "Please load a deck that contains 154 or less cards in the main deck for type 1"
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
        """Take the data found in 'card_data_path' and load it from JSONL format."""
        card_database = {}
        with open(self.card_data_path, "r", encoding="utf-8") as file:
            for line in file:
                if line.strip():  # Skip empty lines
                    card_data = json.loads(line.strip())
                    # Data is already processed in the JSONL file
                    # (keys lowercase, values stripped, apostrophes normalized)
                    card_name = card_data["name"]
                    card_database[card_name] = card_data

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
                    card_details["raw_brigade"] = card_details.get("brigade", "")
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

    def calculate_m_count(self) -> float:
        """
        Calculate the M count of the main deck.

        The M count represents the expected number of unique brigades when randomly
        drawing 8 non-lost soul cards from the deck.

        For example, if you draw 8 cards with brigades [Orange], [Purple], [Orange, Crimson],
        [Teal], [Orange], [Purple], [Orange], [Teal], the M count would be 4
        (Orange, Purple, Teal, Crimson).

        Returns:
            float: The expected number of unique brigades in a random 8-card draw.
                   Returns 0.0 if there are no non-lost soul cards in the deck.
        """

        # Get all non-lost soul cards with their brigades
        non_lost_soul_cards = []
        for card_name, card_data in self.mapped_main_deck_list.items():
            if card_data.get("type", "").lower() != "lost soul":
                quantity = card_data.get("quantity", 1)
                brigades = card_data.get("brigade", [])
                for _ in range(quantity):
                    non_lost_soul_cards.append(brigades)

        # If we have no non-lost soul cards, return 0
        if not non_lost_soul_cards:
            return 0.0

        # If we have fewer than 8 cards, use all available cards
        sample_size = min(8, len(non_lost_soul_cards))

        # Monte Carlo simulation to calculate expected unique brigades
        num_simulations = 10_000
        total_unique_brigades = 0

        for _ in range(num_simulations):
            # Randomly sample cards
            sampled_cards = random.sample(non_lost_soul_cards, sample_size)

            # Count unique brigades in this sample
            unique_brigades = set()
            for card_brigades in sampled_cards:
                unique_brigades.update(card_brigades)

            total_unique_brigades += len(unique_brigades)

        return round(total_unique_brigades / num_simulations, 2)

    def calculate_aod_count(self) -> float:
        """
        Calculate the AoD count of the main deck.

        The AoD count represents the average number of Daniel reference cards
        when randomly drawing the top 9 cards from the deck.

        Returns:
            float: The average number of Daniel reference cards in the top 9 cards.
                   Returns 0.0 if the deck has fewer than 9 cards.
        """
        # Build a list of all cards in the main deck with their references
        # Exclude "The Ancient of Days" card itself from the simulation
        all_cards = []
        for card_name, card_data in self.mapped_main_deck_list.items():
            # Skip The Ancient of Days card
            if card_name == "The Ancient of Days":
                continue

            quantity = card_data.get("quantity", 1)
            reference = card_data.get("reference", "")
            for _ in range(quantity):
                all_cards.append(reference)

        # If we have fewer than 9 cards, return 0
        if len(all_cards) < 9:
            return 0.0

        # Monte Carlo simulation to calculate average Daniel reference cards in top 9
        num_simulations = 10_000
        total_daniel_cards = 0

        for _ in range(num_simulations):
            # Shuffle the deck
            shuffled_deck = random.sample(all_cards, len(all_cards))

            # Check first 3 cards for any Daniel references
            first_3 = shuffled_deck[0:3]
            first_3_daniel = sum(1 for ref in first_3 if ref and "Daniel" in ref)

            # If no Daniel cards in first 3, AoD count is 0 for this simulation
            if first_3_daniel == 0:
                daniel_count = 0
            else:
                # If at least 1 Daniel in first 3, count all Daniel cards in top 9
                top_9_cards = shuffled_deck[0:9]
                daniel_count = sum(1 for ref in top_9_cards if ref and "Daniel" in ref)

            total_daniel_cards += daniel_count

        return round(total_daniel_cards / num_simulations, 2)
