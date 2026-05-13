import pygame
import sys
import json
import os
from Utils import load_path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Dimensions de la fenêtre (Agrandies pour ne pas superposer l'UI)
WIDTH, HEIGHT = 1200, 800
UI_WIDTH = 280
pygame.init()

# Palette de couleurs
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (100, 100, 100),
    "red": (255, 50, 50),
    "green": (50, 255, 50),
    "blue": (50, 50, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "dark_gray": (30, 30, 35),
    "dark_blue": (45, 45, 50),
    "dark_bg": (60, 60, 70),
    "light_green": (100, 200, 100),
    "cyan": (0, 200, 200),
    "purple": (180, 100, 255),
    "violet": (200, 130, 200),
}

# Modes d'édition
MODES = {
    "tile": "TILE",
    "link": "LINK",
    "start_p1": "START_P1",
    "start_p2": "START_P2",
    "forteresse_p1": "FORTERESSE_P1",
    "forteresse_p2": "FORTERESSE_P2",
    "delete": "DELETE",
    "star": "STAR",          # Nouveau mode étoile
}

class MapEditor:
    """Éditeur interactif de cartes pour ToyBattle"""

    def __init__(self, img_path=None):
        """Initialise l'éditeur avec une image de fond"""
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ToyBattle Map Editor")

        # État de l'éditeur
        self.tiles = []
        self.links = []
        self.star_zones = []               # Liste des zones d'étoiles
        self.current_mode = MODES["tile"]
        self.selected_tile_id = None
        self.temp_start_pos = None
        self.tile_counter = 0
        self.current_map_name = None
        self.img_path = None
        self.original_bg = None
        self.display_bg = None
        self.canvas_w = 0
        self.canvas_h = 0
        self.offset_x = 0
        self.offset_y = 0

        # Dictionnaire pour stocker les zones cliquables de l'UI
        self.ui_rects = {}

        # Variables pour le mode étoile
        self.selected_star_tiles = set()    # IDs des tuiles sélectionnées pour la nouvelle zone
        self.star_area_start = None         # Premier coin du rectangle de la zone de spawn
        self.star_drawing = False           # True si en train de dessiner le rectangle

        # Polices
        self.font = pygame.font.SysFont("Arial", 18)
        self.title_font = pygame.font.SysFont("Arial", 22, bold=True)

        # Charger la map si un chemin est fourni
        if img_path:
            self.load_map(img_path)

    def load_map(self, img_path):
        """Charge une carte depuis un chemin d'image"""
        self.img_path = img_path
        self.map_name = os.path.basename(img_path).split('.')[0]
        self.original_bg = self._load_image(load_path("assets/map", self.map_name + ".jpg"))

        if self.original_bg:
            self._setup_canvas()
            self.load_existing_data()
            print(f"✓ Carte chargée: {self.map_name}")

    def load_existing_data(self):
        """Charge les données existantes de la carte depuis map_data.json"""
        if os.path.exists(load_path("data", "map_data.json")):
            try:
                with open(load_path("data", "map_data.json"), "r") as f:
                    all_maps = json.load(f)

                if self.map_name in all_maps:
                    map_data = all_maps[self.map_name]
                    self.tiles = map_data.get("tiles", [])
                    self.links = map_data.get("links", [])
                    self.star_zones = map_data.get("star_zones", [])

                    if self.tiles:
                        self.tile_counter = max(tile['id'] for tile in self.tiles) + 1
                    else:
                        self.tile_counter = 0

                    print(f"✓ Données: {len(self.tiles)} tuiles, {len(self.links)} liens, "
                          f"{len(self.star_zones)} zones étoiles")
                else:
                    print(f"ℹ Aucune donnée existante pour {self.map_name}")
                    self.tiles = []
                    self.links = []
                    self.star_zones = []
                    self.tile_counter = 0
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠ Erreur de chargement: {e}")
        else:
            print("ℹ Aucun fichier de données trouvé")

    def _load_image(self, img_path):
        """Charge l'image de fond"""
        try:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image non trouvée: {img_path}")
            return pygame.image.load(img_path).convert()
        except FileNotFoundError as e:
            print(f"✗ ERREUR: {e}")
            return None

    def _setup_canvas(self):
        """Configure et redimensionne la carte pour qu'elle s'intègre parfaitement"""
        max_canvas_w = WIDTH - UI_WIDTH - 40
        max_canvas_h = HEIGHT - 40
        
        img_w = self.original_bg.get_width()
        img_h = self.original_bg.get_height()
        
        # Conserver le ratio sans déborder de la fenêtre
        ratio_w = max_canvas_w / img_w
        ratio_h = max_canvas_h / img_h
        scale = min(ratio_w, ratio_h)
        
        self.canvas_w = int(img_w * scale)
        self.canvas_h = int(img_h * scale)
        self.display_bg = pygame.transform.scale(self.original_bg, (self.canvas_w, self.canvas_h))

        # Centrer
        self.offset_x = UI_WIDTH + (WIDTH - UI_WIDTH - self.canvas_w) // 2
        self.offset_y = (HEIGHT - self.canvas_h) // 2

    def screen_to_map(self, screen_pos):
        """Convertit une position écran en coordonnées normalisées [0, 1]"""
        x = (screen_pos[0] - self.offset_x) / self.canvas_w
        y = (screen_pos[1] - self.offset_y) / self.canvas_h
        return x, y

    def map_to_screen(self, map_x, map_y):
        """Convertit des coordonnées normalisées en position écran"""
        screen_x = int(map_x * self.canvas_w) + self.offset_x
        screen_y = int(map_y * self.canvas_h) + self.offset_y
        return screen_x, screen_y

    def get_tile_at(self, screen_pos):
        """Trouve la tuile sous le curseur"""
        map_x, map_y = self.screen_to_map(screen_pos)
        for tile in self.tiles:
            if tile['x'] <= map_x <= tile['x'] + tile['w'] and tile['y'] <= map_y <= tile['y'] + tile['h']:
                return tile
        return None

    def _is_valid_map_coords(self, map_x, map_y):
        return 0 <= map_x <= 1 and 0 <= map_y <= 1

    def save(self):
        """Sauvegarde la carte et les zones étoiles en JSON"""
        if not self.img_path:
            return

        all_maps = {}
        if os.path.exists(load_path("data", "map_data.json")):
            try:
                with open(load_path("data", "map_data.json"), "r") as f:
                    all_maps = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        all_maps[self.map_name] = {
            "image_path": self.img_path,
            "tiles": self.tiles,
            "links": self.links,
            "star_zones": self.star_zones   # Sauvegarde des zones étoiles !
        }

        with open(load_path("data", "map_data.json"), "w") as f:
            json.dump(all_maps, f, indent=4)
            
        print(f"✓ Carte '{self.map_name}' sauvegardée avec succès !")

    def load_map_from_json(self):
        """Interface terminal simple pour charger une carte existante"""
        if not os.path.exists(load_path("data", "map_data.json")):
            print("✗ Aucun fichier map_data.json trouvé")
            return False

        try:
            with open(load_path("data", "map_data.json"), "r") as f:
                all_maps = json.load(f)

            if not all_maps:
                return False

            map_list = list(all_maps.keys())
            print("\n--- Cartes disponibles ---")
            for i, map_name in enumerate(map_list):
                print(f"{i+1}. {map_name}")

            choice = input(f"\nSélectionnez une carte (1-{len(map_list)}) ou 'q' pour quitter: ")
            if choice.lower() != 'q':
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(map_list):
                    self.load_map(all_maps[map_list[choice_idx]]['image_path'])
                    return True
        except Exception as e:
            print(f"✗ Erreur : {e}")
        return False

    def run(self):
        """Boucle principale"""
        clock = pygame.time.Clock()
        while True:
            self.ui_rects.clear()  # Réinitialise les clics possibles à chaque frame
            if self.original_bg:
                self.draw()
            else:
                self._draw_no_map_screen()
                
            self.handle_events()
            pygame.display.flip()
            clock.tick(60)

    def _draw_no_map_screen(self):
        self.screen.fill(COLORS["dark_gray"])
        pygame.draw.rect(self.screen, COLORS["dark_blue"], (0, 0, UI_WIDTH, HEIGHT))
        title = self.title_font.render("TOY BATTLE EDITOR", True, COLORS["white"])
        self.screen.blit(title, (20, 30))

        load_rect = pygame.Rect(20, 100, UI_WIDTH - 40, 50)
        self.ui_rects['load_min'] = load_rect
        pygame.draw.rect(self.screen, COLORS["blue"], load_rect, border_radius=5)
        text = self.font.render("LOAD MAP", True, COLORS["white"])
        self.screen.blit(text, text.get_rect(center=load_rect.center))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    if event.pos[0] < UI_WIDTH:
                        self._on_ui_click(event.pos)
                    elif self.original_bg:
                        self._on_map_click(event.pos)
                elif event.button == 3:  # Clic droit
                    if self.current_mode == MODES["star"] and self.original_bg and event.pos[0] >= UI_WIDTH:
                        self._on_map_right_click(event.pos)

    def _on_ui_click(self, ui_pos):
        """Gère les clics via les rectangles UI enregistrés de façon dynamique"""
        # Si aucune map chargée
        if not self.original_bg:
            if 'load_min' in self.ui_rects and self.ui_rects['load_min'].collidepoint(ui_pos):
                self.load_map_from_json()
            return

        # Changement de mode
        for mode_key, mode_val in MODES.items():
            if mode_val in self.ui_rects and self.ui_rects[mode_val].collidepoint(ui_pos):
                self.current_mode = mode_val
                # Reset des variables si on passe en mode étoile
                if mode_val == MODES["star"]:
                    self.selected_star_tiles.clear()
                    self.star_area_start = None
                    self.star_drawing = False
                return

        # Boutons généraux (Sauvegarder / Charger)
        if 'save' in self.ui_rects and self.ui_rects['save'].collidepoint(ui_pos):
            self.save()
            return
        if 'load' in self.ui_rects and self.ui_rects['load'].collidepoint(ui_pos):
            self.load_map_from_json()
            return

        # Boutons spécifiques au Panel Étoile
        if self.current_mode == MODES["star"]:
            if not self.star_drawing and 'define_spawn' in self.ui_rects and self.ui_rects['define_spawn'].collidepoint(ui_pos):
                if self.selected_star_tiles:
                    self.star_drawing = True
                    self.star_area_start = None
            elif self.star_drawing and 'cancel_spawn' in self.ui_rects and self.ui_rects['cancel_spawn'].collidepoint(ui_pos):
                self.star_drawing = False
                self.star_area_start = None

    def _on_map_right_click(self, screen_pos):
        """Supprime une zone étoile existante sous le curseur (clic droit)"""
        if self.current_mode != MODES["star"] or self.star_drawing:
            return
            
        map_x, map_y = self.screen_to_map(screen_pos)
        to_remove = None
        for idx, zone in enumerate(self.star_zones):
            area = zone["area"]
            if area['x'] <= map_x <= area['x'] + area['w'] and area['y'] <= map_y <= area['y'] + area['h']:
                to_remove = idx
                break
                
        if to_remove is not None:
            del self.star_zones[to_remove]
            print(f"✓ Zone étoile {to_remove} supprimée")

    def _on_map_click(self, screen_pos):
        """Gère les clics gauche sur la carte"""
        map_x, map_y = self.screen_to_map(screen_pos)
        if not self._is_valid_map_coords(map_x, map_y):
            return

        if self.current_mode == MODES["star"]:
            self._handle_star_zone_click(screen_pos, map_x, map_y)
        elif self.current_mode in [MODES["tile"], MODES["start_p1"], MODES["start_p2"], MODES["forteresse_p1"], MODES["forteresse_p2"]]:
            self._handle_tile_creation(map_x, map_y)
        elif self.current_mode == MODES["link"]:
            self._handle_link_creation(screen_pos)
        elif self.current_mode == MODES["delete"]:
            self._handle_tile_deletion(screen_pos)

    def _handle_star_zone_click(self, screen_pos, map_x, map_y):
        """Gère la création de la zone étoile ou la sélection de tuiles"""
        if self.star_drawing:
            # On définit le rectangle d'apparition (Spawn)
            if self.star_area_start is None:
                self.star_area_start = (map_x, map_y)
            else:
                x1, y1 = self.star_area_start
                new_zone = {
                    "required_tiles": sorted(list(self.selected_star_tiles)),
                    "area": {
                        "x": min(x1, map_x), 
                        "y": min(y1, map_y), 
                        "w": abs(map_x - x1), 
                        "h": abs(map_y - y1)
                    }
                }
                self.star_zones.append(new_zone)
                print(f"✓ Nouvelle zone étoile créée nécessitant les tuiles : {new_zone['required_tiles']}")
                
                self.selected_star_tiles.clear()
                self.star_area_start = None
                self.star_drawing = False
        else:
            # On sélectionne les tuiles requises
            tile = self.get_tile_at(screen_pos)
            if tile:
                tid = tile['id']
                if tid in self.selected_star_tiles:
                    self.selected_star_tiles.remove(tid)
                else:
                    self.selected_star_tiles.add(tid)

    def _handle_tile_creation(self, map_x, map_y):
        if self.temp_start_pos is None:
            self.temp_start_pos = (map_x, map_y)
        else:
            x1, y1 = self.temp_start_pos
            tile_type = "normal"
            tile_player = None

            if self.current_mode == MODES["start_p1"]: tile_type, tile_player = "start", "player1"
            elif self.current_mode == MODES["start_p2"]: tile_type, tile_player = "start", "player2"
            elif self.current_mode == MODES["forteresse_p1"]: tile_type, tile_player = "forteresse", "player1"
            elif self.current_mode == MODES["forteresse_p2"]: tile_type, tile_player = "forteresse", "player2"

            new_tile = {
                "id": self.tile_counter,
                "x": min(x1, map_x), "y": min(y1, map_y),
                "w": abs(map_x - x1), "h": abs(map_y - y1),
                "type": tile_type,
            }
            if tile_player:
                new_tile["player"] = tile_player

            self.tiles.append(new_tile)
            self.tile_counter += 1
            self.temp_start_pos = None

    def _handle_link_creation(self, screen_pos):
        clicked_tile = self.get_tile_at(screen_pos)
        if not clicked_tile: return
        
        if self.selected_tile_id is None:
            self.selected_tile_id = clicked_tile['id']
        else:
            if self.selected_tile_id != clicked_tile['id']:
                link = sorted([self.selected_tile_id, clicked_tile['id']])
                if link not in self.links:
                    self.links.append(link)
            self.selected_tile_id = None

    def _handle_tile_deletion(self, screen_pos):
        clicked_tile = self.get_tile_at(screen_pos)
        if not clicked_tile: return
        
        tile_id = clicked_tile['id']
        self.tiles = [t for t in self.tiles if t['id'] != tile_id]
        self.links = [l for l in self.links if tile_id not in l]
        
        # Nettoyer les zones étoiles associées à la tuile
        for zone in self.star_zones:
            zone["required_tiles"] = [tid for tid in zone["required_tiles"] if tid != tile_id]
        self.selected_star_tiles.discard(tile_id)

    # ========================================================================
    # AFFICHAGE / DESSIN
    # ========================================================================

    def draw(self):
        self.screen.fill(COLORS["dark_gray"])
        self._draw_ui()
        self._draw_map()

    def _draw_ui(self):
        pygame.draw.rect(self.screen, COLORS["dark_blue"], (0, 0, UI_WIDTH, HEIGHT))
        self.screen.blit(self.title_font.render("TOY BATTLE EDITOR", True, COLORS["white"]), (20, 20))
        
        if self.current_map_name:
            self.screen.blit(self.font.render(f"Map: {self.current_map_name}", True, COLORS["cyan"]), (20, 50))

        modes_list = [
            (MODES["tile"], "1. Draw Tiles", COLORS["green"]),
            (MODES["link"], "2. Create Links", COLORS["blue"]),
            (MODES["start_p1"], "3. P1 Start Point", COLORS["orange"]),
            (MODES["start_p2"], "4. P2 Start Point", COLORS["cyan"]),
            (MODES["forteresse_p1"], "5. P1 Fortress", COLORS["orange"]),
            (MODES["forteresse_p2"], "6. P2 Fortress", COLORS["cyan"]),
            (MODES["delete"], "7. Delete Elements", COLORS["red"]),
            (MODES["star"], "8. Star Zones", COLORS["purple"]),
        ]

        # Dessin dynamique des boutons de modes
        y_offset = 80
        for mode, label, color in modes_list:
            btn_rect = pygame.Rect(20, y_offset, UI_WIDTH - 40, 35)
            self.ui_rects[mode] = btn_rect
            bg_color = color if self.current_mode == mode else COLORS["dark_bg"]
            text_color = COLORS["black"] if self.current_mode == mode else COLORS["white"]
            
            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=5)
            self.screen.blit(self.font.render(label, True, text_color), (btn_rect.x + 10, btn_rect.y + 7))
            y_offset += 45

        if self.current_mode == MODES["star"]:
            self._draw_star_panel(y_offset)

        # Boutons Sauvegarder et Charger ancrés en bas
        save_rect = pygame.Rect(20, HEIGHT - 110, UI_WIDTH - 40, 40)
        self.ui_rects['save'] = save_rect
        pygame.draw.rect(self.screen, COLORS["light_green"], save_rect, border_radius=5)
        self.screen.blit(self.font.render("SAVE JSON", True, COLORS["black"]), (save_rect.x + 60, save_rect.y + 10))

        load_rect = pygame.Rect(20, HEIGHT - 60, UI_WIDTH - 40, 40)
        self.ui_rects['load'] = load_rect
        pygame.draw.rect(self.screen, COLORS["blue"], load_rect, border_radius=5)
        self.screen.blit(self.font.render("LOAD MAP", True, COLORS["white"]), (load_rect.x + 60, load_rect.y + 10))

    def _draw_star_panel(self, y_base):
        """Affiche le panneau dédié pour créer les zones étoiles"""
        panel_rect = pygame.Rect(10, y_base + 10, UI_WIDTH - 20, 180)
        pygame.draw.rect(self.screen, COLORS["dark_bg"], panel_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["purple"], panel_rect, 2, border_radius=5)
        self.screen.blit(self.font.render("★ Star Zones ★", True, COLORS["violet"]), (20, y_base + 15))

        if not self.star_drawing:
            # Etape 1 : Selection des tuiles
            tiles_str = ", ".join(str(tid) for tid in sorted(self.selected_star_tiles)) if self.selected_star_tiles else "Aucune"
            self.screen.blit(self.font.render(f"Tuiles requises : {tiles_str}", True, COLORS["white"]), (20, y_base + 45))

            # Bouton "Define Spawn Area"
            btn_rect = pygame.Rect(20, y_base + 80, UI_WIDTH - 40, 35)
            self.ui_rects['define_spawn'] = btn_rect
            
            if self.selected_star_tiles:
                pygame.draw.rect(self.screen, COLORS["light_green"], btn_rect, border_radius=5)
                self.screen.blit(self.font.render("Dessiner la zone", True, COLORS["black"]), (btn_rect.x + 30, btn_rect.y + 7))
            else:
                pygame.draw.rect(self.screen, COLORS["gray"], btn_rect, border_radius=5)
                self.screen.blit(self.font.render("Sél. tuiles d'abord", True, COLORS["dark_gray"]), (btn_rect.x + 20, btn_rect.y + 7))
        else:
            # Etape 2 : Dessin du rectangle
            self.screen.blit(self.font.render("1. Cliquez un coin", True, COLORS["yellow"]), (20, y_base + 40))
            self.screen.blit(self.font.render("2. Cliquez l'opposé", True, COLORS["yellow"]), (20, y_base + 60))

            cancel_rect = pygame.Rect(20, y_base + 90, UI_WIDTH - 40, 35)
            self.ui_rects['cancel_spawn'] = cancel_rect
            pygame.draw.rect(self.screen, COLORS["red"], cancel_rect, border_radius=5)
            self.screen.blit(self.font.render("Annuler le dessin", True, COLORS["white"]), (cancel_rect.x + 30, cancel_rect.y + 7))

        # Statistiques
        self.screen.blit(self.font.render(f"Zones créées: {len(self.star_zones)}", True, COLORS["violet"]), (20, y_base + 140))
        self.screen.blit(self.font.render("(Clic droit sur zone = Suppr)", True, COLORS["gray"]), (20, y_base + 160))

    def _draw_map(self):
        if not self.display_bg: return
        
        pygame.draw.rect(self.screen, COLORS["black"], (self.offset_x + 5, self.offset_y + 5, self.canvas_w, self.canvas_h))
        self.screen.blit(self.display_bg, (self.offset_x, self.offset_y))

        self._draw_star_zones()
        self._draw_links()
        self._draw_tiles()
        self._draw_selection_preview()

        if self.current_mode == MODES["star"] and not self.star_drawing:
            self._draw_selected_star_tiles()

    def _draw_star_zones(self):
        for idx, zone in enumerate(self.star_zones):
            area = zone["area"]
            screen_x, screen_y = self.map_to_screen(area["x"], area["y"])
            screen_w = int(area["w"] * self.canvas_w)
            screen_h = int(area["h"] * self.canvas_h)
            
            surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            surface.fill((180, 100, 255, 60))  # Violet transparent
            self.screen.blit(surface, (screen_x, screen_y))
            pygame.draw.rect(self.screen, COLORS["violet"], (screen_x, screen_y, screen_w, screen_h), 3)
            
            self.screen.blit(self.font.render(f"★ Zone {idx}", True, COLORS["white"]), (screen_x + 5, screen_y + 5))

    def _draw_selected_star_tiles(self):
        for tile in self.tiles:
            if tile['id'] in self.selected_star_tiles:
                screen_x, screen_y = self.map_to_screen(tile['x'], tile['y'])
                screen_w, screen_h = int(tile['w'] * self.canvas_w), int(tile['h'] * self.canvas_h)
                pygame.draw.rect(self.screen, COLORS["purple"], (screen_x, screen_y, screen_w, screen_h), 5)

    def _draw_links(self):
        for start_id, end_id in self.links:
            start_tile = next((t for t in self.tiles if t['id'] == start_id), None)
            end_tile = next((t for t in self.tiles if t['id'] == end_id), None)
            if start_tile and end_tile:
                start_pos = self.map_to_screen(start_tile['x'] + start_tile['w'] / 2, start_tile['y'] + start_tile['h'] / 2)
                end_pos = self.map_to_screen(end_tile['x'] + end_tile['w'] / 2, end_tile['y'] + end_tile['h'] / 2)
                pygame.draw.line(self.screen, COLORS["yellow"], start_pos, end_pos, 4)

    def _draw_tiles(self):
        for tile in self.tiles:
            screen_x, screen_y = self.map_to_screen(tile['x'], tile['y'])
            screen_w, screen_h = int(tile['w'] * self.canvas_w), int(tile['h'] * self.canvas_h)

            color = COLORS["green"]
            if self.selected_tile_id == tile['id']: color = COLORS["white"]
            elif tile['type'] == 'start':
                color = COLORS["orange"] if tile.get('player') == 'player1' else COLORS["cyan"]
            elif tile['type'] == 'forteresse':
                color = COLORS["red"] if tile.get('player') == 'player1' else COLORS["blue"]

            pygame.draw.rect(self.screen, color, (screen_x, screen_y, screen_w, screen_h), 3)

            # Labels
            label = str(tile['id'])
            if tile['type'] in ['start', 'forteresse']:
                p = "P1" if tile.get('player') == 'player1' else "P2"
                t = "S" if tile['type'] == 'start' else "F"
                label = f"{t}{tile['id']}({p})"
                
            self.screen.blit(self.font.render(label, True, color), (screen_x + 5, screen_y + 5))

    def _draw_selection_preview(self):
        # Preview création tuiles
        if self.current_mode in [MODES["tile"], MODES["start_p1"], MODES["start_p2"], MODES["forteresse_p1"], MODES["forteresse_p2"]]:
            if self.temp_start_pos:
                map_x, map_y = self.screen_to_map(pygame.mouse.get_pos())
                x1, y1 = self.temp_start_pos
                sx, sy = self.map_to_screen(min(x1, map_x), min(y1, map_y))
                sw, sh = int(abs(map_x - x1) * self.canvas_w), int(abs(map_y - y1) * self.canvas_h)
                pygame.draw.rect(self.screen, COLORS["white"], (sx, sy, sw, sh), 2)

        # Preview création zone Etoile
        if self.current_mode == MODES["star"] and self.star_drawing and self.star_area_start:
            map_x, map_y = self.screen_to_map(pygame.mouse.get_pos())
            x1, y1 = self.star_area_start
            sx, sy = self.map_to_screen(min(x1, map_x), min(y1, map_y))
            sw, sh = int(abs(map_x - x1) * self.canvas_w), int(abs(map_y - y1) * self.canvas_h)
            
            pygame.draw.rect(self.screen, COLORS["violet"], (sx, sy, sw, sh), 3)
            self.screen.blit(self.font.render("Star Spawn", True, COLORS["violet"]), (sx + 5, sy + 5))

if __name__ == "__main__":
    map_editor = MapEditor()
    map_editor.run()