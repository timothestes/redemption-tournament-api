from flask import Blueprint, jsonify, request

from client import supabase

participants_bp = Blueprint("participants", __name__)


@participants_bp.route("/participants", methods=["POST"])
def add_participant():
    """Add a participant to a tournament."""
    data = request.json
    tournament_id = data.get("tournament_id")
    user_id = data.get("user_id")

    if not tournament_id or not user_id:
        return jsonify({"error": "tournament_id and user_id are required."}), 400

    try:
        response = (
            supabase.table("participants")
            .insert({"tournament_id": tournament_id, "user_id": user_id})
            .execute()
        )
        return jsonify(response.data[0]), 201
    except Exception as e:
        error_message = str(e).lower()
        if "duplicate key" in error_message or "unique constraint" in error_message:
            return (
                jsonify({"error": "Participant already exists in this tournament."}),
                409,
            )
        print(e)
        return jsonify({"error": str(e)}), 500


@participants_bp.route("/participants", methods=["GET"])
def list_participants():
    """List participants for a specific tournament."""
    tournament_id = request.args.get("tournament_id")
    if not tournament_id:
        return jsonify({"error": "tournament_id is required."}), 400

    try:
        response = (
            supabase.table("participants")
            .select("id, tournament_id, user_id, created_at")
            .eq("tournament_id", tournament_id)
            .execute()
        )
        return jsonify(response.data), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@participants_bp.route("/participants/<participant_id>", methods=["DELETE"])
def remove_participant(participant_id):
    """Remove a participant from a tournament."""
    try:
        response = (
            supabase.table("participants").delete().eq("id", participant_id).execute()
        )
        if response.data:
            return jsonify({"message": "Participant removed."}), 200
        return jsonify({"error": "Participant not found."}), 404
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@participants_bp.route("/participants/<participant_id>", methods=["PUT"])
def update_participant(participant_id):
    """Update participant information in a tournament."""
    data = request.json
    fields = {k: v for k, v in data.items() if k != "id"}
    if not fields:
        return jsonify({"error": "No valid fields to update."}), 400

    try:
        response = (
            supabase.table("participants")
            .update(fields)
            .eq("id", participant_id)
            .execute()
        )
        if response.data:
            return jsonify(response.data[0]), 200
        return jsonify({"error": "Participant not found."}), 404
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
