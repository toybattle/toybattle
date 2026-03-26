import pygame
import sys
import json
import Cards
import Test.Effect as Effect
import random

# --- INITIALISATION ---
pygame.init()
info = pygame.display.Info()
WIDTH = min(1100, max(800, info.current_w - 120))
HEIGHT = min(900, max(650, info.current_h - 120))
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Toy Battle")
mapIndex = 1

# --- LAYOUT DYNAMIQUE ---
UI_Y = HEIGHT - 150
MAP_HEIGHT = int(HEIGHT * 0.72)
ratio = 1.0  # mis à jour après chargement de la map
MAP_WIDTH = 0
MAP_X = 0
MAP_Y = 20
map_surface = None


def update_layout():
    global WIDTH, HEIGHT, UI_Y, MAP_HEIGHT, MAP_WIDTH, MAP_X, MAP_Y, map_surface, ratio
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


# --- CHARGEMENT ---
try:
    datamap = json.load(open("data/map_data.json", "r"))
    mapName = list(datamap.keys())[mapIndex]
    map_img = pygame.image.load(datamap[mapName]["image_path"]).convert()
    water = pygame.image.load("assets/water.png").convert()
    pioche = pygame.image.load("assets/pioche.png").convert_alpha()
except Exception as e:
    print(f"Erreur Assets: {e}")
    sys.exit()

# --- CONFIGURATION DIMENSIONS ---
update_layout()

# --- Poiche Dimensions ---
pioche = pygame.transform.scale(pioche, (100, 130))

# --- SYSTÈME DE CARTES ---
# Joueur 1 (humain) et Joueur 2 (IA)
deck_host, deck_enemy = Cards.init_cards()
hand = Cards.host_cards(deck_host)
hand_enemy = Cards.host_cards(deck_enemy)
selected_card_index = None

# Tour et temporisation IA
player_turn = True
ai_wait = 0

# --- EFFETS ---
systeme_particules = Effect.SystemeParticules()

# --- LOGIQUE DE PLACEMENT ---

def get_screen_pos(tile_id):
    tile = next(t for t in datamap[mapName]["tiles"] if t["id"] == tile_id)
    tx = MAP_X + int((tile["x"] + tile["w"]/2) * MAP_WIDTH)
    ty = MAP_Y + int((tile["y"] + tile["h"]/2) * MAP_HEIGHT)
    return tx, ty

def can_cover(new_card, occupying_card):
    if occupying_card is None:
        return True
    occupying_name = occupying_card.get("name", "")
    new_name = new_card.get("name", "")
    # Kwak recouvre absolument tout, y compris Roxy
    if "Kwak" in new_name:
        return True
    # Roxy reste invincible contre toutes les autres
    if "Roxy" in occupying_name:
        return False
    # Autres comparaisons (force)
    new_strength = new_card.get("strength", 0)
    occupying_strength = occupying_card.get("strength", 0)
    return new_strength > occupying_strength

def execute_ability(card, owner, active_units, hand, deck):
    desc = card.get("ability_desc", "")
    replay = False
    if "Piocher 2 cartes" in desc:
        for _ in range(2):
            if deck:
                hand.append(deck.pop(0))
    elif "Rejouer immédiatement" in desc:
        replay = True
    elif "Détruit une tuile adverse" in desc:
        enemy_units = [u for u in active_units if u.player != owner]
        if enemy_units:
            to_remove = random.choice(enemy_units)
            active_units.remove(to_remove)
        if hand:
            hand.pop(0)
    elif "Supprime une des tuiles adverses" in desc:
        enemy_units = [u for u in active_units if u.player != owner]
        if enemy_units:
            to_remove = random.choice(enemy_units)
            active_units.remove(to_remove)
    elif "Pioche une seule tuile" in desc:
        if deck:
            hand.append(deck.pop(0))
    return replay

def get_valid_tiles(active_units, card, player="player1"):
    occupied_ids = [u.tile_id for u in active_units]
    unit_on_tile = {u.tile_id: u for u in active_units}
    valid_ids = set()
    # Standard valid: points de départ et liens du joueur
    for tile in datamap[mapName]["tiles"]:
        if tile["type"] == "start" and tile.get("player") == player:
            valid_ids.add(tile["id"])
    player_unit_ids = [u.tile_id for u in active_units if u.player == player]
    for tile_id in player_unit_ids:
        for link in datamap[mapName]["links"]:
            if link[0] == tile_id:
                valid_ids.add(link[1])
            elif link[1] == tile_id:
                valid_ids.add(link[0])
    standard_valid = valid_ids.copy()
    if "Crochet" in card.get("name", ""):
        valid_ids = set(t["id"] for t in datamap[mapName]["tiles"])
    else:
        valid_ids = standard_valid
    final_valid = set()
    for tid in valid_ids:
        if tid not in occupied_ids:
            final_valid.add(tid)
        else:
            occupying = unit_on_tile[tid].card_data
            if can_cover(card, occupying):
                final_valid.add(tid)
    return list(final_valid)


