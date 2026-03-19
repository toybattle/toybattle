import pygame
import sys

pygame.init()

WIDTH = 400
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Map")

background = pygame.image.load(r"C:\Users\louis\Documents\ToyBattle\assets\map\MapGlace.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

temp_tile = None
temp_start_pos = None

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if temp_start_pos is None:
                temp_start_pos = mouse_pos
            else:
                # Deuxième clic pour définir la fin du rectangle
                x1, y1 = temp_start_pos
                x2, y2 = mouse_pos
                    
                # Calculer le rectangle correctement (gérer les clics dans n'importe quel ordre)
                x = min(x1, x2)
                y = min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                
                print(f"\n--- Tile à ajouter ---")
                print(f"Coordonnées: pygame.Rect({x}, {y}, {width}, {height}),")
                print("----------------------\n")
                
                # Réinitialiser pour la prochaine tile
                temp_start_pos = None
                    
    screen.blit(background, (0, 0))


    # Dessiner le rectangle
    if temp_start_pos:
        current_pos = pygame.mouse.get_pos()
        x1, y1 = temp_start_pos
        x2, y2 = current_pos
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        temp_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (0, 255, 0), temp_rect, 2)

    pygame.display.flip()
    clock.tick(60)