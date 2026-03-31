from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# Stockage des parties
games = {}

# Structure d'une partie
def create_game():
    return {
        "players": [],
        "turn": None,
        "state": "waiting",  # waiting / playing / finished
        "board": [""] * 9  # exemple: morpion
    }

# Créer une partie
@app.route("/create_game", methods=["POST"])
def create():
    game_id = str(uuid.uuid4())
    games[game_id] = create_game()
    return jsonify({"game_id": game_id})

# Rejoindre une partie
@app.route("/join_game", methods=["POST"])
def join():
    data = request.json
    game_id = data["game_id"]
    player_name = data["player"]

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]

    if len(game["players"]) >= 2:
        return jsonify({"error": "Game full"}), 400

    game["players"].append(player_name)

    if len(game["players"]) == 2:
        game["state"] = "playing"
        game["turn"] = game["players"][0]

    return jsonify({"message": "joined", "game": game})

# Jouer un coup
@app.route("/move", methods=["POST"])
def move():
    data = request.json
    game_id = data["game_id"]
    player = data["player"]
    position = data["position"]

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]

    if game["state"] != "playing":
        return jsonify({"error": "Game not started"}), 400

    if game["turn"] != player:
        return jsonify({"error": "Not your turn"}), 400

    if game["board"][position] != "":
        return jsonify({"error": "Invalid move"}), 400

    symbol = "X" if game["players"][0] == player else "O"
    game["board"][position] = symbol

    # Changer de tour
    game["turn"] = (
        game["players"][1]
        if game["turn"] == game["players"][0]
        else game["players"][0]
    )

    return jsonify({"message": "move played", "game": game})

# Voir l'état du jeu
@app.route("/state", methods=["GET"])
def state():
    game_id = request.args.get("game_id")

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    return jsonify(games[game_id])


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)