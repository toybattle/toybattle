import pygame
import sys
import json

pygame.init()

# Dimensions de la fenêtre
WIDTH = 800
HEIGHT = 600

# Dimensions souhaitées pour la carte (hauteur fixe, largeur calculée pour garder le ratio)
DESIRED_MAP_HEIGHT = 450

# Dimensions des éléments fixes
JESAISPAS_WIDTH = 350
JESAISPAS_HEIGHT = 70
CARD_STACK_WIDTH = 100
CARD_STACK_HEIGHT = 140

# Chargement des données
datamap = json.load(open("datamap.json", "r"))

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(datamap[0]["name"])

# Chargement de l'image de fond
background_img = pygame.image.load(datamap[0]["background_path"])
map_img = pygame.image.load(datamap[0]["image_path"])

# Calcul des dimensions en préservant le ratio
map_width, map_height = map_img.get_size()
ratio = map_width / map_height

# On fixe la hauteur désirée et on calcule la largeur correspondante
MAP_HEIGHT = DESIRED_MAP_HEIGHT
MAP_WIDTH = int(MAP_HEIGHT * ratio)

# Redimensionnement de l'image
map = pygame.transform.scale(map_img, (MAP_WIDTH, MAP_HEIGHT))
background = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

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
    # Calculer les nouvelles coordonnées en fonction du ratio
    new_tile = pygame.Rect(
        int(tile["x"] * (MAP_WIDTH / map_width)),
        int(tile["y"] * (MAP_HEIGHT / map_height)),
        int(tile["width"] * (MAP_WIDTH / map_width)),
        int(tile["height"] * (MAP_HEIGHT / map_height))
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
            
            # Vérifier les clics sur jesaispas
            if pygame.Rect(jesaispas_x, jesaispas_y, JESAISPAS_WIDTH, JESAISPAS_HEIGHT).collidepoint(mouse_pos):
                print("Jesaispas cliqué")

    # Remplir l'écran avec une couleur de fond
    screen.blit(background, (0, 0))
    

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

    pygame.display.flip()
    clock.tick(60)