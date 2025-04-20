import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from routes import register_routes
from src.utilities.config import str_to_bool

load_dotenv()
app = Flask(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development frontend
    "http://localhost:5000",  # Local development API
    "https://redemption-tournament-tracker.vercel.app",  # Production frontend
]

CORS(
    app,
    resources={
        r"/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)

register_routes(app)

if __name__ == "__main__":
    debug = str_to_bool(os.getenv("DEBUG", "False"))
    print(f"debug mode: {debug}")
    app.run(debug=debug)
