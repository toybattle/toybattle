import pygame
import sys
import json
import random
import time
import Cards
import Effect as Effect
from Utils import load_path

def gameSolo(screen, clock):
    # --- INITIALISATION DES DONNÉES ---
    WIDTH, HEIGHT = screen.get_size()
    
    # Chargement des maps
    try:
        datamap = json.load(open(load_path("data", "map_data.json"), "r"))
        map_index = random.randint(0, len(datamap) - 1)
        map_name = list(datamap.keys())[map_index]
        map_img = pygame.image.load(load_path("assets/map", map_name + ".jpg")).convert()
        water = pygame.image.load(load_path("assets", "water.png")).convert()
        pioche_img = pygame.image.load(load_path("assets", "pioche.png")).convert_alpha()
        pioche_img = pygame.transform.scale(pioche_img, (100, 130))
    except Exception as e:
        print(f"Erreur Assets Game: {e}")
        return "mainMenu"

    pygame.display.set_caption("Toy Battle - Solo vs IA")

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

    map_surface = update_layout(WIDTH, HEIGHT, map_img)

    # --- ZONES D'ÉTOILES ---
    star_zones = datamap[map_name].get("star_zones", [])
    claimed_zones = {}
    player_stars = {'player': 0, 'ia': 0}

    # --- SYSTÈME DE CARTES ---
    deck_player, deck_ia = Cards.init_cards()
    player_hand = Cards.host_cards(deck_player)  # Le joueur commence
    player_deck = deck_player
    ia_hand = Cards.client_cards(deck_ia)
    ia_deck = deck_ia
    
    selected_card_index = None
    current_turn = 'player'  # player ou ia
    victory_start = None
    
    # Plateau de jeu
    units = []  # Liste des unités: {"tile_id": ..., "card": ..., "player": ...}
    
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
    
    # --- FONCTIONS DE JEU ---
    
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

    def get_valid_tiles(units, card, player_name):
        occupied_ids = [u["tile_id"] for u in units]
        unit_on_tile = {u["tile_id"]: u for u in units}
        tile_by_id = {t["id"]: t for t in datamap[map_name]["tiles"]}
        tile_graph = {t["id"]: set() for t in datamap[map_name]["tiles"]}
        for link in datamap[map_name]["links"]:
            tile_graph[link[0]].add(link[1])
            tile_graph[link[1]].add(link[0])
        valid_ids = set()
        
        player_side = "player1" if player_name == 'player' else "player2"

        def is_own_fortress(tile_id):
            tile = tile_by_id.get(tile_id)
            return bool(tile and tile.get("type") == "forteresse" and tile.get("player") == player_side)

        def has_path_to_tile(target_tile_id):
            own_tiles = {u["tile_id"] for u in units if u["player"] == player_name}
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
            if u["player"] == player_name:
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
                if occupying_unit["player"] != player_name:
                    if can_cover(card, occupying_unit["card"]):
                        final_valid.add(tid)
        return list(final_valid)

    def place_unit(tile_id, card_data, player_name):
        nonlocal current_turn
        new_unit = {
            "tile_id": tile_id,
            "card": card_data,
            "player": player_name
        }
        units.append(new_unit)
        
        # Supprimer l'unité recouverte
        for unit in units[:]:
            if unit is not new_unit and unit["tile_id"] == tile_id and unit["player"] != player_name:
                if can_cover(card_data, unit["card"]):
                    units.remove(unit)
        
        # Résoudre les batailles
        resolve_battles(new_unit)
        
        # Appliquer les effets
        change_turn = apply_card_effects(card_data, player_name, tile_id)
        
        # Vérifier victoire
        if check_victory(player_name):
            return True
        
        if change_turn:
            current_turn = 'ia' if player_name == 'player' else 'player'
        
        return False

    def resolve_battles(new_unit):
        card_name = new_unit["card"]["name"]
        card_strength = new_unit["card"].get("strength", 0)
        links = datamap[map_name]["links"]
        
        if "Roxy" in card_name:
            return
        
        if "Mastok" in card_name:
            return
        
        if "Crochet" in card_name:
            return
        
        # Trouver les unités adjacentes
        adjacent_tiles = set()
        for link in links:
            if link[0] == new_unit["tile_id"]:
                adjacent_tiles.add(link[1])
            elif link[1] == new_unit["tile_id"]:
                adjacent_tiles.add(link[0])
        
        top_units_by_tile = {}
        for unit in units:
            top_units_by_tile[unit["tile_id"]] = unit
        
        units_to_remove = []
        for tile_id in adjacent_tiles:
            unit = top_units_by_tile.get(tile_id)
            if not unit or unit["player"] == new_unit["player"]:
                continue
            
            if "Roxy" in unit["card"].get("name", ""):
                continue
            
            if card_strength > unit["card"].get("strength", 0):
                units_to_remove.append(unit)
        
        for unit in units_to_remove:
            if unit in units:
                units.remove(unit)

    def apply_card_effects(card_data, player_name, tile_id):
        card_name = card_data.get("name", "")
        change_turn = True
        
        if "Cap'taine" in card_name or "Captain" in card_name:
            change_turn = False
        
        elif "Skully" in card_name:
            draw_count = min(2, len(player_deck if player_name == 'player' else ia_deck), 
                           max(0, 8 - len(player_hand if player_name == 'player' else ia_hand)))
            for _ in range(draw_count):
                if player_name == 'player' and player_deck:
                    player_hand.append(player_deck.pop(0))
                elif player_name == 'ia' and ia_deck:
                    ia_hand.append(ia_deck.pop(0))
        
        elif "Star" in card_name:
            hand = player_hand if player_name == 'player' else ia_hand
            deck = player_deck if player_name == 'player' else ia_deck
            if deck and len(hand) < 8:
                hand.append(deck.pop(0))
        
        elif "XB-42" in card_name or "XB42" in card_name:
            opponent_hand = ia_hand if player_name == 'player' else player_hand
            if opponent_hand:
                random_index = random.randint(0, len(opponent_hand) - 1)
                opponent_hand.pop(random_index)
        
        elif "Mastok" in card_name:
            # Trouver les cibles adjacentes
            adjacent_ids = set()
            for link in datamap[map_name]["links"]:
                if tile_id in link:
                    adjacent_ids.add(link[0] if link[1] == tile_id else link[1])
            
            valid_targets = [u for u in units if u["player"] != player_name and u["tile_id"] in adjacent_ids]
            if valid_targets:
                target = random.choice(valid_targets)
                units.remove(target)
        
        return change_turn

    def check_victory(player_name):
        # Vérifier victoire par forteresse
        for unit in units:
            if unit["player"] != player_name:
                continue
            for tile in datamap[map_name]["tiles"]:
                if tile["id"] == unit["tile_id"] and tile.get("type") == "forteresse":
                    opponent_side = "player2" if player_name == 'player' else "player1"
                    if tile.get("player") == opponent_side:
                        if has_path_to_fortress(unit["tile_id"], player_name):
                            return True
        
        # Vérifier victoire par étoiles
        player_star_count = get_player_star_count(player_name)
        required_stars = datamap[map_name].get("num_stars", 7)
        if player_star_count >= required_stars:
            return True
        
        return False

    def has_path_to_fortress(fortress_tile_id, player_name):
        owned_tiles = {u["tile_id"] for u in units if u["player"] == player_name}
        player_side = "player1" if player_name == 'player' else "player2"
        
        start_tiles = {
            t["id"] for t in datamap[map_name]["tiles"]
            if t["type"] == "start" and t.get("player") == player_side and t["id"] in owned_tiles
        }
        
        if not start_tiles:
            return False
        
        tile_graph = {t["id"]: set() for t in datamap[map_name]["tiles"]}
        for link in datamap[map_name]["links"]:
            tile_graph[link[0]].add(link[1])
            tile_graph[link[1]].add(link[0])
        
        visited = set(start_tiles)
        queue = list(start_tiles)
        while queue:
            current = queue.pop(0)
            for neighbor in tile_graph.get(current, set()):
                if neighbor == fortress_tile_id:
                    return True
                if neighbor in owned_tiles and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def get_player_star_count(player_name):
        tile_owners = {u["tile_id"]: u["player"] for u in units}
        count = 0
        for zone in star_zones:
            req_tiles = zone.get("required_tiles", [])
            if not req_tiles:
                continue
            owner = tile_owners.get(req_tiles[0])
            if owner and all(tile_owners.get(tid) == owner for tid in req_tiles):
                if owner == player_name:
                    count += 1
        return count

    def update_star_zones():
        nonlocal claimed_zones, player_stars
        tile_owners = {u["tile_id"]: u["player"] for u in units}
        
        for idx, zone in enumerate(star_zones):
            if idx not in claimed_zones:
                req_tiles = zone.get("required_tiles", [])
                if not req_tiles:
                    continue
                
                first_tile_owner = tile_owners.get(req_tiles[0])
                if first_tile_owner:
                    if all(tile_owners.get(t) == first_tile_owner for t in req_tiles):
                        claimed_zones[idx] = first_tile_owner
                        player_stars[first_tile_owner] += 1
                        
                        # Effet visuel
                        zx = MAP_X + int((zone["area"]["x"] + zone["area"]["w"]/2) * MAP_WIDTH)
                        zy = MAP_Y + int((zone["area"]["y"] + zone["area"]["h"]/2) * MAP_HEIGHT)
                        systeme_particules.create_particles(zx, zy, nombre=60)

    def ia_turn():
        nonlocal current_turn
        time.sleep(0.5)  # Petit délai pour que l'IA paraisse naturelle
        
        if not ia_hand:
            # Piocher si possible
            if ia_deck:
                draw_count = min(2, len(ia_deck), 8 - len(ia_hand))
                for _ in range(draw_count):
                    ia_hand.append(ia_deck.pop(0))
            else:
                current_turn = 'player'
                return
        
        # Sélectionner une carte aléatoire
        card_index = random.randint(0, len(ia_hand) - 1)
        card = ia_hand[card_index]
        
        # Trouver les tuiles valides
        valid_tiles = get_valid_tiles(units, card, 'ia')
        
        if valid_tiles:
            # Choisir une tuile aléatoire
            tile_id = random.choice(valid_tiles)
            
            # Placer l'unité
            victory = place_unit(tile_id, card, 'ia')
            
            # Retirer la carte de la main
            ia_hand.pop(card_index)
            
            # Effet visuel
            x, y = get_screen_pos(tile_id)
            systeme_particules.create_particles(x, y, nombre=40)
            
            if victory:
                return
            
            # Pioche après avoir joué (si main < 8)
            if len(ia_hand) < 8 and ia_deck:
                draw_count = min(2, len(ia_deck), 8 - len(ia_hand))
                for _ in range(draw_count):
                    ia_hand.append(ia_deck.pop(0))
        else:
            # Si aucune tuile valide, l'IA pioche et passe son tour
            if ia_deck and len(ia_hand) < 8:
                draw_count = min(2, len(ia_deck), 8 - len(ia_hand))
                for _ in range(draw_count):
                    ia_hand.append(ia_deck.pop(0))
            current_turn = 'player'

    class Unit:
        def __init__(self, tile_id, card_data, owner):
            self.tile_id = tile_id
            self.card_data = card_data
            self.owner = owner
            self.image = get_card_image(card_data)

        def draw(self, surf, highlight=False):
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
            if highlight:
                pygame.draw.rect(surf, (255, 80, 80), rect.inflate(10, 10), 4, border_radius=10)

            if self.owner == 'player':
                outline_rect = rect.inflate(8, 8)
                pygame.draw.rect(surf, (255, 215, 0), outline_rect, 3, border_radius=10)

    # --- BOUCLE PRINCIPALE ---
    last_ia_time = 0
    ia_delay = 0.5  # Délai avant que l'IA joue
    
    while True:
        current_time = time.time()
        
        # Mettre à jour les zones d'étoiles
        update_star_zones()
        
        # Gestion de l'IA
        if current_turn == 'ia' and not victory_start:
            if last_ia_time == 0:
                last_ia_time = current_time
            elif current_time - last_ia_time >= ia_delay:
                ia_turn()
                last_ia_time = 0
        
        # --- GESTION DES ÉVÉNEMENTS ---
        screen.fill((30, 30, 35))
        mouse_pos = pygame.mouse.get_pos()
        ui_font = pygame.font.SysFont("arial", 24)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "mainMenu"
                
            if event.type == pygame.VIDEORESIZE:
                map_surface = update_layout(event.w, event.h, map_img)

            if event.type == pygame.MOUSEBUTTONDOWN and current_turn == 'player' and not victory_start:
                # Sélection de carte dans la main
                for i in range(len(player_hand)):
                    rect = pygame.Rect(WIDTH//2 - 150 + i*110, UI_Y + 20, 90, 120)
                    if rect.collidepoint(mouse_pos):
                        selected_card_index = i
                
                # Placement sur la Map
                if selected_card_index is not None:
                    current_card = player_hand[selected_card_index]
                    valid_ids = get_valid_tiles(units, current_card, 'player')
                    
                    for tile in datamap[map_name]["tiles"]:
                        tr = pygame.Rect(MAP_X + tile["x"]*MAP_WIDTH, MAP_Y + tile["y"]*MAP_HEIGHT, 
                                       tile["w"]*MAP_WIDTH, tile["h"]*MAP_HEIGHT)
                        
                        if tr.collidepoint(mouse_pos) and tile["id"] in valid_ids:
                            victory = place_unit(tile["id"], player_hand[selected_card_index], 'player')
                            
                            x, y = get_screen_pos(tile["id"])
                            systeme_particules.create_particles(x, y, nombre=40)
                            
                            player_hand.pop(selected_card_index)
                            selected_card_index = None
                            
                            if victory:
                                break
                            
                            # Pioche après avoir joué
                            if len(player_hand) < 8 and player_deck:
                                draw_count = min(2, len(player_deck), 8 - len(player_hand))
                                for _ in range(draw_count):
                                    player_hand.append(player_deck.pop(0))
                            
                            break
                
                # Click sur la pioche
                pioche_rect = pygame.Rect(MAP_X + MAP_WIDTH + 20, MAP_Y + 300, 100, 130)
                if (pioche_rect.collidepoint(mouse_pos) and 
                    current_turn == 'player' and 
                    not victory_start and 
                    len(player_hand) < 8):
                    draw_count = min(2, len(player_deck), 8 - len(player_hand))
                    for _ in range(draw_count):
                        player_hand.append(player_deck.pop(0))

        # --- DESSIN ---
        screen.blit(map_surface, (MAP_X, MAP_Y))

        # Dessiner les zones d'étoiles non capturées
        star_font = pygame.font.SysFont("arial", 40)
        for idx, zone in enumerate(star_zones):
            if idx not in claimed_zones:
                zx = MAP_X + int(zone["area"]["x"] * MAP_WIDTH)
                zy = MAP_Y + int(zone["area"]["y"] * MAP_HEIGHT)
                zw = int(zone["area"]["w"] * MAP_WIDTH)
                zh = int(zone["area"]["h"] * MAP_HEIGHT)
                
                pygame.draw.rect(screen, (180, 100, 255), (zx, zy, zw, zh), 3, border_radius=8)
                star_char = star_font.render("★", True, (180, 100, 255))
                cx = zx + zw//2 - star_char.get_width()//2
                cy = zy + zh//2 - star_char.get_height()//2
                screen.blit(star_char, (cx, cy))

        # Vérifier victoire
        if victory_start is None:
            winner = None
            if check_victory('player'):
                winner = 'player'
                victory_start = current_time
                selected_card_index = None
            elif check_victory('ia'):
                winner = 'ia'
                victory_start = current_time
        
        # Affichage fin de jeu
        if victory_start:
            if winner == 'player':
                result_text = "Victoire !"
            else:
                result_text = "Défaite..."
            result_render = ui_font.render(result_text, True, (255, 220, 120))
            screen.blit(result_render, (WIDTH//2 - result_render.get_width()//2, UI_Y - 80))
            if current_time - victory_start > 5:
                return "mainMenu"

        # Surbrillance des cases valides
        if selected_card_index is not None and current_turn == 'player' and not victory_start:
            current_card = player_hand[selected_card_index]
            valid_ids = get_valid_tiles(units, current_card, 'player')
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
        for u_data in units:
            u = Unit(u_data["tile_id"], u_data["card"], u_data["player"])
            u.draw(screen)

        # UI bas du jeu
        pygame.draw.rect(screen, (14, 14, 18), (0, UI_Y - 4, WIDTH, 154), border_radius=8)
        pygame.draw.rect(screen, (70, 70, 90), (0, UI_Y - 4, WIDTH, 154), 2, border_radius=8)

        turn_text = "Votre tour !" if current_turn == 'player' else "Tour de l'IA..."
        if victory_start:
            turn_text = "Partie terminée"
        
        title = ui_font.render(f"Main ({len(player_hand)} cartes) - Deck: {len(player_deck)}", True, (230, 230, 240))
        turn = ui_font.render(turn_text, True, (210, 210, 220))
        screen.blit(title, (20, UI_Y - 26))
        screen.blit(turn, (20, UI_Y - 26 + title.get_height()))

        # Dessiner les cartes du joueur
        for i, card in enumerate(player_hand):
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

        # Description de la carte sélectionnée
        if selected_card_index is not None and not victory_start:
            card = player_hand[selected_card_index]
            desc_text = ui_font.render(card.get("ability_desc", "No description"), True, (255, 230, 180))
            screen.blit(desc_text, (20, UI_Y + 100))

        # Pioche
        pygame.draw.rect(screen, (20, 20, 25), (MAP_X + MAP_WIDTH + 10, MAP_Y + 290, 120, 150), border_radius=8)
        screen.blit(pioche_img, (MAP_X + MAP_WIDTH + 20, MAP_Y + 300))

        # UI des étoiles
        stars_panel_rect = pygame.Rect((MAP_X - 160), (MAP_Y + 290), 150, 150)
        pygame.draw.rect(screen, (34, 34, 40), stars_panel_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 215, 0), stars_panel_rect, 2, border_radius=8)
        
        my_stars_txt = ui_font.render(f"Mes étoiles : {player_stars['player']} ★", True, (255, 215, 0))
        enemy_stars_txt = ui_font.render(f"IA : {player_stars['ia']} ★", True, (150, 150, 160))
        
        screen.blit(my_stars_txt, (stars_panel_rect.x + 10, stars_panel_rect.y + 40))
        screen.blit(enemy_stars_txt, (stars_panel_rect.x + 10, stars_panel_rect.y + 80))

        # Afficher le nombre de cartes de l'IA
        ia_info = ui_font.render(f"IA: {len(ia_hand)} cartes", True, (200, 200, 200))
        screen.blit(ia_info, (MAP_X + MAP_WIDTH - 100, MAP_Y + 10))

        systeme_particules.update()
        systeme_particules.draw(screen)

        pygame.display.flip()
        clock.tick(60)