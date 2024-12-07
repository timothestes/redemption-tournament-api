from flask import Flask

from client import supabase

app = Flask(__name__)


@app.route("/")
def home():
    response = supabase.table("countries").select("*").execute()

    return str(response)


@app.route("/about")
def about():
    return "About this"


if __name__ == "__main__":
    app.run(debug=True)
