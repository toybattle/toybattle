import pygame
import sys

def leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT):
    img = pygame.image.load("assets/Menus/Leaderboard/Leaderboard.png").convert()
    img = pygame.transform.scale(img, (WIDTH, HEIGHT))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        screen.blit(img, (0, 0))
        pygame.display.flip()
        clock.tick(60)