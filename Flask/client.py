import requests
import time

# BASE_URL = "https://flask-production-2976.up.railway.app"
BASE_URL = "https://toybattle.onrender.com"

def create_game():
    r = requests.post(f"{BASE_URL}/create_game")
    data = r.json()
    print("Game créé :", data["game_id"])
    return data["game_id"]

def join_game(game_id, player):
    r = requests.post(f"{BASE_URL}/join_game", json={
        "game_id": game_id,
        "player": player
    })
    print(r.json())

def get_state(game_id):
    r = requests.get(f"{BASE_URL}/state", params={
        "game_id": game_id
    })
    return r.json()

def play_move(game_id, player, position):
    r = requests.post(f"{BASE_URL}/move", json={
        "game_id": game_id,
        "player": player,
        "position": position
    })
    print(r.json())

def display_board(board):
    for i in range(0, 9, 3):
        print(board[i:i+3])
    print()

def main():
    print("1. Créer une partie")
    print("2. Rejoindre une partie")
    choice = input("> ")

    if choice == "1":
        game_id = create_game()
    else:
        game_id = input("Game ID: ")

    player = input("Ton nom: ")
    join_game(game_id, player)

    last_turn = None

    while True:
        state = get_state(game_id)

        if "error" in state:
            print(state["error"])
            break

        if state["state"] != "playing":
            print("En attente d'un autre joueur...")
            time.sleep(2)
            continue

        # afficher seulement si changement
        if state["turn"] != last_turn:
            print("\nEtat du jeu:")
            display_board(state["board"])
            print("Tour de :", state["turn"])
            last_turn = state["turn"]

        if state["turn"] == player:
            try:
                pos = int(input("Position (0-8): "))
                play_move(game_id, player, pos)
            except:
                print("Entrée invalide")
        else:
            time.sleep(2)  # pause pour éviter spam

if __name__ == "__main__":
    main()