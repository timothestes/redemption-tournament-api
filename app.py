import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from client import supabase

load_dotenv()
app = Flask(__name__)

# CORS(app, resources={r"/*": {"origins": os.environ["ALLOWED_ORIGIN"]}})
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def home():
    return "home"


@app.route("/about")
def about():
    return "About this!"


@app.route("/api/save-user-data", methods=["POST"])
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

        if response.data:  # Successful insertion
            return jsonify({"message": "User data saved successfully"}), 201

    except Exception as e:
        error_message = str(e)
        if "duplicate key value violates unique constraint" in str(error_message):
            return jsonify({"error": "This email is already registered."}), 409
        print(f"Unexpected error saving user data: {error_message}")
        return jsonify({"error": "An unexpected error occurred."}), 500


if __name__ == "__main__":
    app.run(debug=False)

# https://redemption-tournament-tracker.vercel.app
# https://redemption-tournament-tracker.vercel.app
