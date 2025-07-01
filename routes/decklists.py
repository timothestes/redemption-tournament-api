import datetime
import os
import traceback

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

from src.deck_generators import generate_pdf

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL_V2")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_V2")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

decklists_bp = Blueprint("decklists", __name__)


@decklists_bp.route("/generate-decklist", methods=["POST"])
def generate_decklist():
    """Take a deck payload and return a link to a deck check pdf."""
    file_path = None
    try:
        if not request.is_json:
            return jsonify({"error": "invalid request"}), 400

        data = request.get_json()
        if "decklist" not in data or "decklist_type" not in data:
            return jsonify({"error": "invalid request"}), 400

        # with open("decklist.txt", "w") as f:
        #     f.write(data["decklist"])
        # Generate PDF
        filename, file_path = generate_pdf(
            data["decklist"],
            data["decklist_type"],
            data["name"],
            data["event"],
            show_alignment=data.get("show_alignment", False),
            m_count=data.get("m_count", False),
        )

        # Upload to Supabase
        with open(file_path, "rb") as pdf_file:
            supabase.storage.from_("decklists").upload(
                path=filename,
                file=pdf_file,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )

        # Get public URL
        public_url = supabase.storage.from_("decklists").get_public_url(filename)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "decklist generated successfully",
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
