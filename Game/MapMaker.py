import pygame
import sys
import json
import os
from Utils import load_path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Fenêtre élargie pour faire de la place aux deux panneaux (Gauche et Droite)
WIDTH, HEIGHT = 1200, 700
UI_WIDTH = 260         # Panneau de gauche
RIGHT_UI_WIDTH = 280   # Panneau de droite
pygame.init()

COLORS = {
    "white": (255, 255, 255), "black": (0, 0, 0), "gray": (100, 100, 100),
    "red": (255, 50, 50), "green": (50, 255, 50), "blue": (50, 50, 255),
    "yellow": (255, 255, 0), "orange": (255, 165, 0), "dark_gray": (30, 30, 35),
    "dark_blue": (45, 45, 50), "dark_bg": (60, 60, 70), "light_green": (100, 200, 100),
    "cyan": (0, 200, 200), "purple": (180, 100, 255), "violet": (200, 130, 200),
}

MODES = {
    "tile": "TILE", "link": "LINK", "start_p1": "START_P1", "start_p2": "START_P2",
    "forteresse_p1": "FORTERESSE_P1", "forteresse_p2": "FORTERESSE_P2",
    "delete": "DELETE", "star": "STAR"
}

# Mapping pour la création simplifiée des tuiles
TILE_SETTINGS = {
    MODES["tile"]: ("normal", None),
    MODES["start_p1"]: ("start", "player1"),
    MODES["start_p2"]: ("start", "player2"),
    MODES["forteresse_p1"]: ("forteresse", "player1"),
    MODES["forteresse_p2"]: ("forteresse", "player2"),
}

