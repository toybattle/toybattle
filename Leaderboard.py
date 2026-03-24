import pygame
import sys

def leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT):

    # Chargement de l'image
    leaderboard = pygame.image.load("assets/Menus/Leaderboard/Leaderboard.png").convert()

    # Adaptation de la taille de l'image
    display_leaderboard = pygame.transform.scale(leaderboard, (WIDTH, HEIGHT))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        screen.blit(display_leaderboard, (0, 0))
        pygame.display.flip()
        clock.tick(60)