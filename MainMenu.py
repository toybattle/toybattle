import pygame
import sys
import json
import os 

pygame.init()

# Dimensions de la fenêtre
WIDTH = 1920
HEIGHT = 1080

# Chargement des données
data = json.load(open("windowsdata.json", "r"))

tiles = {}
for tile in data[0]["tiles"]:
    new_tile = pygame.Rect(
        int(tile["x"] * WIDTH),
        int(tile["y"] * HEIGHT),
        int(tile["width"] * WIDTH),
        int(tile["height"] * HEIGHT)
    )
    tiles[tile["id"]] = new_tile


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu principal")

# Chargement de l'image
image = pygame.image.load(r"assets/MainMenu.jpg").convert()

#Adaptation de la taille de l'image
display_img = pygame.transform.scale(image, (WIDTH, HEIGHT))

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if tiles["play"].collidepoint(mouse_pos):
                print("Play button clicked")

    screen.blit(display_img, (0,0))
    pygame.display.flip()
    clock.tick(60)