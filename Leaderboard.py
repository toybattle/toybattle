import pygame
import sys

def leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT):
    img = pygame.image.load("assets/Menus/Leaderboard/Leaderboard.png").convert()
    img = pygame.transform.scale(img, (800, 600))  # Redimensionne
    screen.blit(img, (0, 0))
    pygame.display.flip()
    print("Affichage du leaderboard")