def ai_take_turn():
    global player_turn
    if not hand_enemy:
        if deck_enemy:
            hand_enemy.append(deck_enemy.pop(0))
        player_turn = True
        return

    best_move = None
    for i, card in enumerate(hand_enemy):
        valid_ids = get_valid_tiles(active_units, card, "player2")
        if not valid_ids:
            continue
        value = card.get("strength", 0)
        if best_move is None or value > best_move[0]:
            best_move = (value, i, card, valid_ids)

    if best_move is None:
        if deck_enemy:
            hand_enemy.append(deck_enemy.pop(0))
        player_turn = True
        return

    _, chosen_index, chosen_card, valid_ids = best_move
    tile_id = random.choice(valid_ids)
    occupying = next((u for u in active_units if u.tile_id == tile_id), None)
    if occupying and can_cover(chosen_card, occupying.card_data):
        active_units.remove(occupying)

    x, y = get_screen_pos(tile_id)
    systeme_particules.create_particles(x, y, nombre=30)
    active_units.append(Unit(tile_id, chosen_card, player="player2"))
    hand_enemy.pop(chosen_index)
    replay = execute_ability(chosen_card, "player2", active_units, hand_enemy, deck_enemy)
    if replay:
        player_turn = False
        ai_wait = 20
    else:
        player_turn = True


class Unit:
    def __init__(self, tile_id, card_data, player="player1"):
        self.tile_id = tile_id
        self.card_data = card_data
        self.player = player
        self.base_image = None
        try:
            self.base_image = pygame.image.load(card_data["image_path"]).convert_alpha()
        except:
            self.base_image = pygame.Surface((40, 50), pygame.SRCALPHA)
            self.base_image.fill((200, 100, 100))

    def draw(self, surf):
        self.x, self.y = get_screen_pos(self.tile_id)
        tile = next((t for t in datamap[mapName]["tiles"] if t["id"] == self.tile_id), None)
        if tile:
            tile_w = int(tile["w"] * MAP_WIDTH)
            tile_h = int(tile["h"] * MAP_HEIGHT)
            if "Crochet" in self.card_data.get("name", ""):
                scale = 1.1
            else:
                scale = 0.9
            width = max(24, min(tile_w, int(tile_w * scale)))
            height = max(32, min(tile_h, int(tile_h * scale * 1.1)))
        else:
            width, height = 60, 80

        image = pygame.transform.scale(self.base_image, (width, height))
        rect = image.get_rect(center=(self.x, self.y))
        surf.blit(image, rect)

        # Outline for distinction joueur / IA
        border_color = (0, 220, 0) if self.player == "player1" else (220, 80, 80)
        pygame.draw.rect(surf, border_color, rect.inflate(4, 4), 2, border_radius=8)

active_units = []
clock = pygame.time.Clock()

