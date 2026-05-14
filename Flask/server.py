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
        code = code + str(random.randint(1,9))
    return code

def map_choice():
    # Retourne un index de map (0 ou 1 pour l'instant)
    # return random.randint(0, len(map_data)-1)
    return 0

# Structure d'une partie
def create_game_struct(map_id):
    return {
        "players": [],
        "turn": None,
        "state": "waiting",  # waiting / playing / finished
        "winner": None,
        "map_id": map_id,
        "units": [],  # Liste des unités posées: {"tile_id": ..., "card": ..., "player": ...}
            "card_counts": {
            "server": {"hand": 0, "deck": 0},
            "client": {"hand": 0, "deck": 0}
        },
        "pending_deck_penalty": None,
        "pending_hand_penalty": None,
        "pending_target": None
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


def get_player_star_count(game, player):
    map_name = list(map_data.keys())[game["map_id"]]
    star_zones = map_data[map_name].get("star_zones", [])
    tile_owners = {u["tile_id"]: u["player"] for u in game["units"]}
    count = 0
    for zone in star_zones:
        req_tiles = zone.get("required_tiles", [])
        if not req_tiles:
            continue
        owner = tile_owners.get(req_tiles[0])
        if owner and all(tile_owners.get(tid) == owner for tid in req_tiles):
            if owner == player:
                count += 1
    return count


def is_victory_stars(game, player):
    map_name = list(map_data.keys())[game["map_id"]]
    required_stars = map_data[map_name].get("num_stars", 7) // 2 + 1
    return get_player_star_count(game, player) >= required_stars


def check_card_exhaustion(game):
    if game["state"] != "playing":
        return

    card_counts = game.get("card_counts", {})
    server_total = card_counts.get("server", {}).get("hand", 0) + card_counts.get("server", {}).get("deck", 0)
    client_total = card_counts.get("client", {}).get("hand", 0) + card_counts.get("client", {}).get("deck", 0)

    if server_total == 0 and client_total == 0:
        server_stars = get_player_star_count(game, "server")
        client_stars = get_player_star_count(game, "client")
        if server_stars > client_stars:
            game["winner"] = "server"
        elif client_stars > server_stars:
            game["winner"] = "client"
        else:
            game["winner"] = "draw"
        game["state"] = "finished"


def switch_turn(game):
    if game["turn"] and len(game["players"]) == 2:
        game["turn"] = (
            game["players"][1]
            if game["turn"] == game["players"][0]
            else game["players"][0]
        )


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

    # Appliquer les effets de la carte ou attendre le ciblage explicite
    card_name = card_data.get("name", "")
    if card_name == "Mastok":
        game["pending_target"] = {
            "player": player,
            "tile_id": tile_id,
            "card": card_data
        }
        change_turn = False
    else:
        change_turn = apply_card_effects(game, new_unit)

    # Vérifier la condition de victoire par forteresse ennemie
    if is_victory_tile(game, new_unit) and has_path_to_enemy_fortress(game, new_unit["tile_id"], player):
        game["state"] = "finished"
        game["winner"] = player
    # Vérifier la condition de victoire par nombre d'étoiles
    elif is_victory_stars(game, player):
        game["state"] = "finished"
        game["winner"] = player
    elif change_turn:
        game["turn"] = (
            game["players"][1]
            if game["turn"] == game["players"][0]
            else game["players"][0]
        )

    return jsonify({"message": "move played", "game": game})

@app.route("/resolve_target", methods=["POST"])
def resolve_target():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")
    target_tile_id = data.get("target_tile_id")

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]

    if game["state"] != "playing":
        return jsonify({"error": "Game not started"}), 400

    pending = game.get("pending_target")
    if not pending or pending.get("player") != player:
        return jsonify({"error": "No pending target selection"}), 400

    if target_tile_id is None:
        return jsonify({"error": "Target tile required"}), 400

    target_unit = next((u for u in game["units"] if u["tile_id"] == target_tile_id and u["player"] != player), None)
    if not target_unit:
        return jsonify({"error": "Invalid target"}), 400

    card_name = pending["card"].get("name", "")
    map_name = list(map_data.keys())[game["map_id"]]
    if card_name == "Mastok":
        adjacent_ids = {link[1] if link[0] == pending["tile_id"] else link[0] for link in map_data[map_name]["links"] if pending["tile_id"] in link}
        if target_tile_id not in adjacent_ids:
            return jsonify({"error": "Target not adjacent"}), 400
        game["units"].remove(target_unit)
    elif card_name == "XB-42":
        game["units"].remove(target_unit)
    else:
        return jsonify({"error": "Unsupported target card"}), 400

    game["pending_target"] = None
    switch_turn(game)
    check_card_exhaustion(game)
    return jsonify({"message": "target resolved", "game": game})


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

    # Roxy does not destroy adjacent tiles on placement and is immune to adjacency battles
    if new_unit["card"]["name"] == "Roxy":
        return

    # Utiliser la carte du dessus si plusieurs unités sont superposées
    top_units_by_tile = {}
    for unit in game["units"]:
        top_units_by_tile[unit["tile_id"]] = unit

    # Vérifier les batailles contre les unités adjacentes
    units_to_remove = []
    for tile_id in adjacent_tiles:
        unit = top_units_by_tile.get(tile_id)
        if not unit or unit["player"] == new_unit["player"]:
            continue
        if unit["card"]["name"] == "Roxy":
            continue
        if new_unit["card"]["strength"] > unit["card"]["strength"]:
            units_to_remove.append(unit)

    # Supprimer les unités mangées
    for unit in units_to_remove:
        if unit in game["units"]:
            game["units"].remove(unit)


