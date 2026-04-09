from flask import Flask, request, jsonify
import random
import os

app = Flask(__name__)

# Stockage des parties
games = {}

def gen_code():
    code = ""
    for i in range(4):
        code = code + str(random.randint(0,9))
    return code

def map_choice():
    # Retourne un index de map (0 ou 1 pour l'instant)
    return random.randint(0,1)

# Structure d'une partie
def create_game_struct(map_id):
    return {
        "players": [],
        "turn": None,
        "state": "waiting",  # waiting / playing / finished
        "map_id": map_id,
        "units": []  # Liste des unités posées: {"tile_id": ..., "card": ..., "player": ...}
    }

@app.route("/test", methods=["GET", "POST"])
def test():
    return jsonify({"msg": "cc"})

# Créer une partie
@app.route("/create_game", methods=["POST"])
def create():
    game_id = gen_code()
    map_id = map_choice()
    games[game_id] = create_game_struct(map_id)
    return jsonify({"game_id": game_id, "map_id" : map_id})

# Rejoindre une partie
@app.route("/join_game", methods=["POST"])
def join():
    data = request.json
    game_id = data.get("game_id")
    player_name = data.get("player")

    if not game_id or game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]

    if player_name not in game["players"]:
        if len(game["players"]) >= 2:
            return jsonify({"error": "Game full"}), 400
        game["players"].append(player_name)

    if len(game["players"]) == 2:
        game["state"] = "playing"
        if not game["turn"]:
            game["turn"] = game["players"][0]

    return jsonify({"message": "joined", "game": game})

# Jouer un coup (poser une carte)
@app.route("/move", methods=["POST"])
def move():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")
    tile_id = data.get("tile_id")
    card_data = data.get("card_data")

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]

    if game["state"] != "playing":
        return jsonify({"error": "Game not started"}), 400

    if game["turn"] != player:
        return jsonify({"error": "Not your turn"}), 400

    # Ajouter l'unité au plateau côté serveur
    game["units"].append({
        "tile_id": tile_id,
        "card": card_data,
        "player": player
    })

    # Changer de tour
    game["turn"] = (
        game["players"][1]
        if game["turn"] == game["players"][0]
        else game["players"][0]
    )

    return jsonify({"message": "move played", "game": game})

# Voir l'état du jeu (Polling)
@app.route("/state", methods=["GET"])
def state():
    game_id = request.args.get("game_id")

    if not game_id or game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    return jsonify(games[game_id])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
