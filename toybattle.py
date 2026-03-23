import os
import gc
import pygame
import json

# Pour les maniacs qui aiment pas le message de pygame :)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from MainMenu import mainMenu
from Leaderboard import leaderboard

pygame.init()

# Dimensions de la fenêtre
WIDTH = 1920
HEIGHT = 1080

# Chargement des données
windowsdata = json.load(open("windowsdata.json", "r"))

# Création de la fenêtre
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Mise en place d'un nom à la fenêtre le temps du chargement
pygame.display.set_caption("Toybattle")

# Lancement de la clock
clock = pygame.time.Clock()

def cleanup(screen, ressources, hover_sound):
        try:
            hover_sound.stop()
        except Exception:
            pass
        for ressource in ressources.keys():
            ressources[ressource] = None
        gc.collect()
        screen.fill((0, 0, 0))
        pygame.display.flip()
        return ressources

menu = mainMenu(screen, clock, windowsdata, WIDTH, HEIGHT)

# Gestion des redirections entre les menus
while True:
    if menu == "mainMenu":
        menu = mainMenu(screen, clock, windowsdata, WIDTH, HEIGHT)
    elif menu == "leaderboard":
        menu = leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT)
    elif menu == "play":
        print("Ba mtn faut faire le jeu là")
        break