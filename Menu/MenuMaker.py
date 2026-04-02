import pygame
import sys
import json
import os 

from Utils import load_path

pygame.init()

WIDTH = 1280
HEIGHT = 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MENU Editor")

#Charger image originale
background = pygame.image.load(load_path("assets/Menus/Room", "Full.png")).convert()
img_width, img_height = background.get_size()

#Garder le ratio
DESIRED_HEIGHT = 500
ratio = img_width / img_height

MAP_HEIGHT = DESIRED_HEIGHT
MAP_WIDTH = int(MAP_HEIGHT * ratio)

display_bg = pygame.transform.scale(background, (MAP_WIDTH, MAP_HEIGHT))

#Centrage
map_x = (WIDTH - MAP_WIDTH) // 2
map_y = (HEIGHT - MAP_HEIGHT) // 2

temp_start_pos = None
tiles = []

clock = pygame.time.Clock()
button_rect = pygame.Rect(WIDTH - 90, 10, 80, 30)

#Btn
font = pygame.font.SysFont(None, 24)

def save_to_json():
    filename = "../data/windows_data.json"
    menu_name = "Room"
    image_path = "../assets/Menus/Room.png"

    # Charger les données existantes si le fichier existe
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Chercher si la map existe déjà
    found = False
    for entry in data:
        if entry.get("name") == menu_name:
            entry["tiles"] = tiles
            entry["image_path"] = image_path
            found = True
            break

    # Si la map n'existe pas, l'ajouter
    if not found:
        data.append({
            "name": menu_name,
            "image_path": image_path,
            "tiles": tiles
        })
        
    json.dump(data, open(filename, "w"), indent=4)
    print(f"Menu '{menu_name}' saved to {filename}.")


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            #SAVE
            if button_rect.collidepoint(mouse_pos):
                save_to_json()
                continue
            
            #Convertir position écran → position dans la map
            local_x = mouse_pos[0] - map_x
            local_y = mouse_pos[1] - map_y

            if temp_start_pos is None:
                temp_start_pos = (local_x, local_y)
            else:
                x1, y1 = temp_start_pos
                x2, y2 = local_x, local_y

                x = min(x1, x2)
                y = min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)

                #Normalisation pour la map
                tile = {
                    "x": x / MAP_WIDTH,
                    "y": y / MAP_HEIGHT,
                    "width": width / MAP_WIDTH,
                    "height": height / MAP_HEIGHT
                }

                tiles.append(tile)
                print("Ajouté:", tile)

                temp_start_pos = None

    screen.fill((30, 30, 30))

    #Dessiner map
    screen.blit(display_bg, (map_x, map_y))

    # Tiles sauvegardées
    for tile in tiles:
        rect = pygame.Rect(
            int(tile["x"] * MAP_WIDTH) + map_x,
            int(tile["y"] * MAP_HEIGHT) + map_y,
            int(tile["width"] * MAP_WIDTH),
            int(tile["height"] * MAP_HEIGHT)
        )
        pygame.draw.rect(screen, (255, 0, 0), rect, 2)

    # Tile en cours
    if temp_start_pos:
        mx, my = pygame.mouse.get_pos()
        local_x = mx - map_x
        local_y = my - map_y

        x1, y1 = temp_start_pos
        x2, y2 = local_x, local_y

        rect = pygame.Rect(
            min(x1, x2) + map_x,
            min(y1, y2) + map_y,
            abs(x2 - x1),
            abs(y2 - y1)
        )
        pygame.draw.rect(screen, (0, 255, 0), rect, 2)

    #Bt,
    pygame.draw.rect(screen, (0, 0, 255), button_rect)
    text = font.render("Save", True, (255, 255, 255))
    screen.blit(text, (button_rect.x + 15, button_rect.y + 5))

    pygame.display.flip()
    clock.tick(60)