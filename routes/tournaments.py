import random

from flask import Blueprint, jsonify, request

from client import supabase

tournaments_bp = Blueprint("tournaments", __name__)


def generate_code():
    return f"{random.randint(0, 9999):04d}"


@tournaments_bp.route("/tournaments", methods=["POST"])
def create_tournament():
    """Create a new tournament."""
    data = request.json
    host_id = data.get("host_id")
    name = data.get("name")
    description = data.get("description")
    settings = data.get("settings", {})

    if not host_id or not name:
        return jsonify({"error": "host_id and name are required."}), 400

    max_retries = 5
    for _ in range(max_retries):
        code = generate_code()
        try:
            response = (
                supabase.table("tournaments")
                .insert(
                    {
                        "host_id": host_id,
                        "name": name,
                        "description": description,
                        "settings": settings,
                        "code": code,
                    }
                )
                .execute()
            )
            return jsonify(response.data[0]), 201
        except Exception as e:
            error_message = str(e).lower()
            if "duplicate key" in error_message or "unique constraint" in error_message:
                continue  # Try a new code
            print(e)
            return jsonify({"error": str(e)}), 400

    return (
        jsonify({"error": "Failed to generate a unique code after multiple attempts."}),
        400,
    )


@tournaments_bp.route("/tournaments", methods=["GET"])
def list_tournaments():
    """List tournaments with participant counts, optionally filtered by host_id."""
    host_id = request.args.get("host_id")

    # Base query to get tournaments
    query = supabase.table("tournaments").select("*")
    if host_id:
        query = query.eq("host_id", host_id)

    try:
        # Fetch tournaments
        tournaments_response = query.execute()
        tournaments = tournaments_response.data

        if not tournaments:
            return jsonify([]), 200

        # Fetch participant counts using the RPC function
        participant_counts_response = supabase.rpc(
            "get_tournament_participant_counts"
        ).execute()
        participant_counts = {
            item["tournament_id"]: item["participant_count"]
            for item in participant_counts_response.data
        }

        # Add participant counts to each tournament
        for tournament in tournaments:
            tournament["participant_count"] = participant_counts.get(
                tournament["id"], 0
            )

        return jsonify(tournaments), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@tournaments_bp.route("/tournaments/<tournament_id>", methods=["PUT"])
def update_tournament(tournament_id):
    """Update a tournament."""
    data = request.json
    fields = {
        k: v
        for k, v in data.items()
        if k in ["name", "description", "settings", "status"]
    }
    if not fields:
        return jsonify({"error": "No valid fields to update."}), 400

    try:
        response = (
            supabase.table("tournaments")
            .update(fields)
            .eq("id", tournament_id)
            .execute()
        )
        if response.data:
            return jsonify(response.data[0]), 200
        return jsonify({"error": "Tournament not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@tournaments_bp.route("/tournaments/<tournament_id>", methods=["DELETE"])
def delete_tournament(tournament_id):
    """Delete a tournament."""
    response = supabase.table("tournaments").delete().eq("id", tournament_id).execute()
    if response.data:
        return jsonify({"message": "Tournament deleted."}), 200
    return jsonify({"error": "Tournament not found."}), 404
