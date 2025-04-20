import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS

from routes import register_routes
from src.utilities.config import str_to_bool

load_dotenv()
app = Flask(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "https://redemption-tournament-tracker.vercel.app",
]

# Configure CORS with more specific settings
CORS(
    app,
    resources={
        r"/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS", "HEAD"],
            "allow_headers": [
                "X-Requested-With",
                "Content-Type",
                "Accept",
                "Authorization",
            ],
            "supports_credentials": True,
            "max_age": 86400,
        }
    },
)


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        return response


register_routes(app)

if __name__ == "__main__":
    debug = str_to_bool(os.getenv("DEBUG", "False"))
    print(f"debug mode: {debug}")
    app.run(debug=debug)