def apply_card_effects(game, new_unit):
    card_name = new_unit["card"]["name"]
    change_turn = True
    if card_name == "Mastok":
        # Détruit une tuile adverse adjacente (le dessus si plusieurs sont superposées)
        map_name = list(map_data.keys())[game["map_id"]]
        links = map_data[map_name]["links"]
        adjacent_tiles = set()
        for link in links:
            if link[0] == new_unit["tile_id"]:
                adjacent_tiles.add(link[1])
            elif link[1] == new_unit["tile_id"]:
                adjacent_tiles.add(link[0])

        top_units_by_tile = {}
        for unit in game["units"]:
            top_units_by_tile[unit["tile_id"]] = unit

        for tile_id in adjacent_tiles:
            unit = top_units_by_tile.get(tile_id)
            if unit and unit["player"] != new_unit["player"]:
                game["units"].remove(unit)
                break  # Supprime une seule unité adverse au sommet
    elif card_name == "XB-42":
        opponent = "client" if new_unit["player"] == "server" else "server"
        hand_count = game["card_counts"][opponent].get("hand", 0)
        if hand_count > 0:
            game["card_counts"][opponent]["hand"] = hand_count - 1
            game["pending_hand_penalty"] = opponent
    elif card_name == "Cap'taine":
        # Rejouer immédiatement
        change_turn = False
    # Autres effets peuvent être ajoutés ici
    return change_turn

@app.route("/update_card_counts", methods=["POST"])
def update_card_counts():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")
    hand_count = data.get("hand_count")
    deck_count = data.get("deck_count")

    if not game_id or game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    if player not in ("server", "client"):
        return jsonify({"error": "Invalid player"}), 400

    game = games[game_id]
    game["card_counts"][player]["hand"] = max(0, int(hand_count or 0))
    game["card_counts"][player]["deck"] = max(0, int(deck_count or 0))
    check_card_exhaustion(game)
    return jsonify({"message": "counts updated", "game": game})

@app.route("/draw", methods=["POST"])
def draw():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")

    if not game_id or game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]
    if game["state"] != "playing":
        return jsonify({"error": "Game not started"}), 400

    if game["turn"] != player:
        return jsonify({"error": "Not your turn"}), 400

    switch_turn(game)
    return jsonify({"message": "draw done", "game": game})

@app.route("/leave", methods=["POST"])
def leave():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")

    if not game_id or game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    if player not in ("server", "client"):
        return jsonify({"error": "Invalid player"}), 400

    game = games[game_id]
    if game["state"] == "finished":
        return jsonify({"message": "Game already finished", "game": game})

    if player not in game["players"]:
        return jsonify({"error": "Player not in game"}), 400

    if len(game["players"]) == 2 and game["state"] == "playing":
        other = game["players"][1] if game["players"][0] == player else game["players"][0]
        game["winner"] = other
        game["state"] = "finished"
        return jsonify({"message": "Player left, opponent wins", "game": game})

    if len(game["players"]) == 1:
        game["players"].remove(player)
        game["state"] = "waiting"
        return jsonify({"message": "Player left", "game": game})

    return jsonify({"message": "Leave recorded", "game": game})

@app.route("/resolve_deck_penalty", methods=["POST"])
def resolve_deck_penalty():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")

    if not game_id or game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    if player not in ("server", "client"):
        return jsonify({"error": "Invalid player"}), 400

    game = games[game_id]
    if game.get("pending_deck_penalty") == player:
        game["pending_deck_penalty"] = None
    if game.get("pending_hand_penalty") == player:
        game["pending_hand_penalty"] = None
    return jsonify({"message": "penalty resolved", "game": game})

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
