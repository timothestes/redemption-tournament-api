from src.utilities.vars import EVIL_BRIGADES, GOOD_BRIGADES


def handle_complex_brigades(card_name: str, brigade: str) -> list:
    complex_brigades = {
        "Delivered": ["Green", "Teal", "Evil Gold", "Pale Green"],
        "Eternal Judgment": ["Green", "White", "Brown", "Crimson"],
        "Scapegoat (PoC)": ["Teal", "Green", "Crimson"],
        "Zion": ["Purple"],
        "Ashkelon": ["Good Gold"],
        "Raamses": ["White"],
        "Babel (FoM)": ["Blue"],
        "Sodom & Gomorrah": ["Silver"],
        "City of Enoch": ["Blue"],
        "Hebron": ["Red"],
        "Damascus (LoC)": ["Red"],
        "Damascus (Promo)": ["Red"],
        "Bethlehem (Promo)": ["White"],
        "Samaria": ["Green"],
        "Nineveh": ["Green"],
        "City of Refuge": ["Teal"],
        "Jerusalem (GoC)": ["Purple", "Good Gold", "White"],
        "Sychar (GoC)": ["Good Gold", "Purple"],
        "Fire Foxes": ["Good Gold", "Crimson", "Black"],
        "Bethlehem (LoC)": ["Good Gold", "White"],
        "New Jerusalem (Bride of Christ) (RoJ AB)": GOOD_BRIGADES,
        "Doubt (LoC Plus)": [],
        "Doubt (LoC)": [],
        "Angel of God [2023 - National]": [],
        "City of Refuge (PoC)": ["Teal"],
        "Fullness of Time": [],
        "Melchizedek (CoW AB)": ["Purple", "Teal"],
        "Philistine Outpost": [],
        "Philosophy": GOOD_BRIGADES + EVIL_BRIGADES,
        "Unified Language": GOOD_BRIGADES + EVIL_BRIGADES,
        "Saul/Paul": ["Gray"] + GOOD_BRIGADES,
        "Coat of Many Colors (FoM)": ["Brown"] + GOOD_BRIGADES,
    }
    if card_name in complex_brigades:
        return complex_brigades[card_name]
    else:
        return handle_simple_brigades(brigade)


def handle_simple_brigades(brigade: str) -> list:
    if "and" in brigade:
        return brigade.split("and")[0].strip().split("/")
    if "(" in brigade:
        main_brigade, sub_brigades = brigade.split(" (")
        sub_brigades = sub_brigades.rstrip(")").split("/")
        return main_brigade.strip().split("/") + sub_brigades
    if "/" in brigade:
        return brigade.split("/")
    return [brigade]


def replace_brigades(brigades, target, replacement):
    return [replacement if b == target else b for b in brigades]


def replace_multi_brigades(brigades_list: list) -> list:
    if "Good Multi" in brigades_list:
        brigades_list = [b for b in brigades_list if b != "Good Multi"]
        brigades_list.extend(GOOD_BRIGADES)
    if "Evil Multi" in brigades_list:
        brigades_list = [b for b in brigades_list if b != "Evil Multi"]
        brigades_list.extend(EVIL_BRIGADES)
    return brigades_list


def handle_gold_brigade(card_name, alignment, brigades_list):
    gold_replacement = {
        "Good": "Good Gold",
        "Evil": "Evil Gold",
        "Neutral": (
            "Good Gold"
            if brigades_list[0] == "Gold"
            or card_name
            in ["First Bowl of Wrath (RoJ)", "Banks of the Nile/Pharaoh's Court"]
            else "Evil Gold"
        ),
        None: "Good Gold",
    }
    return replace_brigades(brigades_list, "Gold", gold_replacement.get(alignment))


def normalize_brigade_field(brigade: str, alignment: str, card_name: str) -> list:
    if not brigade:
        return []

    brigades_list = handle_complex_brigades(card_name, brigade)
    if "Multi" in brigades_list:
        multi_replacements = {
            "Good": "Good Multi",
            "Evil": "Evil Multi",
            "Neutral": "Good Multi",
        }
        brigades_list = replace_brigades(
            brigades_list,
            "Multi",
            multi_replacements.get(card_name, multi_replacements.get(alignment)),
        )
    if "Gold" in brigades_list:
        brigades_list = handle_gold_brigade(card_name, alignment, brigades_list)

    brigades_list = replace_multi_brigades(brigades_list)
    allowed_brigades = set(GOOD_BRIGADES + EVIL_BRIGADES)
    for brigade in brigades_list:
        assert (
            brigade in allowed_brigades
        ), f"Card {card_name} has an invalid brigade: {brigade}."

    return sorted(brigades_list)