class MapEditor:
    """Éditeur interactif de cartes pour ToyBattle"""

    def __init__(self, img_path=None):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ToyBattle Map Editor")

        # État des données
        self.tiles = {}  # Dict {id: tile} pour optimisation O(1)
        self.links = []
        self.star_zones = []
        self.tile_counter = 0

        # Interface & État
        self.current_mode = MODES["tile"]
        self.ui_rects = {}
        self.selected_tile_id = None
        self.temp_start_pos = None

        # Variables mode Étoile optimisées et étendues
        self.star_state = {
            "selected_tiles": set(),
            "drawing": False,
            "area_start": None,
            "editing_idx": None
        }

        # Affichage Carte
        self.map_name = None
        self.img_path = None
        self.original_bg = None
        self.display_bg = None
        self.canvas = {"w": 0, "h": 0, "off_x": 0, "off_y": 0}

        # Polices
        self.font = pygame.font.SysFont("Arial", 18)
        self.title_font = pygame.font.SysFont("Arial", 22, bold=True)

        if img_path:
            self.load_map(img_path)

    # ========================================================================
    # LOGIQUE DE CHARGEMENT / SAUVEGARDE
    # ========================================================================

    def load_map(self, img_path):
        self.img_path = img_path
        self.map_name = os.path.basename(img_path).split('.')[0]
        try:
            self.original_bg = pygame.image.load(load_path("assets/map", f"{self.map_name}.jpg")).convert()
            self._setup_canvas()
            self.load_existing_data()
            print(f"✓ Carte chargée: {self.map_name}")
        except FileNotFoundError:
            print(f"✗ Image non trouvée: {img_path}")

    def load_existing_data(self):
        self.tiles.clear()
        self.links.clear()
        self.star_zones.clear()
        self.tile_counter = 0

        data_path = load_path("data", "map_data.json")
        if os.path.exists(data_path):
            try:
                with open(data_path, "r") as f:
                    all_maps = json.load(f)

                if self.map_name in all_maps:
                    data = all_maps[self.map_name]
                    # Conversion de liste en dict pour accès optimisé
                    self.tiles = {t['id']: t for t in data.get("tiles", [])}
                    self.links = data.get("links", [])
                    self.star_zones = data.get("star_zones", [])
                    
                    if self.tiles:
                        self.tile_counter = max(self.tiles.keys()) + 1

                    print(f"✓ Données: {len(self.tiles)} tuiles, {len(self.links)} liens, {len(self.star_zones)} zones étoiles")
            except Exception as e:
                print(f"⚠ Erreur de chargement: {e}")

    def save(self):
        if not self.img_path: return
        data_path = load_path("data", "map_data.json")
        all_maps = {}
        
        if os.path.exists(data_path):
            with open(data_path, "r") as f:
                all_maps = json.load(f)

        all_maps[self.map_name] = {
            "image_path": self.img_path,
            "tiles": list(self.tiles.values()),  # Conversion dict -> liste
            "links": self.links,
            "star_zones": self.star_zones
        }

        with open(data_path, "w") as f:
            json.dump(all_maps, f, indent=4)
        print(f"✓ Carte '{self.map_name}' sauvegardée avec succès !")

    def load_map_from_json(self):
        data_path = load_path("data", "map_data.json")
        if not os.path.exists(data_path):
            print("✗ Aucun fichier map_data.json trouvé")
            return

        with open(data_path, "r") as f:
            all_maps = json.load(f)

        if not all_maps: return

        print("\n--- Cartes disponibles ---")
        map_list = list(all_maps.keys())
        for i, name in enumerate(map_list):
            print(f"{i+1}. {name}")

        choice = input(f"\nSélectionnez une carte (1-{len(map_list)}) ou 'q': ")
        if choice.isdigit() and 1 <= int(choice) <= len(map_list):
            self.load_map(all_maps[map_list[int(choice) - 1]]['image_path'])

    # ========================================================================
    # LOGIQUE SPATIALE & MATHS
    # ========================================================================

    def _setup_canvas(self):
        """Redimensionne la carte pour tenir STRICTEMENT entre le menu gauche et le menu droit"""
        max_w = WIDTH - UI_WIDTH - RIGHT_UI_WIDTH - 40
        max_h = HEIGHT - 40
        img_w, img_h = self.original_bg.get_size()
        
        scale = min(max_w / img_w, max_h / img_h)
        self.canvas["w"] = int(img_w * scale)
        self.canvas["h"] = int(img_h * scale)
        
        self.display_bg = pygame.transform.scale(self.original_bg, (self.canvas["w"], self.canvas["h"]))
        
        # Centrage parfait entre le panneau gauche et le panneau droit
        self.canvas["off_x"] = UI_WIDTH + 20 + (max_w - self.canvas["w"]) // 2
        self.canvas["off_y"] = 20 + (max_h - self.canvas["h"]) // 2

    def screen_to_map(self, pos):
        x = (pos[0] - self.canvas["off_x"]) / self.canvas["w"]
        y = (pos[1] - self.canvas["off_y"]) / self.canvas["h"]
        return x, y

    def map_to_screen(self, mx, my):
        sx = int(mx * self.canvas["w"]) + self.canvas["off_x"]
        sy = int(my * self.canvas["h"]) + self.canvas["off_y"]
        return sx, sy

    def get_tile_at(self, mx, my):
        for tile in self.tiles.values():
            if tile['x'] <= mx <= tile['x'] + tile['w'] and tile['y'] <= my <= tile['y'] + tile['h']:
                return tile
        return None

    def get_star_zone_at(self, mx, my):
        for idx, zone in enumerate(self.star_zones):
            a = zone["area"]
            if a['x'] <= mx <= a['x'] + a['w'] and a['y'] <= my <= a['y'] + a['h']:
                return idx
        return None

    # ========================================================================
    # GESTION DES EVENEMENTS & OUTILS
    # ========================================================================

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.ui_rects.clear()
            self.draw() # On dessine l'UI en premier pour enregistrer les zones cliquables
            self.handle_events()
            pygame.display.flip()
            clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_ui = False
                
                # Vérification intelligente : un clic tombe-t-il sur l'UI enregistrée ?
                if event.button == 1:
                    for key, rect in self.ui_rects.items():
                        if rect.collidepoint(event.pos):
                            self._on_ui_click(key)
                            clicked_ui = True
                            break

                # Si on a pas cliqué sur l'UI, alors c'est un clic sur la carte
                if not clicked_ui and self.original_bg:
                    if event.button == 1: 
                        self._on_map_click(event.pos)
                    elif event.button == 3: 
                        self._on_map_right_click(event.pos)

    def _on_ui_click(self, key):
        if key in MODES.values():
            self.current_mode = key
            self._reset_star_state()
        elif key == 'save': self.save()
        elif key == 'load': self.load_map_from_json()
        elif key == 'start_draw_spawn':
            if self.star_state["selected_tiles"]: self.star_state["drawing"] = True
        elif key == 'cancel_draw_spawn':
            self.star_state["drawing"] = False
            self.star_state["area_start"] = None
        elif key == 'stop_edit_zone':
            self._reset_star_state()

    def _on_map_click(self, pos):
        mx, my = self.screen_to_map(pos)
        # Rejette les clics en dehors de l'image de la map
        if not (0 <= mx <= 1 and 0 <= my <= 1): return

        if self.current_mode == MODES["star"]:
            self._handle_star_click(mx, my)
        elif self.current_mode in TILE_SETTINGS:
            self._handle_tile_creation(mx, my)
        elif self.current_mode == MODES["link"]:
            self._handle_link_creation(mx, my)
        elif self.current_mode == MODES["delete"]:
            self._handle_deletion(mx, my)

    def _on_map_right_click(self, pos):
        mx, my = self.screen_to_map(pos)
        if not (0 <= mx <= 1 and 0 <= my <= 1): return

        if self.current_mode == MODES["star"] and not self.star_state["drawing"]:
            idx = self.get_star_zone_at(mx, my)
            if idx is not None:
                del self.star_zones[idx]
                if self.star_state["editing_idx"] == idx:
                    self._reset_star_state()
                print(f"✓ Zone étoile supprimée.")

    # ------ FONCTIONNALITES OUTILS ------ #

    def _handle_star_click(self, mx, my):
        # 1. Dessin de la zone (nouveau ou édition)
        if self.star_state["drawing"]:
            if not self.star_state["area_start"]:
                self.star_state["area_start"] = (mx, my)
            else:
                x1, y1 = self.star_state["area_start"]
                area = {"x": min(x1, mx), "y": min(y1, my), "w": abs(mx - x1), "h": abs(my - y1)}
                
                if self.star_state["editing_idx"] is not None:
                    self.star_zones[self.star_state["editing_idx"]]["area"] = area
                    print(f"✓ Zone {self.star_state['editing_idx']} redessinée.")
                else:
                    self.star_zones.append({
                        "required_tiles": sorted(list(self.star_state["selected_tiles"])),
                        "area": area
                    })
                    print("✓ Nouvelle zone étoile créée.")
                    self.star_state["selected_tiles"].clear()

                self.star_state["drawing"] = False
                self.star_state["area_start"] = None
            return

        # 2. Clic sur une zone existante -> Passe en mode édition
        clicked_zone = self.get_star_zone_at(mx, my)
        if clicked_zone is not None:
            self.star_state["editing_idx"] = clicked_zone
            self.star_state["selected_tiles"] = set(self.star_zones[clicked_zone]["required_tiles"])
            print(f"✏ Édition de la zone {clicked_zone}")
            return

        # 3. Clic sur une tuile -> Ajout/Retrait
        tile = self.get_tile_at(mx, my)
        if tile:
            tid = tile['id']
            if tid in self.star_state["selected_tiles"]:
                self.star_state["selected_tiles"].remove(tid)
            else:
                self.star_state["selected_tiles"].add(tid)
            
            if self.star_state["editing_idx"] is not None:
                self.star_zones[self.star_state["editing_idx"]]["required_tiles"] = sorted(list(self.star_state["selected_tiles"]))
            return

        # 4. Clic dans le vide -> Quitter l'édition
        self._reset_star_state()

    def _reset_star_state(self):
        self.star_state = {"selected_tiles": set(), "drawing": False, "area_start": None, "editing_idx": None}

    def _handle_tile_creation(self, mx, my):
        if not self.temp_start_pos:
            self.temp_start_pos = (mx, my)
        else:
            x1, y1 = self.temp_start_pos
            t_type, t_player = TILE_SETTINGS[self.current_mode]
            
            new_tile = {
                "id": self.tile_counter,
                "x": min(x1, mx), "y": min(y1, my),
                "w": abs(mx - x1), "h": abs(my - y1),
                "type": t_type,
            }
            if t_player: new_tile["player"] = t_player
            
            self.tiles[self.tile_counter] = new_tile
            self.tile_counter += 1
            self.temp_start_pos = None

    def _handle_link_creation(self, mx, my):
        tile = self.get_tile_at(mx, my)
        if not tile: return
        
        if self.selected_tile_id is None:
            self.selected_tile_id = tile['id']
        elif self.selected_tile_id != tile['id']:
            link = sorted([self.selected_tile_id, tile['id']])
            if link not in self.links:
                self.links.append(link)
            self.selected_tile_id = None

    def _handle_deletion(self, mx, my):
        tile = self.get_tile_at(mx, my)
        if not tile: return
        
        tid = tile['id']
        del self.tiles[tid]
        self.links = [l for l in self.links if tid not in l]
        
        for zone in self.star_zones:
            if tid in zone["required_tiles"]:
                zone["required_tiles"].remove(tid)
        self.star_state["selected_tiles"].discard(tid)

    # ========================================================================
    # AFFICHAGE / RENDU
    # ========================================================================

    def draw(self):
        self.screen.fill(COLORS["dark_gray"])
        
        # On dessine d'abord la map pour qu'elle soit en fond
        if self.display_bg:
            # Cadre noir autour de la carte
            pygame.draw.rect(self.screen, COLORS["black"], (self.canvas["off_x"] - 5, self.canvas["off_y"] - 5, self.canvas["w"] + 10, self.canvas["h"] + 10))
            self.screen.blit(self.display_bg, (self.canvas["off_x"], self.canvas["off_y"]))
            
            self._draw_star_zones()
            self._draw_links()
            self._draw_tiles()
            self._draw_previews()

        # On dessine l'UI par-dessus le fond (même si elle ne superposera plus l'image grâce au nouveau calcul)
        self._draw_ui()

    def _draw_button(self, key, rect, text, bg_color, text_color=COLORS["white"]):
        self.ui_rects[key] = rect
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        text_surf = self.font.render(text, True, text_color)
        self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def _draw_ui(self):
        # --- PANNEAU GAUCHE ---
        pygame.draw.rect(self.screen, COLORS["dark_blue"], (0, 0, UI_WIDTH, HEIGHT))
        self.screen.blit(self.title_font.render("TOY BATTLE", True, COLORS["white"]), (20, 20))
        self.screen.blit(self.title_font.render("EDITOR", True, COLORS["white"]), (20, 45))
        
        if self.map_name:
            self.screen.blit(self.font.render(f"Map: {self.map_name}", True, COLORS["cyan"]), (20, 80))

        # --- PANNEAU DROIT (Fond permanent) ---
        pygame.draw.rect(self.screen, COLORS["dark_blue"], (WIDTH - RIGHT_UI_WIDTH, 0, RIGHT_UI_WIDTH, HEIGHT))

        modes = [
            (MODES["tile"], "1. Draw Tiles", COLORS["green"]), (MODES["link"], "2. Create Links", COLORS["blue"]),
            (MODES["start_p1"], "3. P1 Start", COLORS["orange"]), (MODES["start_p2"], "4. P2 Start", COLORS["cyan"]),
            (MODES["forteresse_p1"], "5. P1 Fortress", COLORS["orange"]), (MODES["forteresse_p2"], "6. P2 Fortress", COLORS["cyan"]),
            (MODES["delete"], "7. Delete", COLORS["red"]), (MODES["star"], "8. Star Zones", COLORS["purple"]),
        ]

        y = 120
        for m_key, label, color in modes:
            bg = color if self.current_mode == m_key else COLORS["dark_bg"]
            tc = COLORS["black"] if self.current_mode == m_key else COLORS["white"]
            self._draw_button(m_key, pygame.Rect(20, y, UI_WIDTH - 40, 35), label, bg, tc)
            y += 45

        # Panneau Étoiles EN HAUT A DROITE
        if self.current_mode == MODES["star"]:
            self._draw_star_panel()
        else:
            txt = self.font.render("Sélectionnez le Mode Étoile", True, COLORS["gray"])
            txt2 = self.font.render("pour gérer les zones.", True, COLORS["gray"])
            self.screen.blit(txt, (WIDTH - RIGHT_UI_WIDTH + 20, 40))
            self.screen.blit(txt2, (WIDTH - RIGHT_UI_WIDTH + 20, 65))

        # Boutons de Sauvegarde
        self._draw_button('save', pygame.Rect(20, HEIGHT - 110, UI_WIDTH - 40, 40), "SAVE JSON", COLORS["light_green"], COLORS["black"])
        self._draw_button('load', pygame.Rect(20, HEIGHT - 60, UI_WIDTH - 40, 40), "LOAD MAP", COLORS["blue"])

    def _draw_star_panel(self):
        """Dessine le panneau des zones étoiles en haut à droite"""
        px = WIDTH - RIGHT_UI_WIDTH + 10
        py = 20
        pw = RIGHT_UI_WIDTH - 20
        ph = 250
        
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.screen, COLORS["dark_bg"], panel, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["purple"], panel, 2, border_radius=5)

        title = "★ Édition Zone ★" if self.star_state["editing_idx"] is not None else "★ Star Zones ★"
        self.screen.blit(self.font.render(title, True, COLORS["violet"]), (px + 15, py + 15))

        # Texte raccourci si trop de tuiles pour éviter de déborder
        t_str = ", ".join(str(i) for i in sorted(self.star_state["selected_tiles"])) if self.star_state["selected_tiles"] else "Aucune"
        if len(t_str) > 22: t_str = t_str[:19] + "..."
        self.screen.blit(self.font.render(f"Tuiles: {t_str}", True, COLORS["white"]), (px + 15, py + 45))

        btn_rect = pygame.Rect(px + 15, py + 80, pw - 30, 35)

        if not self.star_state["drawing"]:
            if self.star_state["editing_idx"] is not None:
                self._draw_button('start_draw_spawn', btn_rect, "Redessiner la zone", COLORS["orange"], COLORS["black"])
                self._draw_button('stop_edit_zone', pygame.Rect(px + 15, py + 125, pw - 30, 35), "Terminer l'édition", COLORS["gray"])
            else:
                if self.star_state["selected_tiles"]:
                    self._draw_button('start_draw_spawn', btn_rect, "Dessiner la zone", COLORS["light_green"], COLORS["black"])
                else:
                    self._draw_button('disabled', btn_rect, "Sél. tuiles d'abord", COLORS["gray"], COLORS["dark_gray"])
        else:
            self.screen.blit(self.font.render("Cliquez les 2 coins opposés", True, COLORS["yellow"]), (px + 15, py + 85))
            self._draw_button('cancel_draw_spawn', pygame.Rect(px + 15, py + 120, pw - 30, 35), "Annuler", COLORS["red"])

        self.screen.blit(self.font.render(f"Zones: {len(self.star_zones)}", True, COLORS["gray"]), (px + 15, py + ph - 50))
        self.screen.blit(self.font.render("(Clic D = Suppr zone)", True, COLORS["gray"]), (px + 15, py + ph - 25))

    def _draw_star_zones(self):
        for idx, zone in enumerate(self.star_zones):
            sx, sy = self.map_to_screen(zone["area"]["x"], zone["area"]["y"])
            sw, sh = int(zone["area"]["w"] * self.canvas["w"]), int(zone["area"]["h"] * self.canvas["h"])
            
            color = COLORS["yellow"] if idx == self.star_state["editing_idx"] else COLORS["violet"]
            thickness = 4 if idx == self.star_state["editing_idx"] else 2
            
            surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            surf.fill((180, 100, 255, 60))
            self.screen.blit(surf, (sx, sy))
            pygame.draw.rect(self.screen, color, (sx, sy, sw, sh), thickness)
            self.screen.blit(self.font.render(f"★ {idx}", True, COLORS["white"]), (sx + 5, sy + 5))

    def _draw_links(self):
        for id1, id2 in self.links:
            t1, t2 = self.tiles.get(id1), self.tiles.get(id2)
            if t1 and t2:
                p1 = self.map_to_screen(t1['x'] + t1['w']/2, t1['y'] + t1['h']/2)
                p2 = self.map_to_screen(t2['x'] + t2['w']/2, t2['y'] + t2['h']/2)
                pygame.draw.line(self.screen, COLORS["yellow"], p1, p2, 4)

    def _draw_tiles(self):
        for t_id, t in self.tiles.items():
            sx, sy = self.map_to_screen(t['x'], t['y'])
            sw, sh = int(t['w'] * self.canvas["w"]), int(t['h'] * self.canvas["h"])

            color = COLORS["green"]
            if self.selected_tile_id == t_id: color = COLORS["white"]
            elif self.current_mode == MODES["star"] and t_id in self.star_state["selected_tiles"]: color = COLORS["purple"]
            elif t['type'] == 'start': color = COLORS["orange"] if t.get('player') == 'player1' else COLORS["cyan"]
            elif t['type'] == 'forteresse': color = COLORS["red"] if t.get('player') == 'player1' else COLORS["blue"]

            thickness = 5 if color == COLORS["purple"] else 3
            pygame.draw.rect(self.screen, color, (sx, sy, sw, sh), thickness)

            lbl = str(t_id)
            if t['type'] in ['start', 'forteresse']:
                p = "P1" if t.get('player') == 'player1' else "P2"
                lbl = f"{'S' if t['type'] == 'start' else 'F'}{t_id}({p})"
            self.screen.blit(self.font.render(lbl, True, color), (sx + 5, sy + 5))

    def _draw_previews(self):
        mx, my = self.screen_to_map(pygame.mouse.get_pos())
        
        if self.current_mode in TILE_SETTINGS and self.temp_start_pos:
            x1, y1 = self.temp_start_pos
            sx, sy = self.map_to_screen(min(x1, mx), min(y1, my))
            sw, sh = int(abs(mx - x1) * self.canvas["w"]), int(abs(my - y1) * self.canvas["h"])
            pygame.draw.rect(self.screen, COLORS["white"], (sx, sy, sw, sh), 2)

        if self.current_mode == MODES["star"] and self.star_state["drawing"] and self.star_state["area_start"]:
            x1, y1 = self.star_state["area_start"]
            sx, sy = self.map_to_screen(min(x1, mx), min(y1, my))
            sw, sh = int(abs(mx - x1) * self.canvas["w"]), int(abs(my - y1) * self.canvas["h"])
            pygame.draw.rect(self.screen, COLORS["violet"], (sx, sy, sw, sh), 3)

if __name__ == "__main__":
    MapEditor().run()