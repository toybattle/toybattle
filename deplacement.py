import pygame
import sys
import json
import Cards
import math

pygame.init()

WIDTH = 1000
HEIGHT = 800

JESAISPAS_WIDTH = 350
JESAISPAS_HEIGHT = 70
CARD_STACK_WIDTH = 100
CARD_STACK_HEIGHT = 140

mapindex = 1

datamap = json.load(open("datamap.json", "r"))

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(datamap[mapindex]["name"])

# =========================
# MAP
# =========================
map_img = pygame.image.load(datamap[mapindex]["image_path"])
map_width, map_height = map_img.get_size()
ratio = map_width / map_height

MAP_HEIGHT = 650
MAP_WIDTH = int(MAP_HEIGHT * ratio)

map = pygame.transform.scale(map_img, (MAP_WIDTH, MAP_HEIGHT))

map_x = (WIDTH - MAP_WIDTH) // 2
map_y = 30

# =========================
# UI
# =========================
jesaispas = pygame.image.load("assets/jesaispas.png")
jesaispas = pygame.transform.scale(jesaispas, (JESAISPAS_WIDTH, JESAISPAS_HEIGHT))

jesaispas_x = (WIDTH - JESAISPAS_WIDTH) // 2
jesaispas_y = map_y + MAP_HEIGHT + 15

# =========================
# CARDS
# =========================
host_cards, client_cards = Cards.init_cards()
host_cards_deck = Cards.host_cards(host_cards)

selected_card_index = None
cartes_sur_plateau = []

clock = pygame.time.Clock()

# =========================
# BUILD GRAPH
# =========================
def build_graph():
    adjacency = {i: [] for i in range(len(datamap[mapindex]["tiles"]))}

    for i, t1 in enumerate(datamap[mapindex]["tiles"]):
        for j, t2 in enumerate(datamap[mapindex]["tiles"]):
            if i == j:
                continue

            dx = t1["x"] - t2["x"]
            dy = t1["y"] - t2["y"]
            dist = math.sqrt(dx**2 + dy**2)

            if dist < 0.20:
                adjacency[i].append(j)

    return adjacency

adjacency = build_graph()
print("GRAPH:", adjacency)

# =========================
# START TILES (GAUCHE / DROITE)
# =========================
def get_start_tiles():
    tiles = datamap[mapindex]["tiles"]
    left = []
    right = []

    for i, t in enumerate(tiles):
        if t["x"] < 0.2:
            left.append(i)
        elif t["x"] > 0.8:
            right.append(i)

    print("START LEFT:", left)
    print("START RIGHT:", right)

    return left, right

start_left, start_right = get_start_tiles()

# =========================
# LOGIQUE JEU
# =========================
def get_carte_sur_tile(tile_index):
    for c in cartes_sur_plateau:
        if c["tile_index"] == tile_index:
            return c
    return None


def is_valid_start(tile_index):
    return tile_index in start_left or tile_index in start_right


def is_connected_to_player(tile_index):
    for c in cartes_sur_plateau:
        if tile_index in adjacency[c["tile_index"]]:
            return True
    return False


def can_place_card(card, tile_index):
    print("TEST placement:", card["name"], tile_index)

    # 🔥 PREMIER TOUR → UNIQUEMENT START
    if len(cartes_sur_plateau) == 0:
        if is_valid_start(tile_index):
            print("✅ Start OK")
            return True
        else:
            print("❌ Pas une case de départ")
            return False

    # Crochet ignore tout
    if card["name"] == "Crochet":
        return True

    # 🔥 progression normale
    if is_connected_to_player(tile_index):
        print("✅ Connecté")
        return True

    print("❌ Pas connecté")
    return False


def can_override(card, existing):
    if card["name"] == "Kwak":
        return True

    if existing["carte"]["name"] == "Kwak":
        return True

    if existing["carte"]["name"] == "Roxy":
        return card["name"] == "Kwak"

    return card["strength"] > existing["carte"]["strength"]


# =========================
# DEBUG DRAW
# =========================
def draw_tiles_debug():
    for i, tile in enumerate(datamap[mapindex]["tiles"]):
        rect = pygame.Rect(
            int(tile["x"] * MAP_WIDTH) + map_x,
            int(tile["y"] * MAP_HEIGHT) + map_y,
            int(tile["width"] * MAP_WIDTH),
            int(tile["height"] * MAP_HEIGHT)
        )

        color = (255, 0, 0)

        if is_valid_start(i):
            color = (0, 255, 0)

        pygame.draw.rect(screen, color, rect, 2)


# =========================
# LOOP
# =========================
while True:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = pygame.mouse.get_pos()
            print("\nCLICK:", mouse_pos)

            # SELECT CARD
            if selected_card_index is None:
                for i, card in enumerate(host_cards_deck):
                    rect = pygame.Rect(
                        jesaispas_x + i * (CARD_STACK_WIDTH + 10),
                        jesaispas_y,
                        CARD_STACK_WIDTH,
                        JESAISPAS_HEIGHT
                    )
                    if rect.collidepoint(mouse_pos):
                        selected_card_index = i
                        print("Carte sélectionnée:", card["name"])
                        break

            # PLACE CARD
            else:
                for i, tile in enumerate(datamap[mapindex]["tiles"]):

                    tile_rect = pygame.Rect(
                        int(tile["x"] * MAP_WIDTH) + map_x,
                        int(tile["y"] * MAP_HEIGHT) + map_y,
                        int(tile["width"] * MAP_WIDTH),
                        int(tile["height"] * MAP_HEIGHT)
                    )

                    if tile_rect.collidepoint(mouse_pos):

                        print("👉 TILE:", i)

                        card = host_cards_deck[selected_card_index]
                        existing = get_carte_sur_tile(i)

                        if not can_place_card(card, i):
                            print("❌ Placement refusé")
                            selected_card_index = None
                            break

                        if existing is None:
                            cartes_sur_plateau.append({
                                "carte": card,
                                "tile_index": i
                            })
                        else:
                            if not can_override(card, existing):
                                print("❌ Trop faible")
                                selected_card_index = None
                                break

                            cartes_sur_plateau.remove(existing)
                            cartes_sur_plateau.append({
                                "carte": card,
                                "tile_index": i
                            })

                        host_cards_deck.pop(selected_card_index)
                        selected_card_index = None
                        break

                else:
                    selected_card_index = None

    # DRAW
    screen.fill((0, 0, 0))

    screen.blit(map, (map_x, map_y))
    screen.blit(jesaispas, (jesaispas_x, jesaispas_y))

    draw_tiles_debug()

    # MAIN
    for i, card in enumerate(host_cards_deck):
        img = pygame.image.load(card["image_path"])
        img = pygame.transform.scale(img, (CARD_STACK_WIDTH, JESAISPAS_HEIGHT))

        x = jesaispas_x + i * (CARD_STACK_WIDTH + 10)
        y = jesaispas_y

        screen.blit(img, (x, y))

    # PLATEAU
    for c in cartes_sur_plateau:
        tile = datamap[mapindex]["tiles"][c["tile_index"]]
        img = pygame.image.load(c["carte"]["image_path"])

        tile_w = int(tile["width"] * MAP_WIDTH)
        tile_h = int(tile["height"] * MAP_HEIGHT)

        img = pygame.transform.scale(img, (tile_w, tile_h))

        x = int(tile["x"] * MAP_WIDTH) + map_x
        y = int(tile["y"] * MAP_HEIGHT) + map_y

        screen.blit(img, (x, y))

    pygame.display.flip()
    clock.tick(60)