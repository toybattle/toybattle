import pygame
import sys
import json
import random
import time
import Cards
import Effect as Effect
from Utils import load_path


def encode_action(card, tile, units, player_name, datamap, map_name, player_stars):
    score = card.get("strength", 0) * 2
    desc = card.get("ability_desc", "")
    if "Piocher 2 cartes" in desc:
        score += 4
    if "Rejouer immédiatement" in desc:
        score += 3
    if "Détruit une tuile adverse" in desc or "Supprime une des tuiles adverses" in desc:
        score += 5
    if "Pioche une seule tuile" in desc:
        score += 2
    if "Va n'importe où" in desc:
        score += 2
    if "Roxy" in card.get("name", ""):
        score += 2
    if "Kwak" in card.get("name", ""):
        score += 2

    tile_type = tile.get("type", "normal")
    if tile_type == "start":
        score += 1
    if tile_type == "forteresse":
        score += 3

    owner = tile.get("player")
    if owner is not None and owner != player_name:
        score += 4

    neighbors = [link for link in datamap[map_name]["links"] if tile["id"] in link]
    neighbor_ids = {n for link in neighbors for n in link if n != tile["id"]}
    friendly_neighbors = sum(1 for uid in neighbor_ids if any(u["tile_id"] == uid and u["player"] == player_name for u in units))
    enemy_neighbors = sum(1 for uid in neighbor_ids if any(u["tile_id"] == uid and u["player"] != player_name for u in units))
    score += friendly_neighbors * 0.5
    score += enemy_neighbors * 0.7

    for zone in datamap[map_name].get("star_zones", []):
        if tile["id"] in zone.get("required_tiles", []):
            score += 2

    star_balance = player_stars.get(player_name, 0) - player_stars.get("player1" if player_name == "player2" else "player2", 0)
    score -= star_balance * 0.5
    return score


