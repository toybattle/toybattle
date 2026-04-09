import pygame
import sys
import json
import requests
import time
import Cards
import Effect as Effect
import random
from Utils import load_path

# Url du serveur (à synchroniser avec Room.py)
# BASE_URL = "http://127.0.0.1:8000"
BASE_URL = "https://flask-production-2976.up.railway.app"

def gameMulti(screen, clock, gamedata):
    # --- INITIALISATION DES DONNÉES ---
    WIDTH, HEIGHT = screen.get_size()
    game_id = gamedata.get('game_id')
    my_role = gamedata.get('role') # 'server' ou 'client'
    map_index = gamedata.get('map', 0)
    
    # On définit quel joueur on est pour le serveur (joueur 1 ou 2)
    # Le créateur (server) est le premier à rejoindre, donc joueur 1?
    # En fait on utilise le rôle directement pour le check de tour
    my_player_name = my_role 

    pygame.display.set_caption(f"Toy Battle - Partie {game_id} ({my_role})")

    # --- LAYOUT DYNAMIQUE ---
    UI_Y = HEIGHT - 150
    MAP_HEIGHT = int(HEIGHT * 0.72)
    MAP_WIDTH = 0
    MAP_X = 0
    MAP_Y = 20
    map_surface = None
    ratio = 1.0

    def update_layout(w, h, map_img):
        nonlocal UI_Y, MAP_HEIGHT, MAP_WIDTH, MAP_X, MAP_Y, map_surface, ratio, WIDTH, HEIGHT
        WIDTH, HEIGHT = w, h
        UI_Y = HEIGHT - 150
        MAP_HEIGHT = int(HEIGHT * 0.72)
        ratio = map_img.get_width() / map_img.get_height()
        MAP_WIDTH = int(MAP_HEIGHT * ratio)
        if MAP_WIDTH > WIDTH - 250:
            MAP_WIDTH = WIDTH - 250
            MAP_HEIGHT = int(MAP_WIDTH / ratio)
        map_surface = pygame.transform.scale(map_img, (MAP_WIDTH, MAP_HEIGHT))
        MAP_X = (WIDTH - MAP_WIDTH) // 2
        MAP_Y = 20
        return map_surface

    # --- CHARGEMENT ---
    try:
        datamap = json.load(open(load_path("data", "map_data.json"), "r"))
        map_name = list(datamap.keys())[map_index]
        map_img = pygame.image.load(load_path("assets/map", "MapHalloween.jpg")).convert()
        water = pygame.image.load(load_path("assets", "water.png")).convert()
        pioche_img = pygame.image.load(load_path("assets", "pioche.png")).convert_alpha()
        pioche_img = pygame.transform.scale(pioche_img, (100, 130))
    except Exception as e:
        print(f"Erreur Assets Game: {e}")
        return "mainMenu"

    map_surface = update_layout(WIDTH, HEIGHT, map_img)

    # --- SYSTÈME DE CARTES ---
    # On initialise les cartes localement
    deck_host, deck_client = Cards.init_cards()
    if my_role == 'server':
        my_hand = Cards.host_cards(deck_host)
        my_deck = deck_host
    else:
        my_hand = Cards.client_cards(deck_client)
        my_deck = deck_client
        
    selected_card_index = None

    # --- EFFETS ---
    systeme_particules = Effect.SystemeParticules()

    # --- LOGIQUE RÉSEAU ---
    game_state = {
        "turn": None,
        "units": [],
        "state": "waiting"
    }
    last_poll_time = 0
    poll_interval = 1.0 # 1 seconde entre chaque check

    def poll_server():
        nonlocal game_state
        try:
            r = requests.get(f"{BASE_URL}/state", params={"game_id": game_id}, timeout=2)
            if r.status_code == 200:
                game_state = r.json()
        except:
            pass

    def send_move(tile_id, card_data):
        try:
            requests.post(f"{BASE_URL}/move", json={
                "game_id": game_id,
                "player": my_player_name,
                "tile_id": tile_id,
                "card_data": card_data
            }, timeout=2)
        except:
            pass

    # --- LOGIQUE DE PLACEMENT ---

    def get_screen_pos(tile_id):
        tile = next(t for t in datamap[map_name]["tiles"] if t["id"] == tile_id)
        tx = MAP_X + int((tile["x"] + tile["w"]/2) * MAP_WIDTH)
        ty = MAP_Y + int((tile["y"] + tile["h"]/2) * MAP_HEIGHT)
        return tx, ty

    class Unit:
        def __init__(self, tile_id, card_data, owner):
            self.tile_id = tile_id
            self.card_data = card_data
            self.owner = owner
            try:
                self.base_image = pygame.image.load(load_path("assets/cards", card_data["image_path"])).convert_alpha()
            except:
                self.base_image = pygame.Surface((40, 50), pygame.SRCALPHA)
                self.base_image.fill((200, 100, 100))

        def draw(self, surf):
            self.x, self.y = get_screen_pos(self.tile_id)
            tile = next((t for t in datamap[map_name]["tiles"] if t["id"] == self.tile_id), None)
            if tile:
                tile_w = int(tile["w"] * MAP_WIDTH)
                tile_h = int(tile["h"] * MAP_HEIGHT)
                scale = 1.1 if "Crochet" in self.card_data.get("name", "") else 0.9
                width = max(24, min(tile_w, int(tile_w * scale)))
                height = max(32, min(tile_h, int(tile_h * scale * 1.1)))
            else:
                width, height = 60, 80

            image = pygame.transform.scale(self.base_image, (width, height))
            rect = image.get_rect(center=(self.x, self.y))
            surf.blit(image, rect)

    def get_valid_tiles(units, card):
        occupied_ids = [u["tile_id"] for u in units]
        valid_ids = set()
        
        # Le joueur 1 (server) part d'un coté, joueur 2 (client) de l'autre
        player_side = "player1" if my_role == "server" else "player2"
        
        for tile in datamap[map_name]["tiles"]:
            if tile["type"] == "start" and tile["player"] == player_side:
                valid_ids.add(tile["id"])
        
        # Et les cases adjacentes à ses propres unités
        for u in units:
            if u["player"] == my_player_name:
                for link in datamap[map_name]["links"]:
                    if link[0] == u["tile_id"]: valid_ids.add(link[1])
                    elif link[1] == u["tile_id"]: valid_ids.add(link[0])
        
        # Filtre: on ne peut pas poser sur une case déjà occupée par soi-même
        # (Pour simplifier, on enlève toutes les cases occupées pour l'instant)
        final_valid = [tid for tid in valid_ids if tid not in occupied_ids]
        return final_valid

    # --- BOUCLE PRINCIPALE ---
    while True:
        current_time = time.time()
        if current_time - last_poll_time > poll_interval:
            poll_server()
            last_poll_time = current_time

        screen.fill((30, 30, 35))
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "mainMenu"
                
            if event.type == pygame.VIDEORESIZE:
                map_surface = update_layout(event.w, event.h, map_img)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Sélection de carte dans la main
                for i in range(len(my_hand)):
                    rect = pygame.Rect(WIDTH//2 - 150 + i*110, UI_Y + 20, 90, 120)
                    if rect.collidepoint(mouse_pos):
                        selected_card_index = i
                
                # Placement sur la Map (si c'est mon tour)
                if selected_card_index is not None and game_state.get("turn") == my_player_name:
                    current_card = my_hand[selected_card_index]
                    valid_ids = get_valid_tiles(game_state.get("units", []), current_card)
                    
                    for tile in datamap[map_name]["tiles"]:
                        tr = pygame.Rect(MAP_X + tile["x"]*MAP_WIDTH, MAP_Y + tile["y"]*MAP_HEIGHT, 
                                         tile["w"]*MAP_WIDTH, tile["h"]*MAP_HEIGHT)
                        
                        if tr.collidepoint(mouse_pos) and tile["id"] in valid_ids:
                            # Envoyer le coup au serveur
                            send_move(tile["id"], current_card)
                            
                            # Effets locaux immédiats
                            x, y = get_screen_pos(tile["id"])
                            systeme_particules.create_particles(x, y, nombre=40)
                            
                            my_hand.pop(selected_card_index)
                            selected_card_index = None
                            
                            # On force un poll immédiat pour voir le changement de tour
                            poll_server()
                            break

                # Click sur la pioche
                pioche_rect = pygame.Rect(MAP_X + MAP_WIDTH + 20, MAP_Y + 300, 100, 130)
                if pioche_rect.collidepoint(mouse_pos) and (len(my_hand) < 5):
                    if my_deck:
                        my_hand.append(my_deck.pop(0))

        # --- DESSIN ---
        screen.blit(map_surface, (MAP_X, MAP_Y))

        # Surbrillance des cases valides
        if selected_card_index is not None and game_state.get("turn") == my_player_name:
            current_card = my_hand[selected_card_index]
            valid_ids = get_valid_tiles(game_state.get("units", []), current_card)
            for tile in datamap[map_name]["tiles"]:
                if tile["id"] in valid_ids:
                    sx = MAP_X + int(tile["x"] * MAP_WIDTH)
                    sy = MAP_Y + int(tile["y"] * MAP_HEIGHT)
                    sw = int(tile["w"] * MAP_WIDTH)
                    sh = int(tile["h"] * MAP_HEIGHT)
                    s = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    color = (0, 150, 255, 150) if "Crochet" in current_card.get("name", "") else (0, 255, 100, 150)
                    pygame.draw.rect(s, color, (0, 0, sw, sh), border_radius=5)
                    screen.blit(s, (sx, sy))

        # Dessiner les unités du serveur
        for u_data in game_state.get("units", []):
            u = Unit(u_data["tile_id"], u_data["card"], u_data["player"])
            u.draw(screen)

        # UI
        pygame.draw.rect(screen, (14, 14, 18), (0, UI_Y - 4, WIDTH, 154), border_radius=8)
        pygame.draw.rect(screen, (70, 70, 90), (0, UI_Y - 4, WIDTH, 154), 2, border_radius=8)

        ui_font = pygame.font.SysFont(None, 24)
        turn_text = "C'est votre tour !" if game_state.get("turn") == my_player_name else f"Attente de {game_state.get('turn')}..."
        if game_state.get("state") == "waiting": turn_text = "En attente d'un adversaire..."
        
        title = ui_font.render(f"Main ({len(my_hand)}) - {turn_text}", True, (230, 230, 240))
        screen.blit(title, (20, UI_Y - 26))

        # Main du joueur
        for i, card in enumerate(my_hand):
            cx = WIDTH//2 - 150 + i*110
            cy = UI_Y + 20
            is_selected = (i == selected_card_index)
            slot_color = (34, 34, 40) if not is_selected else (40, 50, 70)
            pygame.draw.rect(screen, slot_color, (cx-5, cy-5, 100, 130), border_radius=8)
            try:
                img = pygame.image.load(load_path("assets/cards", card["image_path"])).convert_alpha()
                scaled = pygame.transform.scale(img, (90, 120))
                screen.blit(scaled, (cx, cy))
            except:
                pygame.draw.rect(screen, (80, 80, 80), (cx, cy, 90, 120), border_radius=8)
            if is_selected:
                pygame.draw.rect(screen, (255, 215, 0), (cx-5, cy-5, 100, 130), 3, border_radius=8)

        # Pioche
        pygame.draw.rect(screen, (20, 20, 25), (MAP_X + MAP_WIDTH + 10, MAP_Y + 290, 120, 150), border_radius=8)
        screen.blit(pioche_img, (MAP_X + MAP_WIDTH + 20, MAP_Y + 300))

        systeme_particules.update()
        systeme_particules.draw(screen)

        pygame.display.flip()
        clock.tick(60)