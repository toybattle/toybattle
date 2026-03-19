import pygame
import sys

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

clock = pygame.time.Clock()

# Charger ta texture
water = pygame.image.load(r"C:\Users\63043998\Desktop\ToyBattle\toybattle\assets\water.png").convert()

tile_size = 256
water = pygame.transform.scale(water, (tile_size, tile_size))

# Deux couches
water2 = pygame.transform.rotate(water, 90)

offset1_x = 0
offset1_y = 0
offset2_x = 0
offset2_y = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Animation
    offset1_x += 0.3
    offset1_y += 0.2

    offset2_x += 0.1
    offset2_y += 0.25

    # Dessin couche 1
    for x in range(-tile_size, WIDTH + tile_size, tile_size):
        for y in range(-tile_size, HEIGHT + tile_size, tile_size):
            screen.blit(water, (x - offset1_x % tile_size, y - offset1_y % tile_size))

    # Dessin couche 2 (transparente)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for x in range(-tile_size, WIDTH + tile_size, tile_size):
        for y in range(-tile_size, HEIGHT + tile_size, tile_size):
            overlay.blit(water2, (x - offset2_x % tile_size, y - offset2_y % tile_size))

    overlay.set_alpha(80)
    screen.blit(overlay, (0, 0))
    
    pygame.display.flip()
    clock.tick(60)