# --- BOUCLE PRINCIPALE ---
while True:
    screen.fill((30, 30, 35))
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
            
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = max(760, event.w), max(620, event.h)
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            update_layout()
            mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            # Sélection de carte dans la main
            for i in range(len(hand)):
                rect = pygame.Rect(WIDTH//2 - 150 + i*110, UI_Y + 20, 90, 120)
                if rect.collidepoint(mouse_pos):
                    selected_card_index = i
            
            # Placement sur la Map
            if selected_card_index is not None:
                current_card = hand[selected_card_index]
                valid_ids = get_valid_tiles(active_units, current_card, "player1")
                
                for tile in datamap[mapName]["tiles"]:
                    tr = pygame.Rect(MAP_X + tile["x"]*MAP_WIDTH, MAP_Y + tile["y"]*MAP_HEIGHT, 
                                     tile["w"]*MAP_WIDTH, tile["h"]*MAP_HEIGHT)
                    
                    if tr.collidepoint(mouse_pos) and tile["id"] in valid_ids:
                        x = MAP_X + (tile["x"] + tile["w"]/2) * MAP_WIDTH
                        y = MAP_Y + (tile["y"] + tile["h"]/2) * MAP_HEIGHT
                        systeme_particules.create_particles(x, y, nombre=40)
                        occupying = next((u for u in active_units if u.tile_id == tile["id"]), None)
                        if occupying and can_cover(current_card, occupying.card_data):
                            active_units.remove(occupying)
                        active_units.append(Unit(tile["id"], current_card, player="player1"))
                        hand.pop(selected_card_index)
                        selected_card_index = None
                        replay = execute_ability(current_card, "player1", active_units, hand, deck_host)
                        if replay:
                            player_turn = True
                            ai_wait = 0
                        else:
                            player_turn = False
                            ai_wait = 30
                        break

            # Click sur la pioche
            pioche_rect = pygame.Rect(MAP_X + MAP_WIDTH + 20, MAP_Y + 300, 100, 130)
            if pioche_rect.collidepoint(mouse_pos):
                if deck_host:
                    new_card = deck_host.pop(0)
                    hand.append(new_card)
                # Tirage fait sur pioche normale => fin de tour humain
                player_turn = False
                ai_wait = 30

    # Tour IA
    if not player_turn:
        if ai_wait > 0:
            ai_wait -= 1
        else:
            ai_take_turn()

    # AFFICHAGE
    screen.blit(map_surface, (MAP_X, MAP_Y))

    # Mise en surbrillance des cases valides
    if selected_card_index is not None:
        current_card = hand[selected_card_index]
        valid_ids = get_valid_tiles(active_units, current_card, "player1")
        for tile in datamap[mapName]["tiles"]:
            if tile["id"] in valid_ids:
                sx = MAP_X + int(tile["x"] * MAP_WIDTH)
                sy = MAP_Y + int(tile["y"] * MAP_HEIGHT)
                sw = int(tile["w"] * MAP_WIDTH)
                sh = int(tile["h"] * MAP_HEIGHT)
                s = pygame.Surface((sw, sh), pygame.SRCALPHA)
                # Couleur différente pour le Crochet (Bleu) vs Normal (Vert)
                color = (0, 150, 255, 150) if "Crochet" in current_card.get("name", "") else (0, 255, 100, 150)
                pygame.draw.rect(s, color, (0, 0, sw, sh), border_radius=5)
                screen.blit(s, (sx, sy))

    for u in active_units:
        u.draw(screen)

    # UI Main container
    panel_color = (14, 14, 18)
    pygame.draw.rect(screen, panel_color, (0, UI_Y - 4, WIDTH, 154), border_radius=8)
    pygame.draw.rect(screen, (70, 70, 90), (0, UI_Y - 4, WIDTH, 154), 2, border_radius=8)

    # hand zone title
    ui_font = pygame.font.SysFont(None, 24)
    title = ui_font.render(f"Main ({len(hand)} cartes) - Deck: {len(deck_host)}", True, (230, 230, 240))
    screen.blit(title, (20, UI_Y - 26))
    enemy_title = ui_font.render(f"IA ({len(hand_enemy)} cartes) - Deck: {len(deck_enemy)}", True, (220, 180, 180))
    screen.blit(enemy_title, (20, UI_Y - 50))

    # draw each card slot
    card_base_x = WIDTH//2 - 150
    for i, card in enumerate(hand):
        cx = card_base_x + i*110
        cy = UI_Y + 20
        is_selected = (i == selected_card_index)
        slot_color = (34, 34, 40) if not is_selected else (40, 50, 70)
        pygame.draw.rect(screen, slot_color, (cx-5, cy-5, 100, 130), border_radius=8)

        try:
            img = pygame.image.load(card["image_path"]).convert_alpha()
            scaled = pygame.transform.scale(img, (90, 120))
            screen.blit(scaled, (cx, cy))
        except:
            pygame.draw.rect(screen, (80, 80, 80), (cx, cy, 90, 120), border_radius=8)

        if is_selected:
            pygame.draw.rect(screen, (255, 215, 0), (cx-5, cy-5, 100, 130), 3, border_radius=8)
            # afficher description d'ability
            text = ui_font.render(card.get("ability_desc", ""), True, (255, 230, 180))
            screen.blit(text, (20, UI_Y + 100))

    # Pioche a droite de la map
    pygame.draw.rect(screen, (20, 20, 25), (MAP_X + MAP_WIDTH + 10, MAP_Y + 290, 120, 150), border_radius=8)
    pygame.draw.rect(screen, (80, 80, 100), (MAP_X + MAP_WIDTH + 10, MAP_Y + 290, 120, 150), 2, border_radius=8)
    screen.blit(pioche, (MAP_X + MAP_WIDTH + 20, MAP_Y + 300))

    # Info mode selection
    mode_text = "Selectionnez une carte pour voir les cases valides"
    mode_render = ui_font.render(mode_text, True, (210, 210, 220))
    screen.blit(mode_render, (20, UI_Y + 60))

    systeme_particules.update()
    systeme_particules.draw(screen)

    pygame.display.flip()
    clock.tick(60)