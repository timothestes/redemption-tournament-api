import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from config import str_to_bool
from routes import register_routes

load_dotenv()
app = Flask(__name__)
# TODO: fix CORS on prod
CORS(app, resources={r"/*": {"origins": "*"}})

register_routes(app)

if __name__ == "__main__":
    debug = str_to_bool(os.getenv("DEBUG", "False"))
    print(f"debug mode: {debug}")
    app.run(debug=debug)
