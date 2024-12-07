from flask import Flask, jsonify, request
from flask_cors import CORS

from client import supabase

app = Flask(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://redemption-tournament-tracker.vercel.app",
]
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})


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

        if response.status_code == 201:
            print("User data saved successfully (201)")
            return jsonify({"message": "User data saved successfully"}), 201
        else:
            print("Failed to save data (status code not 201)")
            return jsonify({"error": "Failed to save user data"}), 400

    except Exception as e:
        error_message = str(e)
        print(f"Error saving user data: {error_message}")

        if "duplicate key value violates unique constraint" in error_message:
            return jsonify({"error": "This email is already registered."}), 409

        return jsonify({"error": "An unexpected error occurred."}), 500


if __name__ == "__main__":
    app.run(debug=True)
