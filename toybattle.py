import pygame
import json

from MainMenu import mainMenu

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

menu = mainMenu(screen, clock, windowsdata, WIDTH, HEIGHT)

while True:
    if menu == 'play':
        # menu = fonction renvoyant à la création/join de game
        print("Lancement du jeu")
        break