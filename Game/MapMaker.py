import pygame
import sys
import json
import os
from Utils import load_path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Dimensions de la fenêtre
WIDTH, HEIGHT = 1000, 600
UI_WIDTH = 250
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
        
        # Calcul des dimensions du canvas
        self._setup_canvas()
        
        # Charger les données existantes de cette carte
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
                    
                    # Mettre à jour le compteur d'IDs
                    if self.tiles:
                        self.tile_counter = max(tile['id'] for tile in self.tiles) + 1
                    else:
                        self.tile_counter = 0
                    
                    print(f"✓ Données chargées: {len(self.tiles)} tuiles, {len(self.links)} liens")
                else:
                    print(f"ℹ Aucune donnée existante pour {self.map_name}")
                    self.tiles = []
                    self.links = []
                    self.tile_counter = 0
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠ Erreur de chargement: {e}")
                self.tiles = []
                self.links = []
                self.tile_counter = 0
        else:
            print("ℹ Aucun fichier de données trouvé")

    def _load_image(self, img_path):
        """Charge l'image de fond avec gestion d'erreur"""
        try:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image non trouvée: {img_path}")
            image = pygame.image.load(img_path).convert()
            print(f"✓ Image chargée: {img_path}")
            return image
        except FileNotFoundError as e:
            print(f"✗ ERREUR: {e}")
            return None

    def _setup_canvas(self):
        """Configure les dimensions et position du canvas"""
        canvas_height = HEIGHT - 40
        aspect_ratio = self.original_bg.get_width() / self.original_bg.get_height()
        canvas_width = int(canvas_height * aspect_ratio)
        
        self.canvas_w = canvas_width
        self.canvas_h = canvas_height
        self.display_bg = pygame.transform.scale(self.original_bg, (canvas_width, canvas_height))
        
        # Centrer le canvas
        self.offset_x = UI_WIDTH + (WIDTH - UI_WIDTH - canvas_width) // 2
        self.offset_y = 20

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
        """Trouve la tuile à une position donnée"""
        map_x, map_y = self.screen_to_map(screen_pos)
        
        for tile in self.tiles:
            x_overlaps = tile['x'] <= map_x <= tile['x'] + tile['w']
            y_overlaps = tile['y'] <= map_y <= tile['y'] + tile['h']
            if x_overlaps and y_overlaps:
                return tile
        return None

    def _is_valid_map_coords(self, map_x, map_y):
        """Vérifie si les coordonnées sont dans les limites de la carte"""
        return 0 <= map_x <= 1 and 0 <= map_y <= 1

    def save(self):
        """Sauvegarde la carte en JSON en conservant les autres cartes"""
        if not self.img_path:
            print("✗ Aucune carte chargée à sauvegarder")
            return
            
        # Charger les données existantes si le fichier existe
        all_maps = {}
        if os.path.exists(load_path("data", "map_data.json")):
            try:
                with open(load_path("data", "map_data.json"), "r") as f:
                    all_maps = json.load(f)
            except (json.JSONDecodeError, IOError):
                all_maps = {}
        
        # Ajouter ou mettre à jour la carte actuelle
        all_maps[self.map_name] = {
            "image_path": self.img_path,
            "tiles": self.tiles,
            "links": self.links
        }
        
        # Sauvegarder toutes les cartes
        with open(load_path("data", "map_data.json"), "w") as f:
            json.dump(all_maps, f, indent=4)
        print(f"✓ Carte '{self.map_name}' sauvegardée: map_data.json ({len(self.tiles)} tuiles, {len(self.links)} liens)")

    def load_map_from_json(self):
        """Affiche une interface pour charger une carte existante"""
        if not os.path.exists(load_path("data", "map_data.json")):
            print("✗ Aucun fichier map_data.json trouvé")
            return False
        
        try:
            with open(load_path("data", "map_data.json"), "r") as f:
                all_maps = json.load(f)
            
            if not all_maps:
                print("✗ Aucune carte disponible")
                return False
            
            # Créer une liste des cartes disponibles
            map_list = list(all_maps.keys())
            
            # Interface simple de sélection
            print("\n--- Cartes disponibles ---")
            for i, map_name in enumerate(map_list):
                map_data = all_maps[map_name]
                print(f"{i+1}. {map_name} ({len(map_data.get('tiles', []))} tuiles)")
            
            # Demander le choix à l'utilisateur
            while True:
                try:
                    choice = input("\nSélectionnez une carte (1-{}) ou 'q' pour quitter: ".format(len(map_list)))
                    if choice.lower() == 'q':
                        return False
                    
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(map_list):
                        selected_map = map_list[choice_idx]
                        map_data = all_maps[selected_map]
                        
                        # Charger la carte sélectionnée
                        self.load_map(map_data['image_path'])
                        return True
                    else:
                        print("Choix invalide")
                except ValueError:
                    print("Entrée invalide")
        except Exception as e:
            print(f"✗ Erreur lors du chargement: {e}")
            return False

    def run(self):
        """Boucle principale"""
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            if self.original_bg:  # Ne dessine que si une carte est chargée
                self.draw()
            else:
                self._draw_no_map_screen()
            pygame.display.flip()
            clock.tick(60)

    def _draw_no_map_screen(self):
        """Affiche un écran quand aucune carte n'est chargée"""
        self.screen.fill(COLORS["dark_gray"])
        self._draw_minimal_ui()

    def _draw_minimal_ui(self):
        """Dessine une UI minimale pour le chargement"""
        # Fond du panneau
        pygame.draw.rect(self.screen, COLORS["dark_blue"], (0, 0, UI_WIDTH, HEIGHT))
        
        # Titre
        title = self.title_font.render("TOY BATTLE EDITOR", True, COLORS["white"])
        self.screen.blit(title, (20, 30))
        
        # Bouton Load
        load_rect = pygame.Rect(20, 100, UI_WIDTH - 40, 50)
        pygame.draw.rect(self.screen, COLORS["blue"], load_rect, border_radius=5)
        text = self.font.render("LOAD MAP", True, COLORS["white"])
        text_rect = text.get_rect(center=load_rect.center)
        self.screen.blit(text, text_rect)

    def handle_events(self):
        """Traite les événements"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] < UI_WIDTH:
                    self._on_ui_click(event.pos)
                elif self.original_bg:  # Seulement si une carte est chargée
                    self._on_map_click(event.pos)

    def _on_ui_click(self, ui_pos):
        """Gère les clics sur l'interface utilisateur"""
        y = ui_pos[1]
        
        if not self.original_bg:
            # UI minimale pour le chargement
            if 100 <= y <= 150:  # Bouton Load
                self.load_map_from_json()
            return
        
        # Sélection du mode
        if 100 <= y <= 140:
            self.current_mode = MODES["tile"]
        elif 150 <= y <= 190:
            self.current_mode = MODES["link"]
        elif 200 <= y <= 240:
            self.current_mode = MODES["start_p1"]
        elif 250 <= y <= 290:
            self.current_mode = MODES["start_p2"]
        elif 300 <= y <= 340:
            self.current_mode = MODES["forteresse_p1"]
        elif 350 <= y <= 390:
            self.current_mode = MODES["forteresse_p2"]
        elif 400 <= y <= 440:
            self.current_mode = MODES["delete"]
        
        # Bouton Sauvegarder
        elif HEIGHT - 100 <= y <= HEIGHT - 50:
            self.save()
        
        # Bouton Load
        elif HEIGHT - 50 <= y <= HEIGHT:
            self.load_map_from_json()

    def _on_map_click(self, screen_pos):
        """Gère les clics sur la carte"""
        map_x, map_y = self.screen_to_map(screen_pos)
        
        if not self._is_valid_map_coords(map_x, map_y):
            return

        if self.current_mode in [MODES["tile"], MODES["start_p1"], MODES["start_p2"], 
                                 MODES["forteresse_p1"], MODES["forteresse_p2"]]:
            self._handle_tile_creation(map_x, map_y)
        elif self.current_mode == MODES["link"]:
            self._handle_link_creation(screen_pos)
        elif self.current_mode == MODES["delete"]:
            self._handle_tile_deletion(screen_pos)

    def _handle_tile_creation(self, map_x, map_y):
        """Crée une tuile (2 clics)"""
        if self.temp_start_pos is None:
            self.temp_start_pos = (map_x, map_y)
        else:
            x1, y1 = self.temp_start_pos
            
            # Déterminer le type de tuile
            if self.current_mode == MODES["start_p1"]:
                tile_type = "start"
                tile_player = "player1"
            elif self.current_mode == MODES["start_p2"]:
                tile_type = "start"
                tile_player = "player2"
            elif self.current_mode == MODES["forteresse_p1"]:
                tile_type = "forteresse"
                tile_player = "player1"
            elif self.current_mode == MODES["forteresse_p2"]:
                tile_type = "forteresse"
                tile_player = "player2"
            else:
                tile_type = "normal"
                tile_player = None
            
            new_tile = {
                "id": self.tile_counter,
                "x": min(x1, map_x),
                "y": min(y1, map_y),
                "w": abs(map_x - x1),
                "h": abs(map_y - y1),
                "type": tile_type,
            }
            
            # Ajouter le joueur si c'est un start ou une forteresse
            if tile_player:
                new_tile["player"] = tile_player
            
            self.tiles.append(new_tile)
            self.tile_counter += 1
            self.temp_start_pos = None

    def _handle_link_creation(self, screen_pos):
        """Crée un lien entre deux tuiles (2 clics)"""
        clicked_tile = self.get_tile_at(screen_pos)
        if not clicked_tile:
            return

        if self.selected_tile_id is None:
            self.selected_tile_id = clicked_tile['id']
        else:
            if self.selected_tile_id != clicked_tile['id']:
                link = [self.selected_tile_id, clicked_tile['id']]
                if link not in self.links:
                    self.links.append(link)
            self.selected_tile_id = None

    def _handle_tile_deletion(self, screen_pos):
        """Supprime une tuile et ses liens"""
        clicked_tile = self.get_tile_at(screen_pos)
        if not clicked_tile:
            return

        tile_id = clicked_tile['id']
        self.tiles = [t for t in self.tiles if t['id'] != tile_id]
        self.links = [l for l in self.links if tile_id not in l]

    def draw(self):
        """Redessine l'interface"""
        self.screen.fill(COLORS["dark_gray"])
        self._draw_ui()
        self._draw_map()

    def _draw_ui(self):
        """Dessine le panneau d'interface (gauche)"""
        # Fond du panneau
        pygame.draw.rect(self.screen, COLORS["dark_blue"], (0, 0, UI_WIDTH, HEIGHT))
        
        # Titre
        title = self.title_font.render("TOY BATTLE EDITOR", True, COLORS["white"])
        self.screen.blit(title, (20, 30))
        
        # Infos carte
        if self.current_map_name:
            map_info = self.font.render(f"Map: {self.current_map_name}", True, COLORS["cyan"])
            self.screen.blit(map_info, (20, 65))

        # Boutons des modes
        modes_list = [
            (MODES["tile"], "1. Draw Tiles", COLORS["green"]),
            (MODES["link"], "2. Create Links", COLORS["blue"]),
            (MODES["start_p1"], "3. P1 Start Point", COLORS["orange"]),
            (MODES["start_p2"], "4. P2 Start Point", COLORS["cyan"]),
            (MODES["forteresse_p1"], "5. P1 Fortress", COLORS["orange"]),
            (MODES["forteresse_p2"], "6. P2 Fortress", COLORS["cyan"]),
            (MODES["delete"], "7. Delete Elements", COLORS["red"]),
        ]

        for i, (mode, label, color) in enumerate(modes_list):
            self._draw_mode_button(i, mode, label, color)

        # Bouton Sauvegarder
        self._draw_save_button()
        
        # Bouton Load
        self._draw_load_button()

    def _draw_mode_button(self, index, mode, label, color):
        """Dessine un bouton de mode"""
        button_rect = pygame.Rect(20, 100 + index * 50, UI_WIDTH - 40, 40)
        
        # Couleur selon sélection
        bg_color = color if self.current_mode == mode else COLORS["dark_bg"]
        pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=5)
        
        # Texte
        text_color = COLORS["black"] if self.current_mode == mode else COLORS["white"]
        text = self.font.render(label, True, text_color)
        self.screen.blit(text, (button_rect.x + 10, button_rect.y + 10))

    def _draw_save_button(self):
        """Dessine le bouton sauvegarder"""
        button_rect = pygame.Rect(20, HEIGHT - 100, UI_WIDTH - 40, 40)
        pygame.draw.rect(self.screen, COLORS["light_green"], button_rect, border_radius=5)
        
        text = self.font.render("SAVE JSON", True, COLORS["black"])
        text_rect = text.get_rect(center=button_rect.center)
        self.screen.blit(text, text_rect)
    
    def _draw_load_button(self):
        """Dessine le bouton charger"""
        button_rect = pygame.Rect(20, HEIGHT - 50, UI_WIDTH - 40, 40)
        pygame.draw.rect(self.screen, COLORS["blue"], button_rect, border_radius=5)
        
        text = self.font.render("LOAD MAP", True, COLORS["white"])
        text_rect = text.get_rect(center=button_rect.center)
        self.screen.blit(text, text_rect)

    def _draw_map(self):
        """Dessine la zone de la carte"""
        if not self.display_bg:
            return
            
        # Ombre portée
        pygame.draw.rect(
            self.screen, COLORS["black"],
            (self.offset_x + 5, self.offset_y + 5, self.canvas_w, self.canvas_h)
        )
        
        # Image de fond
        self.screen.blit(self.display_bg, (self.offset_x, self.offset_y))

        # Dessiner les liens
        self._draw_links()

        # Dessiner les tuiles
        self._draw_tiles()

        # Rectangle de sélection en cours
        self._draw_selection_preview()

    def _draw_links(self):
        """Dessine les lignes entre tuiles"""
        for start_id, end_id in self.links:
            start_tile = next((t for t in self.tiles if t['id'] == start_id), None)
            end_tile = next((t for t in self.tiles if t['id'] == end_id), None)
            
            if start_tile and end_tile:
                start_pos = self.map_to_screen(
                    start_tile['x'] + start_tile['w'] / 2,
                    start_tile['y'] + start_tile['h'] / 2
                )
                end_pos = self.map_to_screen(
                    end_tile['x'] + end_tile['w'] / 2,
                    end_tile['y'] + end_tile['h'] / 2
                )
                pygame.draw.line(self.screen, COLORS["yellow"], start_pos, end_pos, 4)

    def _draw_tiles(self):
        """Dessine les tuiles"""
        for tile in self.tiles:
            screen_x, screen_y = self.map_to_screen(tile['x'], tile['y'])
            screen_w = int(tile['w'] * self.canvas_w)
            screen_h = int(tile['h'] * self.canvas_h)

            # Couleur selon type et sélection
            if self.selected_tile_id == tile['id']:
                color = COLORS["white"]
            elif tile['type'] == 'start':
                # Distinguer les start points par joueur
                if tile.get('player') == 'player1':
                    color = COLORS["orange"]
                elif tile.get('player') == 'player2':
                    color = COLORS["cyan"]
                else:
                    color = COLORS["orange"]  # Par défaut
            elif tile['type'] == 'forteresse':
                # Distinguer les forteresses par joueur
                if tile.get('player') == 'player1':
                    color = COLORS["red"]
                elif tile.get('player') == 'player2':
                    color = COLORS["blue"]
                else:
                    color = COLORS["red"]  # Par défaut
            else:
                color = COLORS["green"]

            pygame.draw.rect(self.screen, color, (screen_x, screen_y, screen_w, screen_h), 2)
            
            # ID et type de la tuile
            if tile['type'] == 'start' and tile.get('player'):
                player_num = "P1" if tile['player'] == 'player1' else "P2"
                tile_label = f"S{tile['id']}({player_num})"
            elif tile['type'] == 'forteresse' and tile.get('player'):
                player_num = "P1" if tile['player'] == 'player1' else "P2"
                tile_label = f"F{tile['id']}({player_num})"
            else:
                tile_label = str(tile['id'])
            
            tile_id_text = self.font.render(tile_label, True, color)
            self.screen.blit(tile_id_text, (screen_x + 2, screen_y + 2))

    def _draw_selection_preview(self):
        """Affiche l'aperçu du rectangle en cours de dessin"""
        if not self.temp_start_pos:
            return

        if self.current_mode not in [MODES["tile"], MODES["start_p1"], MODES["start_p2"],
                                     MODES["forteresse_p1"], MODES["forteresse_p2"]]:
            return

        map_x, map_y = self.screen_to_map(pygame.mouse.get_pos())
        x1, y1 = self.temp_start_pos

        screen_x = int(min(x1, map_x) * self.canvas_w) + self.offset_x
        screen_y = int(min(y1, map_y) * self.canvas_h) + self.offset_y
        screen_w = int(abs(map_x - x1) * self.canvas_w)
        screen_h = int(abs(map_y - y1) * self.canvas_h)

        pygame.draw.rect(self.screen, COLORS["white"], (screen_x, screen_y, screen_w, screen_h), 1)


if __name__ == "__main__":
    # Lance l'éditeur avec une carte (optionnel)
    # Décommentez la ligne suivante pour charger une carte au démarrage:
    # map_editor = MapEditor("C:\\Users\\louis\\Documents\\Toybattle\\toybattle\\assets\\map\\MapGlace.jpg")
    
    # Ou lancez sans carte pour utiliser le bouton LOAD
    map_editor = MapEditor()  # Sans carte au démarrage
    map_editor.run()