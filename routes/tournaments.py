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
    """List tournaments, optionally filtered by host_id."""
    host_id = request.args.get("host_id")

    # Base query to get tournaments
    query = supabase.table("tournaments").select("*")
    if host_id:
        query = query.eq("host_id", host_id)

    try:
        tournaments_response = query.execute()
        tournaments = tournaments_response.data or []
        return jsonify(tournaments), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@tournaments_bp.route("/user-tournaments", methods=["GET"])
def list_user_tournaments():
    """List tournaments the user is part of (hosted or joined)."""
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required."}), 400

    try:
        # Fetch tournaments where the user is the host
        hosted_response = (
            supabase.table("tournaments").select("*").eq("host_id", user_id).execute()
        )
        hosted_tournaments = hosted_response.data or []

        # Fetch tournaments where the user is a participant
        participant_response = (
            supabase.table("participants")
            .select("tournament_id")
            .eq("user_id", user_id)
            .execute()
        )
        participant_tournament_ids = [
            p["tournament_id"] for p in participant_response.data
        ]

        joined_tournaments_response = (
            supabase.table("tournaments")
            .select("*")
            .in_("id", participant_tournament_ids)
            .execute()
        )
        joined_tournaments = joined_tournaments_response.data or []

        # Combine and deduplicate tournaments
        all_tournaments = {t["id"]: t for t in hosted_tournaments + joined_tournaments}

        return jsonify(list(all_tournaments.values())), 200
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
    """Delete a tournament and its participants."""
    try:
        # Delete participants associated with the tournament

        supabase.table("participants").delete().eq(
            "tournament_id", tournament_id
        ).execute()

        # Delete the tournament itself
        tournament_response = (
            supabase.table("tournaments").delete().eq("id", tournament_id).execute()
        )

        if tournament_response.data:
            return (
                jsonify({"message": "Tournament and associated participants deleted."}),
                200,
            )

        return jsonify({"error": "Tournament not found."}), 404
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
