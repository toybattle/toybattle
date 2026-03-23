import pygame
import sys
import json
import Cards

pygame.init()

# Dimensions de la fenêtre
WIDTH = 1000
HEIGHT = 800

# Dimensions des éléments fixes
JESAISPAS_WIDTH = 350
JESAISPAS_HEIGHT = 70
CARD_STACK_WIDTH = 100
CARD_STACK_HEIGHT = 140

mapindex = 1

# Chargement des données
datamap = json.load(open("datamap.json", "r"))

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(datamap[mapindex]["name"])

# Chargement de l'image de fond
water = pygame.image.load(r"assets/water.png").convert()

tile_size = 256
water = pygame.transform.scale(water, (tile_size, tile_size))

# Deux couches
water2 = pygame.transform.rotate(water, 90)

offset1_x = 0
offset1_y = 0
offset2_x = 0
offset2_y = 0

selected_card_index = None

map_img = pygame.image.load(datamap[mapindex]["image_path"])

# Calcul des dimensions en préservant le ratio
map_width, map_height = map_img.get_size()
ratio = map_width / map_height

# On fixe la hauteur désirée et on calcule la largeur correspondante
MAP_HEIGHT = 650
MAP_WIDTH = int(MAP_HEIGHT * ratio)

# Redimensionnement de l'image
map = pygame.transform.scale(map_img, (MAP_WIDTH, MAP_HEIGHT))

jesaispas = pygame.image.load("assets/jesaispas.png")
jesaispas = pygame.transform.scale(jesaispas, (JESAISPAS_WIDTH, JESAISPAS_HEIGHT))

# Charger les images pour la pioche et la défausse
try:
    pioche_img = pygame.image.load("assets/pioche.png")
    defausse_img = pygame.image.load("assets/pioche.png")
except:
    # Créer des surfaces de couleur si les images n'existent pas
    pioche_img = pygame.Surface((CARD_STACK_WIDTH, CARD_STACK_HEIGHT))
    pioche_img.fill((100, 100, 200))
    defausse_img = pygame.Surface((CARD_STACK_WIDTH, CARD_STACK_HEIGHT))
    defausse_img.fill((200, 100, 100))

pioche_img = pygame.transform.scale(pioche_img, (CARD_STACK_WIDTH, CARD_STACK_HEIGHT))
defausse_img = pygame.transform.scale(defausse_img, (CARD_STACK_WIDTH, CARD_STACK_HEIGHT))

# Ajustement des tiles pour correspondre au nouveau ratio
tiles = []
for tile in datamap[0]["tiles"]:
    new_tile = pygame.Rect(
        int(tile["x"] * MAP_WIDTH),
        int(tile["y"] * MAP_HEIGHT),
        int(tile["width"] * MAP_WIDTH),
        int(tile["height"] * MAP_HEIGHT)
    )
    tiles.append(new_tile)

clock = pygame.time.Clock()

# Calcul des positions pour centrer les éléments
map_x = (WIDTH - MAP_WIDTH) // 2
map_y = 30  # Carte remontée

jesaispas_x = (WIDTH - JESAISPAS_WIDTH) // 2
jesaispas_y = map_y + MAP_HEIGHT + 15

pioche_x = map_x - CARD_STACK_WIDTH - 20
pioche_y = map_y + (MAP_HEIGHT - CARD_STACK_HEIGHT) // 2

defausse_x = map_x + MAP_WIDTH + 20
defausse_y = map_y + (MAP_HEIGHT - CARD_STACK_HEIGHT) // 2

# Titres pour les piles
font = pygame.font.Font(None, 20)
pioche_text = font.render("Pioche", True, (255, 255, 255))
defausse_text = font.render("Défausse", True, (255, 255, 255))

host_cards, client_cards = Cards.init_cards()
host_cards_deck = Cards.host_cards(host_cards)
client_cards_deck = Cards.client_cards(client_cards)

# Initialiser hover_progress pour chaque carte du deck
hover_progress = [0.0 for _ in host_cards_deck]
hover_scale_max = 1.1
hover_anim_speed = 12.0
dt = 1 / 60

# Structure pour stocker les cartes placées sur le plateau
cartes_sur_plateau = []  # [{"carte": ..., "tile_index": ...}]

