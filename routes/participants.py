from flask import Blueprint, jsonify, request

from client import supabase

participants_bp = Blueprint("participants", __name__)


@participants_bp.route("/participants", methods=["POST"])
def add_participant():
    """Add a participant to a tournament using either tournament_id or code."""
    data = request.json
    tournament_id = data.get("tournament_id")
    code = data.get("code")
    user_id = data.get("user_id")

    if not user_id or (not tournament_id and not code):
        return (
            jsonify(
                {"error": "user_id and either tournament_id or code are required."}
            ),
            400,
        )

    # Resolve tournament_id using code if not provided
    if not tournament_id:
        try:
            tournament_response = (
                supabase.table("tournaments").select("id").eq("code", code).execute()
            )
            if tournament_response.data:
                tournament_id = tournament_response.data[0]["id"]
            else:
                return (
                    jsonify({"error": "Tournament with the provided code not found."}),
                    404,
                )
        except Exception as e:
            print(e)
            return jsonify({"error": "Error fetching tournament by code."}), 500

    # Add participant
    try:
        response = (
            supabase.table("participants")
            .insert({"tournament_id": tournament_id, "user_id": user_id})
            .execute()
        )

        # Increment the participant count using the RPC function
        supabase.rpc(
            "increment_participant_count",
            {"tournament_id": tournament_id, "increment_by": 1},
        ).execute()

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
    """List participants for a specific tournament, enriched with user data."""
    tournament_id = request.args.get("tournament_id")
    if not tournament_id:
        return jsonify({"error": "tournament_id is required."}), 400

    try:
        # Fetch participants
        participants_response = (
            supabase.table("participants")
            .select("id, tournament_id, user_id, created_at")
            .eq("tournament_id", tournament_id)
            .execute()
        )

        if not participants_response.data:
            return jsonify([]), 200

        participant_ids = [p["user_id"] for p in participants_response.data]

        # Fetch user data for the participants
        user_data_response = (
            supabase.table("user_data")
            .select("user_id, email, first_name, last_name")
            .in_("user_id", participant_ids)
            .execute()
        )

        # Create a mapping of user_id to user details
        user_data_map = {u["user_id"]: u for u in user_data_response.data}

        # Enrich participants with user data
        enriched_participants = [
            {
                **participant,
                "email": user_data_map.get(participant["user_id"], {}).get("email"),
                "first_name": user_data_map.get(participant["user_id"], {}).get(
                    "first_name"
                ),
                "last_name": user_data_map.get(participant["user_id"], {}).get(
                    "last_name"
                ),
            }
            for participant in participants_response.data
        ]

        return jsonify(enriched_participants), 200
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


@participants_bp.route("/participants/<participant_id>", methods=["DELETE"])
def remove_participant(participant_id):
    """Remove a participant from a tournament."""
    try:
        # Fetch the tournament_id before deleting
        participant_response = (
            supabase.table("participants")
            .select("tournament_id")
            .eq("id", participant_id)
            .execute()
        )
        if not participant_response.data:
            return jsonify({"error": "Participant not found."}), 404

        tournament_id = participant_response.data[0]["tournament_id"]

        # Remove the participant
        supabase.table("participants").delete().eq("id", participant_id).execute()

        # Decrement the participant count using the RPC function
        supabase.rpc(
            "increment_participant_count",
            {"tournament_id": tournament_id, "increment_by": -1},
        ).execute()

        return jsonify({"message": "Participant removed."}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
