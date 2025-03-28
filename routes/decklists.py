import os
import traceback

from dotenv import load_dotenv
from flask import Blueprint, jsonify
from supabase import Client, create_client

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL_V2")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_V2")

# Initialize the official Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

decklists_bp = Blueprint("buckets", __name__)


@decklists_bp.route("/list-buckets", methods=["GET"])
def list_buckets():
    """
    List all storage buckets using the official Supabase Python client.
    """
    try:
        buckets = supabase.storage.list_buckets()
        return jsonify(buckets), 200
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"error": str(e), "traceback": tb}), 500