# Fonction utilitaire pour savoir si une tile est occupée
def get_carte_sur_tile(tile_index):
    for c in cartes_sur_plateau:
        if c["tile_index"] == tile_index:
            return c
    return None

# Fonction pour vérifier si une tile est adjacente à une carte déjà posée
# On considère l'adjacence en 4 directions (haut, bas, gauche, droite)
def is_adjacent_to_card(tile_index):
    tile = datamap[0]["tiles"][tile_index]
    x = tile["x"]
    y = tile["y"]
    # On considère une tolérance pour l'adjacence (dépend de la taille des tiles)
    tolerance_x = 0.13  # à ajuster selon la map
    tolerance_y = 0.13
    for c in cartes_sur_plateau:
        t2 = datamap[0]["tiles"][c["tile_index"]]
        dx = abs(t2["x"] - x)
        dy = abs(t2["y"] - y)
        # Adjacence horizontale ou verticale
        if (dx < tolerance_x and dy == 0) or (dy < tolerance_y and dx == 0):
            return True
        # Optionnel : diagonale
        # if (dx < tolerance_x and dy < tolerance_y and dx > 0 and dy > 0):
        #     return True
    return False

while True:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = pygame.mouse.get_pos()

            # Si aucune carte n'est sélectionnée, on regarde si on clique sur une carte de la main
            if selected_card_index is None:
                for i, card in enumerate(host_cards_deck):
                    card_rect = pygame.Rect(
                        jesaispas_x + i * (CARD_STACK_WIDTH + 10),
                        jesaispas_y,
                        CARD_STACK_WIDTH,
                        JESAISPAS_HEIGHT
                    )
                    if card_rect.collidepoint(mouse_pos):
                        selected_card_index = i
                        print(f"Carte {i} sélectionnée")
                        break
            # Si une carte est sélectionnée, on regarde si on clique sur une tile client
            else:
                for i, tile in enumerate(datamap[0]["tiles"]):
                    if tile.get("owner") == "client":
                        tile_rect = pygame.Rect(
                            int(tile["x"] * MAP_WIDTH) + map_x,
                            int(tile["y"] * MAP_HEIGHT) + map_y,
                            int(tile["width"] * MAP_WIDTH),
                            int(tile["height"] * MAP_HEIGHT)
                        )
                        if tile_rect.collidepoint(mouse_pos):
                            print(f"Tile client {i} cliquée")
                            # Vérifier si la tile est libre ou recouvrable
                            carte_sur_tile = get_carte_sur_tile(i)
                            carte_a_placer = host_cards_deck[selected_card_index]
                            # --- NOUVELLE CONDITION ---
                            # Première carte : placement libre
                            placement_autorise = False
                            if len(cartes_sur_plateau) == 0:
                                placement_autorise = True
                            else:
                                # Placement autorisé seulement si la tile est adjacente à une carte déjà posée
                                if is_adjacent_to_card(i):
                                    placement_autorise = True
                            if not placement_autorise:
                                print("Placement interdit : la tile n'est pas adjacente à une carte déjà posée.")
                                selected_card_index = None
                                break
                            if carte_sur_tile is None:
                                # Tile vide, placement autorisé
                                cartes_sur_plateau.append({
                                    "carte": carte_a_placer,
                                    "tile_index": i
                                })
                                host_cards_deck.pop(selected_card_index)
                                print(f"Carte placée sur tile {i}")
                                selected_card_index = None
                                break
                            else:
                                # Tile occupée, vérifier la règle de force
                                force_carte = carte_a_placer.get("strength", 0)
                                force_sur_tile = carte_sur_tile["carte"].get("strength", 0)
                                if force_carte > force_sur_tile:
                                    cartes_sur_plateau.remove(carte_sur_tile)
                                    cartes_sur_plateau.append({
                                        "carte": carte_a_placer,
                                        "tile_index": i
                                    })
                                    host_cards_deck.pop(selected_card_index)
                                    print(f"Carte recouvre la carte sur tile {i}")
                                    selected_card_index = None
                                    break
                                else:
                                    print("Impossible de placer ici : force insuffisante ou règle spéciale.")
                                    selected_card_index = None
                                    break
                # Si on clique ailleurs, on désélectionne la carte
                else:
                    print("Aucune tile client cliquée, désélection de la carte.")
                    selected_card_index = None

            # Vérifier les clics sur la pioche
            if pygame.Rect(pioche_x, pioche_y, CARD_STACK_WIDTH, CARD_STACK_HEIGHT).collidepoint(mouse_pos):
                print("Pioche cliquée")

            # Vérifier les clics sur la défausse
            if pygame.Rect(defausse_x, defausse_y, CARD_STACK_WIDTH, CARD_STACK_HEIGHT).collidepoint(mouse_pos):
                print("Défausse cliquée")

    # Animation
    offset1_x += 0.3
    offset1_y += 0.2

    offset2_x += 0.1
    offset2_y += 0.25

    for x in range(-tile_size, WIDTH + tile_size, tile_size):
        for y in range(-tile_size, HEIGHT + tile_size, tile_size):
            screen.blit(water, (x - offset1_x % tile_size, y - offset1_y % tile_size))

    # Dessin couche 2 (transparente)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for x in range(-tile_size, WIDTH + tile_size, tile_size):
        for y in range(-tile_size, HEIGHT + tile_size, tile_size):
            overlay.blit(water2, (x - offset2_x % tile_size, y - offset2_y % tile_size))

    overlay.set_alpha(80)
    screen.blit(overlay, (0, 0))

    # Dessiner la carte principale
    screen.blit(map, (map_x, map_y))
    
    # Dessiner les piles de cartes
    screen.blit(pioche_img, (pioche_x, pioche_y))
    screen.blit(defausse_img, (defausse_x, defausse_y))
    
    # Ajouter les titres
    screen.blit(pioche_text, (pioche_x + 10, pioche_y - 20))
    screen.blit(defausse_text, (defausse_x + 10, defausse_y - 20))
    
    # Dessiner jesaispas en dessous de la carte
    screen.blit(jesaispas, (jesaispas_x, jesaispas_y))
    
    # Dessiner les cartes du joueur hôte sur jesaispas
    for i, card in enumerate(host_cards_deck):
        img = pygame.image.load(card["image_path"])
        img_width, img_height = img.get_size()
        scale_factor = JESAISPAS_HEIGHT / img_height
        new_width = int(img_width * scale_factor)
        img = pygame.transform.scale(img, (new_width, JESAISPAS_HEIGHT))

        x = jesaispas_x + i * (CARD_STACK_WIDTH + 10)
        y = jesaispas_y

        # Si la carte est sélectionnée → zoom animé
        if selected_card_index == i:
            hover_progress[i] += (1.0 - hover_progress[i]) * min(1.0, hover_anim_speed * dt)
            progress = hover_progress[i]
            scale = 1.0 + (hover_scale_max - 1.0) * progress
            scaled_width = max(1, int(new_width * scale))
            scaled_height = max(1, int(JESAISPAS_HEIGHT * scale))
            img_zoom = pygame.transform.smoothscale(img, (scaled_width, scaled_height))
            # Centrer le zoom sur la carte
            zoom_x = x - (scaled_width - new_width) // 2
            zoom_y = y - (scaled_height - JESAISPAS_HEIGHT) // 2
            screen.blit(img_zoom, (zoom_x, zoom_y))
        else:
            hover_progress[i] += (0.0 - hover_progress[i]) * min(1.0, hover_anim_speed * dt)
            screen.blit(img, (x, y))

    # Afficher les cartes placées sur le plateau
    for c in cartes_sur_plateau:
        tile = datamap[0]["tiles"][c["tile_index"]]
        img = pygame.image.load(c["carte"]["image_path"])
        img_width, img_height = img.get_size()
        # On adapte la taille à la tile
        tile_w = int(tile["width"] * MAP_WIDTH)
        tile_h = int(tile["height"] * MAP_HEIGHT)
        scale = min(tile_w / img_width, tile_h / img_height)
        new_w = int(img_width * scale)
        new_h = int(img_height * scale)
        img = pygame.transform.scale(img, (new_w, new_h))
        x = int(tile["x"] * MAP_WIDTH) + map_x + (tile_w - new_w) // 2
        y = int(tile["y"] * MAP_HEIGHT) + map_y + (tile_h - new_h) // 2
        screen.blit(img, (x, y))

    pygame.display.flip()
    clock.tick(60)