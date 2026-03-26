import pygame
import sys

from Utils import load_path

def leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT):

    leaderboard = pygame.image.load(load_path("assets/Menus/Leaderboard", "Leaderboard.png")).convert()
    display_leaderboard = pygame.transform.scale(leaderboard, (WIDTH, HEIGHT))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                return 'mainMenu'

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return 'mainMenu'

        screen.blit(display_leaderboard, (0, 0))
        pygame.display.flip()
        clock.tick(60)