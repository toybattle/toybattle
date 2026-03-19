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
water = pygame.image.load(r"C:\Users\63043998\Desktop\ToyBattle\toybattle\assets\water.png").convert()

tile_size = 256
water = pygame.transform.scale(water, (tile_size, tile_size))

# Deux couches
water2 = pygame.transform.rotate(water, 90)

offset1_x = 0
offset1_y = 0
offset2_x = 0
offset2_y = 0

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

while True:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = pygame.mouse.get_pos()

            # Vérifier les clics sur les tiles de la carte
            for i, tile in enumerate(tiles):
                # Ajuster la position des tiles par rapport à la position de la carte
                adjusted_tile = pygame.Rect(
                    tile.x + map_x,
                    tile.y + map_y,
                    tile.width,
                    tile.height
                )
                if adjusted_tile.collidepoint(mouse_pos):
                    print(f"Tile {i} clicked")
            
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
    
    for card in host_cards_deck:
        img = pygame.image.load(card["image_path"])
        # Garder le ratio de l'image, hauteur = JESAISPAS_HEIGHT
        img_width, img_height = img.get_size()
        scale_factor = JESAISPAS_HEIGHT / img_height
        new_width = int(img_width * scale_factor)
        img = pygame.transform.scale(img, (new_width, JESAISPAS_HEIGHT))
        screen.blit(img, (jesaispas_x + host_cards_deck.index(card) * (CARD_STACK_WIDTH + 10), jesaispas_y))

    pygame.display.flip()
    clock.tick(60)