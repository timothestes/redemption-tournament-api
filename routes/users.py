from flask import Blueprint, jsonify, request

from client import supabase

users_bp = Blueprint("users", __name__)


@users_bp.route("/api/save-user-data", methods=["POST"])
def save_user_data():
    data = request.json
    user_id = data.get("id")
    email = data.get("email")
    first_name = data.get("firstName")
    last_name = data.get("lastName")

    if not user_id or not email or not first_name or not last_name:
        return jsonify({"error": "All fields are required."}), 400

    try:
        response = (
            supabase.table("user_data")
            .insert(
                {
                    "user_id": user_id,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )
            .execute()
        )
        if response.data:
            return jsonify({"message": "User data saved successfully"}), 201
    except Exception as e:
        error_message = str(e)
        if "duplicate key value violates unique constraint" in error_message:
            return jsonify({"error": "This email is already registered."}), 409
        print(f"Unexpected error saving user data: {error_message}")
        return jsonify({"error": "An unexpected error occurred."}), 500