def gameSolo(screen, clock):
    WIDTH, HEIGHT = screen.get_size()
    pygame.display.set_caption("Toy Battle - Solo")

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

    try:
        datamap = json.load(open(load_path("data", "map_data.json"), "r", encoding="utf-8"))
        map_name = list(datamap.keys())[0]
        map_img = pygame.image.load(load_path("assets/map", map_name + ".jpg")).convert()
        pioche_img = pygame.image.load(load_path("assets", "pioche.png")).convert_alpha()
        pioche_img = pygame.transform.scale(pioche_img, (100, 130))
    except Exception as e:
        print(f"Erreur Assets GameSolo: {e}")
        return "mainMenu"

    map_surface = update_layout(WIDTH, HEIGHT, map_img)

    star_zones = datamap[map_name].get("star_zones", [])
    claimed_zones = {}
    player_stars = {"player1": 0, "player2": 0}

    deck_host, deck_client = Cards.init_cards()
    my_hand = Cards.host_cards(deck_host)
    ai_hand = Cards.client_cards(deck_client)
    my_deck = deck_host
    ai_deck = deck_client

    selected_card_index = None
    selecting_target = False
    pending_target_card = None
    pending_target_owner = None
    destroy_cost = False
    victory_start = None
    game_state = "playing"
    winner = None
    can_play_extra = False

    card_image_cache = {}

    def get_card_image(card):
        img_path = card["image_path"]
        if img_path not in card_image_cache:
            try:
                card_image_cache[img_path] = pygame.image.load(load_path("assets/cards", img_path)).convert_alpha()
            except Exception:
                surface = pygame.Surface((90, 120), pygame.SRCALPHA)
                surface.fill((80, 80, 80))
                card_image_cache[img_path] = surface
        return card_image_cache[img_path]

    systeme_particules = Effect.SystemeParticules()
    current_turn = "player1"
    ai_wait_frames = 0
    frame_count = 0

    def get_screen_pos(tile_id):
        tile = next(t for t in datamap[map_name]["tiles"] if t["id"] == tile_id)
        tx = MAP_X + int((tile["x"] + tile["w"] / 2) * MAP_WIDTH)
        ty = MAP_Y + int((tile["y"] + tile["h"] / 2) * MAP_HEIGHT)
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
        return new_card.get("strength", 0) > occupying_card.get("strength", 0)

    def get_valid_tiles(units, card, player_name="player1"):
        occupied_ids = [u["tile_id"] for u in units]
        unit_on_tile = {u["tile_id"]: u for u in units}
        tile_graph = {t["id"]: set() for t in datamap[map_name]["tiles"]}
        for link in datamap[map_name]["links"]:
            tile_graph[link[0]].add(link[1])
            tile_graph[link[1]].add(link[0])

        def is_own_fortress(tile_id):
            tile = next((t for t in datamap[map_name]["tiles"] if t["id"] == tile_id), None)
            return bool(tile and tile.get("type") == "forteresse" and tile.get("player") == player_name)

        def has_path_to_tile(target_tile_id):
            own_tiles = {u["tile_id"] for u in units if u["player"] == player_name}
            start_tiles = {
                t["id"] for t in datamap[map_name]["tiles"]
                if t["type"] == "start" and t.get("player") == player_name and t["id"] in own_tiles
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

        valid_ids = set()
        for tile in datamap[map_name]["tiles"]:
            if tile["type"] == "start" and tile.get("player") == player_name:
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

        if "Crochet" in card.get("name", ""):
            valid_ids = {t["id"] for t in datamap[map_name]["tiles"] if not is_own_fortress(t["id"])}

        final_valid = set()
        for tid in valid_ids:
            tile = next((t for t in datamap[map_name]["tiles"] if t["id"] == tid), None)
            if tile and tile.get("type") == "forteresse" and tile.get("player") != player_name:
                if not has_path_to_tile(tid):
                    continue
            if tid not in occupied_ids:
                final_valid.add(tid)
            else:
                occupying_unit = unit_on_tile[tid]
                if occupying_unit["player"] != player_name and can_cover(card, occupying_unit["card"]):
                    final_valid.add(tid)
        return list(final_valid)

    def execute_ability(card, owner, units, hand, deck):
        nonlocal selecting_target, destroy_cost, pending_target_card, pending_target_owner, can_play_extra
        desc = card.get("ability_desc", "")
        if "Piocher 2 cartes" in desc:
            draw_count = min(2, len(deck), max(0, 8 - len(hand)))
            for _ in range(draw_count):
                hand.append(deck.pop(0))
        elif "Pioche une seule tuile" in desc:
            if deck and len(hand) < 8:
                hand.append(deck.pop(0))
        elif "Rejouer immédiatement" in desc:
            can_play_extra = True
        elif "Détruit une tuile adverse" in desc or "Supprime une des tuiles adverses" in desc:
            selecting_target = True
            pending_target_card = card
            pending_target_owner = owner
            if "supprime la tuile du dessus" in desc:
                destroy_cost = True
        return None

    class Unit:
        def __init__(self, tile_id, card_data, owner):
            self.tile_id = tile_id
            self.card_data = card_data
            self.owner = owner
            try:
                self.image = pygame.image.load(load_path("assets/cards", card_data["image_path"])) .convert_alpha()
            except Exception:
                self.image = pygame.Surface((90, 120), pygame.SRCALPHA)
                self.image.fill((80, 80, 80))

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
                highlight_rect = rect.inflate(12, 12)
                pygame.draw.rect(surf, (255, 80, 80), highlight_rect, 4, border_radius=10)
            border = (255, 215, 0) if self.owner == "player1" else (220, 80, 80)
            pygame.draw.rect(surf, border, rect.inflate(6, 6), 3, border_radius=10)

    def claim_star_zones(units):
        nonlocal player_stars
        tile_owners = {u["tile_id"]: u["player"] for u in units}
        for idx, zone in enumerate(star_zones):
            if idx in claimed_zones:
                continue
            req_tiles = zone.get("required_tiles", [])
            if not req_tiles:
                continue
            first_owner = tile_owners.get(req_tiles[0])
            if first_owner and all(tile_owners.get(t) == first_owner for t in req_tiles):
                claimed_zones[idx] = first_owner
                player_stars[first_owner] += 1
                zx = MAP_X + int((zone["area"]["x"] + zone["area"]["w"] / 2) * MAP_WIDTH)
                zy = MAP_Y + int((zone["area"]["y"] + zone["area"]["h"] / 2) * MAP_HEIGHT)
                systeme_particules.create_particles(zx, zy, nombre=80)

    def game_over_check(units):
        if any(player_stars[p] >= 4 for p in player_stars):
            return True
        if not my_deck and not ai_deck and not my_hand and not ai_hand:
            return True
        return False

    def decide_winner():
        if player_stars["player1"] > player_stars["player2"]:
            return "player1"
        if player_stars["player2"] > player_stars["player1"]:
            return "player2"
        return "draw"

    def remove_enemy_unit(owner, units):
        enemy_units = [u for u in units if u["player"] != owner]
        if not enemy_units:
            return False
        strongest = max(enemy_units, key=lambda u: u["card"].get("strength", 0))
        units.remove(strongest)
        return True

    def get_action_score(card, tile_id, units, player_name):
        tile = next((t for t in datamap[map_name]["tiles"] if t["id"] == tile_id), None)
        if tile is None:
            return float("-inf")
        return encode_action(card, tile, units, player_name, datamap, map_name, player_stars)

    def ai_take_turn(units):
        nonlocal current_turn, can_play_extra, ai_wait_frames
        if not ai_hand:
            if ai_deck and len(ai_hand) < 8:
                ai_hand.append(ai_deck.pop(0))
            current_turn = "player1"
            return

        best_move = None
        for idx, card in enumerate(ai_hand):
            valid_tiles = get_valid_tiles(units, card, "player2")
            for tile_id in valid_tiles:
                score = get_action_score(card, tile_id, units, "player2")
                if best_move is None or score > best_move[0]:
                    best_move = (score, idx, card, tile_id)

        if best_move is None:
            if ai_deck and len(ai_hand) < 8:
                ai_hand.append(ai_deck.pop(0))
            current_turn = "player1"
            return

        _, card_index, card, tile_id = best_move
        occupying = next((u for u in units if u["tile_id"] == tile_id), None)
        if occupying and occupying["player"] != "player2" and can_cover(card, occupying["card"]):
            units.remove(occupying)

        units.append({"tile_id": tile_id, "card": card, "player": "player2"})
        ai_hand.pop(card_index)
        execute_ability(card, "player2", units, ai_hand, ai_deck)
        x, y = get_screen_pos(tile_id)
        systeme_particules.create_particles(x, y, nombre=40)

        if pending_target_card and pending_target_owner == "player2":
            remove_enemy_unit("player2", units)
            if destroy_cost and ai_hand:
                ai_hand.pop(0)
            reset_pending_target()

        if can_play_extra:
            can_play_extra = False
            current_turn = "player2"
            ai_wait_frames = 30
        else:
            current_turn = "player1"

    def reset_pending_target():
        nonlocal selecting_target, pending_target_card, pending_target_owner, destroy_cost
        selecting_target = False
        pending_target_card = None
        pending_target_owner = None
        destroy_cost = False

    units = []

    while True:
        frame_count += 1
        if game_state == "playing":
            claim_star_zones(units)
            if game_over_check(units):
                game_state = "finished"
                winner = decide_winner()
                victory_start = time.time()

        screen.fill((30, 30, 35))
        mouse_pos = pygame.mouse.get_pos()
        ui_font = pygame.font.SysFont("arial", 24)
        title_font = pygame.font.SysFont("arial", 28, bold=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((max(760, event.w), max(620, event.h)), pygame.RESIZABLE)
                map_surface = update_layout(screen.get_width(), screen.get_height(), map_img)
            if event.type == pygame.MOUSEBUTTONDOWN and current_turn == "player1" and game_state == "playing":
                if selecting_target:
                    for u in units:
                        if u["player"] == "player2":
                            x, y = get_screen_pos(u["tile_id"])
                            rect = pygame.Rect(x - 30, y - 40, 60, 80)
                            if rect.collidepoint(mouse_pos):
                                units.remove(u)
                                if destroy_cost and my_hand:
                                    my_hand.pop(0)
                                reset_pending_target()
                                if can_play_extra:
                                    current_turn = "player1"
                                else:
                                    current_turn = "player2"
                                break
                    continue

                for i in range(len(my_hand)):
                    rect = pygame.Rect(WIDTH // 2 - 150 + i * 110, UI_Y + 20, 90, 120)
                    if rect.collidepoint(mouse_pos):
                        selected_card_index = i

                if selected_card_index is not None:
                    current_card = my_hand[selected_card_index]
                    valid_tiles = get_valid_tiles(units, current_card, "player1")
                    for tile in datamap[map_name]["tiles"]:
                        tr = pygame.Rect(MAP_X + tile["x"] * MAP_WIDTH, MAP_Y + tile["y"] * MAP_HEIGHT,
                                         tile["w"] * MAP_WIDTH, tile["h"] * MAP_HEIGHT)
                        if tr.collidepoint(mouse_pos) and tile["id"] in valid_tiles:
                            occupying = next((u for u in units if u["tile_id"] == tile["id"]), None)
                            if occupying and occupying["player"] != "player1" and not can_cover(current_card, occupying["card"]):
                                continue
                            if occupying and occupying["player"] != "player1":
                                units.remove(occupying)
                            units.append({"tile_id": tile["id"], "card": current_card, "player": "player1"})
                            my_hand.pop(selected_card_index)
                            execute_ability(current_card, "player1", units, my_hand, my_deck)
                            x, y = get_screen_pos(tile["id"])
                            systeme_particules.create_particles(x, y, nombre=40)
                            selected_card_index = None
                            if not selecting_target:
                                if can_play_extra:
                                    can_play_extra = False
                                    current_turn = "player1"
                                else:
                                    current_turn = "player2"
                            break

                pioche_rect = pygame.Rect(MAP_X + MAP_WIDTH + 20, MAP_Y + 300, 100, 130)
                if pioche_rect.collidepoint(mouse_pos) and len(my_hand) < 8 and my_deck:
                    draw_count = min(2, len(my_deck), 8 - len(my_hand))
                    for _ in range(draw_count):
                        my_hand.append(my_deck.pop(0))
                    current_turn = "player2"

        if current_turn == "player2" and game_state == "playing":
            ai_wait_frames = max(0, ai_wait_frames - 1)
            if ai_wait_frames == 0:
                ai_take_turn(units)

        screen.blit(map_surface, (MAP_X, MAP_Y))

        star_font = pygame.font.SysFont("arial", 36)
        for idx, zone in enumerate(star_zones):
            if idx not in claimed_zones:
                zx = MAP_X + int(zone["area"]["x"] * MAP_WIDTH)
                zy = MAP_Y + int(zone["area"]["y"] * MAP_HEIGHT)
                zw = int(zone["area"]["w"] * MAP_WIDTH)
                zh = int(zone["area"]["h"] * MAP_HEIGHT)
                pygame.draw.rect(screen, (180, 100, 255), (zx, zy, zw, zh), 3, border_radius=8)
                star_char = star_font.render("★", True, (180, 100, 255))
                screen.blit(star_char, (zx + zw // 2 - star_char.get_width() // 2, zy + zh // 2 - star_char.get_height() // 2))

        for u in units:
            unit = Unit(u["tile_id"], u["card"], u["player"])
            unit.draw(screen, highlight=(selecting_target and u["player"] != "player1"))

        pygame.draw.rect(screen, (14, 14, 18), (0, UI_Y - 4, WIDTH, 154), border_radius=8)
        pygame.draw.rect(screen, (70, 70, 90), (0, UI_Y - 4, WIDTH, 154), 2, border_radius=8)

        if game_state == "playing":
            turn_text = "Votre tour" if current_turn == "player1" else "Tour de l'IA"
        else:
            turn_text = "Fin de la partie"
        screen.blit(title_font.render(turn_text, True, (230, 230, 240)), (20, UI_Y - 26))
        screen.blit(ui_font.render(f"Main: {len(my_hand)} cartes  Deck: {len(my_deck)}", True, (210, 210, 220)), (20, UI_Y + 20))
        screen.blit(ui_font.render(f"IA - Main: {len(ai_hand)} cartes  Deck: {len(ai_deck)}", True, (210, 210, 220)), (20, UI_Y + 50))
        screen.blit(ui_font.render(f"Etoiles: Vous {player_stars['player1']} - IA {player_stars['player2']}", True, (255, 215, 0)), (20, UI_Y + 80))

        if selected_card_index is not None and current_turn == "player1":
            card = my_hand[selected_card_index]
            desc = ui_font.render(card.get("ability_desc", ""), True, (255, 230, 180))
            screen.blit(desc, (20, UI_Y + 110))
            valid_tiles = get_valid_tiles(units, card, "player1")
            for tile in datamap[map_name]["tiles"]:
                if tile["id"] in valid_tiles:
                    sx = MAP_X + int(tile["x"] * MAP_WIDTH)
                    sy = MAP_Y + int(tile["y"] * MAP_HEIGHT)
                    sw = int(tile["w"] * MAP_WIDTH)
                    sh = int(tile["h"] * MAP_HEIGHT)
                    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    color = (0, 150, 255, 100) if "Crochet" in card.get("name", "") else (0, 255, 100, 100)
                    pygame.draw.rect(overlay, color, (0, 0, sw, sh), border_radius=6)
                    screen.blit(overlay, (sx, sy))

        for i, card in enumerate(my_hand):
            cx = WIDTH // 2 - 150 + i * 110
            cy = UI_Y + 20
            pygame.draw.rect(screen, (34, 34, 40), (cx - 5, cy - 5, 100, 130), border_radius=8)
            img = get_card_image(card)
            screen.blit(pygame.transform.scale(img, (90, 120)), (cx, cy))
            if i == selected_card_index:
                pygame.draw.rect(screen, (255, 215, 0), (cx - 5, cy - 5, 100, 130), 3, border_radius=8)

        pygame.draw.rect(screen, (20, 20, 25), (MAP_X + MAP_WIDTH + 10, MAP_Y + 290, 120, 150), border_radius=8)
        screen.blit(pioche_img, (MAP_X + MAP_WIDTH + 20, MAP_Y + 300))

        if selecting_target:
            prompt = ui_font.render("Sélectionnez une tuile adverse à détruire", True, (255, 120, 120))
            screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, UI_Y - 80))

        if game_state == "finished":
            if winner == "player1":
                result = "Victoire !"
            elif winner == "player2":
                result = "Défaite..."
            else:
                result = "Match nul"
            result_render = title_font.render(result, True, (255, 220, 120))
            screen.blit(result_render, (WIDTH // 2 - result_render.get_width() // 2, UI_Y - 80))
            if time.time() - victory_start > 5:
                return "mainMenu"

        systeme_particules.update()
        systeme_particules.draw(screen)
        pygame.display.flip()
        clock.tick(60)
