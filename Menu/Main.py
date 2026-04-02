import os
import gc
import pygame
import json

# Pour les maniacs qui aiment pas le message de pygame :)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from MainMenu import mainMenu
from Leaderboard import leaderboard
from Room import room
from Utils import load_path

pygame.init()

# Dimensions de la fenêtre (responsive)
display_info = pygame.display.Info()
max_w, max_h = display_info.current_w, display_info.current_h

# On limite et on force une taille minimum
WIDTH = min(1920, max(800, max_w))
HEIGHT = min(1080, max(450, max_h))

# Chargement des données
windowsdata_path = load_path("data", "windows_data.json")
windowsdata = json.load(open(windowsdata_path, "r", encoding="utf-8"))

# Création de la fenêtre
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

# Mise en place d'un nom à la fenêtre le temps du chargement
pygame.display.set_caption("Toybattle")

# Lancement de la clock
clock = pygame.time.Clock()

menu = mainMenu(screen, clock, windowsdata, WIDTH, HEIGHT)

# Gestion des redirections entre les menus
while True:
    if menu == "mainMenu":
        menu = mainMenu(screen, clock, windowsdata, WIDTH, HEIGHT)
    elif menu == "leaderboard":
        menu = leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT)
    elif menu == "play":
        data = room(screen, clock, windowsdata, WIDTH, HEIGHT)
        menu = data[0]
    else:
        menu = "mainMenu"