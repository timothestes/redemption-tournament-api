import datetime
import os
import traceback

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

from src.deck_image_generator import generate_webp

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL_V2")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_V2")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

decklist_images_bp = Blueprint("decklist-images", __name__)


@decklist_images_bp.route("/generate-decklist-image", methods=["POST"])
def generate_decklist():
    """Take a deck payload and return a link to a webp file."""
    file_path = None
    try:
        if not request.is_json:
            return jsonify({"error": "invalid request"}), 400

        data = request.get_json()
        if "decklist" not in data or "decklist_type" not in data:
            return jsonify({"error": "invalid request"}), 400

        # Generate WebP
        filename, file_path = generate_webp(
            data["decklist"],
            data["decklist_type"],
            n_card_columns=data.get("n_card_columns", 10),
        )

        # Upload to Supabase
        with open(file_path, "rb") as webp_file:
            supabase.storage.from_("decklists").upload(
                path=filename,
                file=webp_file,
                file_options={"content-type": "image/webp", "upsert": "true"},
            )

        # Get public URL
        public_url = supabase.storage.from_("decklists").get_public_url(filename)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "deck image generated successfully",
                    "data": {
                        "filename": filename,
                        "downloadUrl": public_url,
                        "createdAt": datetime.datetime.now().isoformat(),
                    },
                }
            ),
            201,
        )

    except AssertionError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        print(traceback.format_exc())
        return (
            jsonify({"status": "error", "message": "something unexpected happened"}),
            500,
        )
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
