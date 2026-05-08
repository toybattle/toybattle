from flask import Flask, request, jsonify
import random
import os
import json

app = Flask(__name__)

# Charger les données de la map
with open("data/map_data.json", "r") as f:
    map_data = json.load(f)

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
        "winner": None,
        "map_id": map_id,
        "units": []  # Liste des unités posées: {"tile_id": ..., "card": ..., "player": ...}
    }


def get_player_side(player):
    return "player1" if player == "server" else "player2"


def is_victory_tile(game, unit):
    map_name = list(map_data.keys())[game["map_id"]]
    enemy_player = "player2" if unit["player"] == "server" else "player1"
    for tile in map_data[map_name]["tiles"]:
        if tile["id"] == unit["tile_id"] and tile.get("type") == "forteresse" and tile.get("player") == enemy_player:
            return True
    return False


def has_path_to_enemy_fortress(game, target_tile_id, player):
    map_name = list(map_data.keys())[game["map_id"]]
    player_side = get_player_side(player)
    owned_tiles = {u["tile_id"] for u in game["units"] if u["player"] == player}
    start_tiles = {
        t["id"]
        for t in map_data[map_name]["tiles"]
        if t["type"] == "start" and t.get("player") == player_side and t["id"] in owned_tiles
    }
    if not start_tiles:
        return False

    graph = {t["id"]: set() for t in map_data[map_name]["tiles"]}
    for link in map_data[map_name]["links"]:
        graph[link[0]].add(link[1])
        graph[link[1]].add(link[0])

    visited = set(start_tiles)
    queue = list(start_tiles)
    while queue:
        current = queue.pop(0)
        for neighbor in graph.get(current, set()):
            if neighbor == target_tile_id:
                return True
            if neighbor in owned_tiles and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False

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
    new_unit = {
        "tile_id": tile_id,
        "card": card_data,
        "player": player
    }
    game["units"].append(new_unit)

    # Résoudre les batailles pour la nouvelle unité
    resolve_battles(game, new_unit)

    # Appliquer les effets de la carte
    change_turn = apply_card_effects(game, new_unit)

    # Vérifier la condition de victoire par forteresse ennemie
    if is_victory_tile(game, new_unit) and has_path_to_enemy_fortress(game, new_unit["tile_id"], player):
        game["state"] = "finished"
        game["winner"] = player
    elif change_turn:
        game["turn"] = (
            game["players"][1]
            if game["turn"] == game["players"][0]
            else game["players"][0]
        )

    return jsonify({"message": "move played", "game": game})

def resolve_battles(game, new_unit):
    map_name = list(map_data.keys())[game["map_id"]]
    links = map_data[map_name]["links"]
    
    # Trouver les unités adjacentes
    adjacent_tiles = set()
    for link in links:
        if link[0] == new_unit["tile_id"]:
            adjacent_tiles.add(link[1])
        elif link[1] == new_unit["tile_id"]:
            adjacent_tiles.add(link[0])
    
    # Vérifier les batailles
    units_to_remove = []
    for unit in game["units"]:
        if unit["tile_id"] in adjacent_tiles and unit["player"] != new_unit["player"]:
            # Bataille: si force supérieure, manger
            if new_unit["card"]["strength"] > unit["card"]["strength"]:
                units_to_remove.append(unit)
    
    # Supprimer les unités mangées
    for unit in units_to_remove:
        game["units"].remove(unit)

def apply_card_effects(game, new_unit):
    card_name = new_unit["card"]["name"]
    change_turn = True
    if card_name == "Mastok":
        # Détruit une tuile adverse adjacente
        map_name = list(map_data.keys())[game["map_id"]]
        links = map_data[map_name]["links"]
        adjacent_tiles = set()
        for link in links:
            if link[0] == new_unit["tile_id"]:
                adjacent_tiles.add(link[1])
            elif link[1] == new_unit["tile_id"]:
                adjacent_tiles.add(link[0])
        for unit in game["units"]:
            if unit["tile_id"] in adjacent_tiles and unit["player"] != new_unit["player"]:
                game["units"].remove(unit)
                break  # Supprime une seule
    elif card_name == "XB-42":
        # Supprime une des tuiles adverses (choisir la première)
        for unit in game["units"]:
            if unit["player"] != new_unit["player"]:
                game["units"].remove(unit)
                break
    elif card_name == "Cap'taine":
        # Rejouer immédiatement
        change_turn = False
    # Autres effets peuvent être ajoutés ici
    return change_turn

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
