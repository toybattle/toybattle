import pygame
import sys
import json
import os

pygame.init()

# --- Configuration écran ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ToyBattle Map Editor")

# --- Charger image map ---
background = pygame.image.load("assets/map/MapGlace.jpg").convert()
img_width, img_height = background.get_size()
DESIRED_HEIGHT = 500
ratio = img_width / img_height
MAP_HEIGHT = DESIRED_HEIGHT
MAP_WIDTH = int(MAP_HEIGHT * ratio)
display_bg = pygame.transform.scale(background, (MAP_WIDTH, MAP_HEIGHT))
map_x = (WIDTH - MAP_WIDTH) // 2
map_y = (HEIGHT - MAP_HEIGHT) // 2

# --- Données map ---
tiles = []
connectors = []
paths = []  # chaque chemin = {"start_id": idx, "end_id": idx}
temp_start_pos = None
selected_connector = None
current_mode = "Tiles"  # Tiles / Connecteur / Chemin

# --- Horloge ---
clock = pygame.time.Clock()

# --- Boutons ---
font = pygame.font.SysFont(None, 24)
button_rects = {
    "Save": pygame.Rect(WIDTH - 90, 10, 80, 30),
    "Tiles": pygame.Rect(WIDTH - 90, 50, 80, 30),
    "Connecteur": pygame.Rect(WIDTH - 90, 90, 80, 30),
    "Chemin": pygame.Rect(WIDTH - 90, 130, 80, 30)
}

# --- Fonctions ---
def save_to_json():
    filename = "datamap.json"
    map_name = "MapGlace"
    image_path = "assets/map/MapGlace.jpg"

    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try: data = json.load(f)
            except json.JSONDecodeError: data = []

    found = False
    for entry in data:
        if entry.get("name") == map_name:
            entry.update({"tiles": tiles, "connectors": connectors, "paths": paths, "image_path": image_path})
            found = True
            break

    if not found:
        data.append({"name": map_name, "tiles": tiles, "connectors": connectors, "paths": paths, "image_path": image_path})

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Map '{map_name}' saved.")

def get_connector_at_pos(pos):
    x, y = pos
    for idx, c in enumerate(connectors):
        cx = int(c["x"] * MAP_WIDTH) + map_x
        cy = int(c["y"] * MAP_HEIGHT) + map_y
        if (cx - x)**2 + (cy - y)**2 <= 100:  # rayon 10px
            return idx
    return None

# --- Boucle principale ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            local_x = mouse_pos[0] - map_x
            local_y = mouse_pos[1] - map_y

            # Vérifier boutons
            clicked_button = False
            for name, rect in button_rects.items():
                if rect.collidepoint(mouse_pos):
                    if name == "Save": save_to_json()
                    else:
                        current_mode = name
                        temp_start_pos = None
                        selected_connector = None
                    clicked_button = True
                    break
            if clicked_button: continue

            if current_mode == "Tiles":
                if temp_start_pos is None:
                    temp_start_pos = (local_x, local_y)
                else:
                    x1, y1 = temp_start_pos
                    x2, y2 = local_x, local_y
                    x = min(x1, x2)
                    y = min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    tile = {"x": x / MAP_WIDTH, "y": y / MAP_HEIGHT, "width": width / MAP_WIDTH, "height": height / MAP_HEIGHT}
                    tiles.append(tile)
                    temp_start_pos = None
                    print("Zone ajoutée:", tile)

            elif current_mode == "Connecteur":
                connector = {"x": local_x / MAP_WIDTH, "y": local_y / MAP_HEIGHT}
                connectors.append(connector)
                print("Connecteur ajouté:", connector)

            elif current_mode == "Chemin":
                conn_idx = get_connector_at_pos(mouse_pos)
                if conn_idx is not None:
                    if selected_connector is None:
                        selected_connector = conn_idx
                        print("Premier connecteur sélectionné:", conn_idx)
                    else:
                        if selected_connector != conn_idx:
                            paths.append({"start_id": selected_connector, "end_id": conn_idx})
                            print(f"Chemin ajouté entre {selected_connector} -> {conn_idx}")
                        selected_connector = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                temp_start_pos = None
                selected_connector = None
                current_path = []

    # --- Affichage ---
    screen.fill((30, 30, 30))
    screen.blit(display_bg, (map_x, map_y))

    # Tiles
    for tile in tiles:
        rect = pygame.Rect(int(tile["x"] * MAP_WIDTH) + map_x,
                           int(tile["y"] * MAP_HEIGHT) + map_y,
                           int(tile["width"] * MAP_WIDTH),
                           int(tile["height"] * MAP_HEIGHT))
        pygame.draw.rect(screen, (255, 0, 0), rect, 2)

    # Connecteurs
    for idx, c in enumerate(connectors):
        cx = int(c["x"] * MAP_WIDTH) + map_x
        cy = int(c["y"] * MAP_HEIGHT) + map_y
        color = (0, 255, 0) if selected_connector == idx else (255, 255, 0)
        pygame.draw.circle(screen, color, (cx, cy), 8)

    # Chemins
    for path in paths:
        start = connectors[path["start_id"]]
        end = connectors[path["end_id"]]
        sx = int(start["x"] * MAP_WIDTH) + map_x
        sy = int(start["y"] * MAP_HEIGHT) + map_y
        ex = int(end["x"] * MAP_WIDTH) + map_x
        ey = int(end["y"] * MAP_HEIGHT) + map_y
        pygame.draw.line(screen, (0, 0, 255), (sx, sy), (ex, ey), 3)

    # Tile en cours
    if temp_start_pos and current_mode == "Tiles":
        mx, my = pygame.mouse.get_pos()
        x1, y1 = temp_start_pos
        rect = pygame.Rect(min(x1, mx - map_x) + map_x, min(y1, my - map_y) + map_y,
                           abs(mx - map_x - x1), abs(my - map_y - y1))
        pygame.draw.rect(screen, (0, 255, 0), rect, 2)

    # Boutons
    for name, rect in button_rects.items():
        color = (0, 0, 255) if current_mode != name else (0, 128, 255)
        pygame.draw.rect(screen, color, rect)
        text = font.render(name, True, (255, 255, 255))
        screen.blit(text, (rect.x + 5, rect.y + 5))

    # Mode actif
    mode_text = font.render(f"Mode actif: {current_mode}", True, (255, 255, 255))
    screen.blit(mode_text, (10, 10))

    pygame.display.flip()
    clock.tick(60)