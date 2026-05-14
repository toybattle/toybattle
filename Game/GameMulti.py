import pygame
import sys
import json
import random
import requests
import time
import Cards
import Effect as Effect
import os
import threading
from Utils import load_path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'auth'))
from db import supabase

# Url du serveur (à synchroniser avec Room.py)

# BASE_URL = "https://flask-production-2976.up.railway.app"
BASE_URL = "https://toybattle.onrender.com"

def gameMulti(screen, clock, gamedata):
    # --- INITIALISATION DES DONNÉES ---
    WIDTH, HEIGHT = screen.get_size()
    game_id = gamedata.get('game_id')
    my_role = gamedata.get('role') # 'server' ou 'client'
    my_name = gamedata.get('name')
    map_index = gamedata.get('map', 0)
    
    # On définit quel joueur on est pour le serveur (joueur 1 ou 2)
    # Le créateur (server) est le premier à rejoindre, donc joueur 1?
    # En fait on utilise le rôle directement pour le check de tour
    my_player_name = my_role 
    enemy_player_name = 'client' if my_role == 'server' else 'server'

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
        map_img = pygame.image.load(load_path("assets/map", map_name + ".jpg")).convert()
        water = pygame.image.load(load_path("assets", "water.png")).convert()
        pioche_img = pygame.image.load(load_path("assets", "pioche.png")).convert_alpha()
        pioche_img = pygame.transform.scale(pioche_img, (100, 130))
    except Exception as e:
        print(f"Erreur Assets Game: {e}")
        return "mainMenu"

    map_surface = update_layout(WIDTH, HEIGHT, map_img)

    # --- ZONES D'ÉTOILES ---
    star_zones = datamap[map_name].get("star_zones", [])
    claimed_zones = {}  # {index_de_la_zone: "server" ou "client"}
    player_stars = {'server': 0, 'client': 0}  # Compteur des étoiles

    # --- SYSTÈME DE CARTES ---
    deck_host, deck_client = Cards.init_cards()
    if my_role == 'server':
        my_hand = Cards.host_cards(deck_host)
        my_deck = deck_host
    else:
        my_hand = Cards.client_cards(deck_client)
        my_deck = deck_client
        
    selected_card_index = None
    selecting_target = False
    victory_start = None

    can_play_extra = False
    destroy_cost = False

    # Cache des images de cartes
    card_image_cache = {}

    def get_card_image(card):
        img_path = card["image_path"]
        if img_path not in card_image_cache:
            try:
                card_image_cache[img_path] = pygame.image.load(load_path("assets/cards", img_path)).convert_alpha()
            except:
                card_image_cache[img_path] = pygame.Surface((90, 120), pygame.SRCALPHA)
                card_image_cache[img_path].fill((80, 80, 80))
        return card_image_cache[img_path]

    # --- EFFETS ---
    systeme_particules = Effect.SystemeParticules()

    # --- LOGIQUE RÉSEAU ---
    game_state = {
        "turn": None,
        "units": [],
        "state": "waiting",
        "winner": None
    }
    last_poll_time = 0
    poll_interval = 1.0 # 1 seconde entre chaque check
    polling_thread = None
    game_state_lock = threading.Lock()
    victory_start = None

    def poll_server():
        nonlocal game_state
        while True:
            try:
                r = requests.get(f"{BASE_URL}/state", params={"game_id": game_id}, timeout=2)
                if r.status_code == 200:
                    with game_state_lock:
                        game_state.update(r.json())
                    handle_pending_penalty()
            except:
                pass
            time.sleep(poll_interval)

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

    def send_card_counts():
        try:
            requests.post(f"{BASE_URL}/update_card_counts", json={
                "game_id": game_id,
                "player": my_player_name,
                "hand_count": len(my_hand),
                "deck_count": len(my_deck)
            }, timeout=2)
        except:
            pass

    def resolve_pending_penalty():
        try:
            requests.post(f"{BASE_URL}/resolve_deck_penalty", json={
                "game_id": game_id,
                "player": my_player_name
            }, timeout=2)
        except:
            pass

    def handle_pending_penalty():
        if game_state.get("pending_hand_penalty") == my_player_name:
            if my_hand:
                my_hand.pop(random.randrange(len(my_hand)))
            send_card_counts()
            resolve_pending_penalty()

    polling_thread = threading.Thread(target=poll_server, daemon=True)
    polling_thread.start()
    send_card_counts()

    # --- LOGIQUE DE PLACEMENT ---

    def get_screen_pos(tile_id):
        tile = next(t for t in datamap[map_name]["tiles"] if t["id"] == tile_id)
        tx = MAP_X + int((tile["x"] + tile["w"]/2) * MAP_WIDTH)
        ty = MAP_Y + int((tile["y"] + tile["h"]/2) * MAP_HEIGHT)
        return tx, ty

    def can_cover(new_card, occupying_card):
        if occupying_card is None:
            return True
        occupying_name = occupying_card.get("name", "")
        new_name = new_card.get("name", "")
        if "Kwak" in new_name:
            return True
        if "Roxy" in occupying_name:
            return False
        new_strength = new_card.get("strength", 0)
        occupying_strength = occupying_card.get("strength", 0)
        return new_strength > occupying_strength

    def execute_ability(card, active_units, hand, deck):
        global selecting_target, destroy_cost
        desc = card.get("ability_desc", "")
        if "Piocher 2 cartes" in desc:
            draw_count = min(2, len(deck), max(0, 8 - len(hand)))
            for _ in range(draw_count):
                hand.append(deck.pop(0))
        elif "Pioche une seule tuile" in desc:
            if deck and len(hand) < 8:
                hand.append(deck.pop(0))
        elif "Détruit une tuile adverse" in desc or "Supprime une des tuiles adverses" in desc:
            selecting_target = True
            if "supprime la tuile du dessus" in desc:
                destroy_cost = True

    class Unit:
        def __init__(self, tile_id, card_data, owner):
            self.tile_id = tile_id
            self.card_data = card_data
            self.owner = owner
            self.image = get_card_image(card_data)

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

            image = pygame.transform.scale(self.image, (width, height))
            rect = image.get_rect(center=(self.x, self.y))
            surf.blit(image, rect)

            if self.owner == my_player_name:
                outline_rect = rect.inflate(8, 8)
                pygame.draw.rect(surf, (255, 215, 0), outline_rect, 3, border_radius=10)

    def get_valid_tiles(units, card):
        occupied_ids = [u["tile_id"] for u in units]
        unit_on_tile = {u["tile_id"]: u for u in units}
        tile_by_id = {t["id"]: t for t in datamap[map_name]["tiles"]}
        tile_graph = {t["id"]: set() for t in datamap[map_name]["tiles"]}
        for link in datamap[map_name]["links"]:
            tile_graph[link[0]].add(link[1])
            tile_graph[link[1]].add(link[0])
        valid_ids = set()
        
        player_side = "player1" if my_role == "server" else "player2"

        def is_own_fortress(tile_id):
            tile = tile_by_id.get(tile_id)
            return bool(tile and tile.get("type") == "forteresse" and tile.get("player") == player_side)

        def has_path_to_tile(target_tile_id):
            own_tiles = {u["tile_id"] for u in units if u["player"] == my_player_name}
            start_tiles = {
                t["id"] for t in datamap[map_name]["tiles"]
                if t["type"] == "start" and t.get("player") == player_side and t["id"] in own_tiles
            }
            if not start_tiles:
                return False

            visited = set(start_tiles)
            queue = list(start_tiles)
            while queue:
                current = queue.pop(0)
                for neighbor in tile_graph.get(current, set()):
                    if neighbor == target_tile_id:
                        return True
                    if neighbor in own_tiles and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            return False

        def can_place_on_tile(tid):
            if is_own_fortress(tid):
                return False
            tile = tile_by_id.get(tid)
            if tile and tile.get("type") == "forteresse" and tile.get("player") != player_side:
                return has_path_to_tile(tid)
            return True
        
        for tile in datamap[map_name]["tiles"]:
            if tile["type"] == "start" and tile["player"] == player_side:
                valid_ids.add(tile["id"])
        
        for u in units:
            if u["player"] == my_player_name:
                for link in datamap[map_name]["links"]:
                    if link[0] == u["tile_id"]:
                        if not is_own_fortress(link[1]):
                            valid_ids.add(link[1])
                    elif link[1] == u["tile_id"]:
                        if not is_own_fortress(link[0]):
                            valid_ids.add(link[0])
        
        standard_valid = set(tid for tid in valid_ids if not is_own_fortress(tid))
        
        if "Crochet" in card.get("name", ""):
            valid_ids = set(t["id"] for t in datamap[map_name]["tiles"] if not is_own_fortress(t["id"]))
        elif "Kwak" in card.get("name", ""):
            valid_ids = standard_valid
        else:
            valid_ids = standard_valid
        
        final_valid = set()
        for tid in valid_ids:
            if not can_place_on_tile(tid):
                continue
            if tid not in occupied_ids:
                final_valid.add(tid)
            else:
                occupying_unit = unit_on_tile[tid]
                if occupying_unit["player"] != my_player_name:
                    if can_cover(card, occupying_unit["card"]):
                        final_valid.add(tid)
        return list(final_valid)

    # --- BOUCLE PRINCIPALE ---
    while True:
        current_time = time.time()

        # ======================================================================
        # GESTION DES ÉTOILES (Logique)
        # ======================================================================
        with game_state_lock:
            current_units = game_state.get("units", [])
            
        # Création d'un dictionnaire liant id de tuile -> propriétaire actuel
        tile_owners = {u["tile_id"]: u["player"] for u in current_units}
        
        # Vérifier si de nouvelles zones ont été capturées
        for idx, zone in enumerate(star_zones):
            if idx not in claimed_zones:
                req_tiles = zone.get("required_tiles", [])
                if not req_tiles:
                    continue
                    
                first_tile_owner = tile_owners.get(req_tiles[0])
                if first_tile_owner:
                    # Vérifier si le joueur possède TOUTES les tuiles requises
                    if all(tile_owners.get(t) == first_tile_owner for t in req_tiles):
                        claimed_zones[idx] = first_tile_owner  # Acquisition définitive
                        player_stars[first_tile_owner] += 1
                        
                        # Effet visuel au centre de la zone d'étoile
                        zx = MAP_X + int((zone["area"]["x"] + zone["area"]["w"]/2) * MAP_WIDTH)
                        zy = MAP_Y + int((zone["area"]["y"] + zone["area"]["h"]/2) * MAP_HEIGHT)
                        systeme_particules.create_particles(zx, zy, nombre=60)

        # ======================================================================
        # GESTION DES ÉVÉNEMENTS
        # ======================================================================
        screen.fill((30, 30, 35))
        mouse_pos = pygame.mouse.get_pos()
        ui_font = pygame.font.SysFont("arial", 24)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "mainMenu"
                
            if event.type == pygame.VIDEORESIZE:
                map_surface = update_layout(event.w, event.h, map_img)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state.get("state") == "finished":
                    continue
                # Sélection de carte dans la main
                for i in range(len(my_hand)):
                    rect = pygame.Rect(WIDTH//2 - 150 + i*110, UI_Y + 20, 90, 120)
                    if rect.collidepoint(mouse_pos):
                        selected_card_index = i
                
                # Placement sur la Map
                if selected_card_index is not None and game_state.get("turn") == my_player_name:
                    with game_state_lock:
                        if game_state.get("turn") == my_player_name:
                            current_card = my_hand[selected_card_index]
                            valid_ids = get_valid_tiles(game_state.get("units", []), current_card)
                    
                    for tile in datamap[map_name]["tiles"]:
                        tr = pygame.Rect(MAP_X + tile["x"]*MAP_WIDTH, MAP_Y + tile["y"]*MAP_HEIGHT, 
                                         tile["w"]*MAP_WIDTH, tile["h"]*MAP_HEIGHT)
                        
                        if tr.collidepoint(mouse_pos) and tile["id"] in valid_ids:
                            send_move(tile["id"], current_card)
                            
                            x, y = get_screen_pos(tile["id"])
                            systeme_particules.create_particles(x, y, nombre=40)
                            
                            card_desc = current_card.get("ability_desc", "")
                            if can_play_extra:
                                my_hand.pop(selected_card_index)
                                can_play_extra = False
                            else:
                                my_hand.pop(selected_card_index)
                                if "Rejouer immédiatement" in card_desc:
                                    can_play_extra = True
                            selected_card_index = None
                            execute_ability(current_card, game_state.get("units", []), my_hand, my_deck)
                            send_card_counts()
                            
                            try:
                                r = requests.get(f"{BASE_URL}/state", params={"game_id": game_id}, timeout=1)
                                if r.status_code == 200:
                                    with game_state_lock:
                                        game_state.update(r.json())
                            except:
                                pass

                # Click sur la pioche
                pioche_rect = pygame.Rect(MAP_X + MAP_WIDTH + 20, MAP_Y + 300, 100, 130)
                if (
                    pioche_rect.collidepoint(mouse_pos)
                    and game_state.get("turn") == my_player_name
                    and game_state.get("state") == "playing"
                    and len(my_hand) < 8
                ):
                    draw_count = min(2, len(my_deck), 8 - len(my_hand))
                    for _ in range(draw_count):
                        my_hand.append(my_deck.pop(0))
                    send_card_counts()
                    try:
                        requests.post(f"{BASE_URL}/draw", json={
                            "game_id": game_id,
                            "player": my_player_name
                        }, timeout=2)
                    except:
                        pass

                # Sélection de cible pour destruction
                if selecting_target:
                    for u_data in game_state.get("units", []):
                        if u_data["player"] != my_player_name:
                            x, y = get_screen_pos(u_data["tile_id"])
                            rect = pygame.Rect(x - 30, y - 40, 60, 80)
                            if rect.collidepoint(mouse_pos):
                                with game_state_lock:
                                    if u_data in game_state["units"]:
                                        game_state["units"].remove(u_data)
                                if destroy_cost:
                                    if my_hand:
                                        my_hand.pop(0)
                                        send_card_counts()
                                    destroy_cost = False
                                selecting_target = False
                                break

        # --- DESSIN ---
        screen.blit(map_surface, (MAP_X, MAP_Y))

        # -----------------------------------------------------------
        # DESSIN DES ZONES D'ÉTOILES NON CAPTURÉES
        # -----------------------------------------------------------
        star_font = pygame.font.SysFont("arial", 40)
        for idx, zone in enumerate(star_zones):
            if idx not in claimed_zones:
                zx = MAP_X + int(zone["area"]["x"] * MAP_WIDTH)
                zy = MAP_Y + int(zone["area"]["y"] * MAP_HEIGHT)
                zw = int(zone["area"]["w"] * MAP_WIDTH)
                zh = int(zone["area"]["h"] * MAP_HEIGHT)
                
                # Rectangle et icône
                pygame.draw.rect(screen, (180, 100, 255), (zx, zy, zw, zh), 3, border_radius=8)
                star_char = star_font.render("★", True, (180, 100, 255))
                cx = zx + zw//2 - star_char.get_width()//2
                cy = zy + zh//2 - star_char.get_height()//2
                screen.blit(star_char, (cx, cy))

        # Fin de jeu
        if game_state.get("state") == "finished":
            if victory_start is None:
                victory_start = current_time
                selected_card_index = None
                selecting_target = False
            winner = game_state.get("winner")
                     
            if winner == my_player_name:
                try:
                    supabase.table("games").update([{"win": my_name}]).eq("room_id", game_id).execute()
                except Exception as exception:
                    print(exception)
                result_text = "Victoire !"
            elif winner == "draw":
                result_text = "Match nul..."
            else:
                result_text = "Défaite..."
            result_render = ui_font.render(result_text, True, (255, 220, 120))
            screen.blit(result_render, (WIDTH//2 - result_render.get_width()//2, UI_Y - 80))
            if current_time - victory_start > 5:
                return "mainMenu"

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

        # Dessiner les unités
        for u_data in game_state.get("units", []):
            u = Unit(u_data["tile_id"], u_data["card"], u_data["player"])
            u.draw(screen)

        # UI BAS DU JEU
        pygame.draw.rect(screen, (14, 14, 18), (0, UI_Y - 4, WIDTH, 154), border_radius=8)
        pygame.draw.rect(screen, (70, 70, 90), (0, UI_Y - 4, WIDTH, 154), 2, border_radius=8)

        turn_text = "C'est votre tour !" if game_state.get("turn") == my_player_name else f"Attente de {game_state.get('turn')}..."
        if game_state.get("state") == "waiting": turn_text = "En attente d'un adversaire..."
        
        title = ui_font.render(f"Main ({len(my_hand)} cartes) - Deck: {len(my_deck)}", True, (230, 230, 240))
        turn = ui_font.render(turn_text, True, (210, 210, 220))
        screen.blit(title, (20, UI_Y - 26))
        screen.blit(turn, (20, UI_Y - 26 + title.get_height()))

        for i, card in enumerate(my_hand):
            cx = WIDTH//2 - 150 + i*110
            cy = UI_Y + 20
            is_selected = (i == selected_card_index)
            slot_color = (34, 34, 40) if not is_selected else (40, 50, 70)
            pygame.draw.rect(screen, slot_color, (cx-5, cy-5, 100, 130), border_radius=8)
            try:
                img = get_card_image(card)
                scaled = pygame.transform.scale(img, (90, 120))
                screen.blit(scaled, (cx, cy))
            except:
                pygame.draw.rect(screen, (80, 80, 80), (cx, cy, 90, 120), border_radius=8)
            if is_selected:
                pygame.draw.rect(screen, (255, 215, 0), (cx-5, cy-5, 100, 130), 3, border_radius=8)

        if selected_card_index is not None:
            card = my_hand[selected_card_index]
            desc_text = ui_font.render(card.get("ability_desc", "No description"), True, (255, 230, 180))
            screen.blit(desc_text, (20, UI_Y + 100))

        pygame.draw.rect(screen, (20, 20, 25), (MAP_X + MAP_WIDTH + 10, MAP_Y + 290, 120, 150), border_radius=8)
        screen.blit(pioche_img, (MAP_X + MAP_WIDTH + 20, MAP_Y + 300))

        # -----------------------------------------------------------
        # UI CENTRE GAUCHE - COMPTEUR D'ÉTOILES
        # -----------------------------------------------------------
        stars_panel_rect = pygame.Rect((MAP_X - 160), (MAP_Y + 290), 150, 150)
        pygame.draw.rect(screen, (34, 34, 40), stars_panel_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 215, 0), stars_panel_rect, 2, border_radius=8)
        
        my_stars_txt = ui_font.render(f"Mes étoiles : {player_stars[my_player_name]} ★", True, (255, 215, 0))
        enemy_stars_txt = ui_font.render(f"Ennemi : {player_stars[enemy_player_name]} ★", True, (150, 150, 160))
        
        screen.blit(my_stars_txt, (
            stars_panel_rect.x + 10,
            stars_panel_rect.y + 40
        ))

        screen.blit(enemy_stars_txt, (
            stars_panel_rect.x + 10,
            stars_panel_rect.y + 80
        ))

        systeme_particules.update()
        systeme_particules.draw(screen)

        pygame.display.flip()
        clock.tick(60)