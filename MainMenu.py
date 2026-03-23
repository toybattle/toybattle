import pygame
import sys
import gc
from Leaderboard import leaderboard

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

def mainMenu(screen, clock, windowsdata, WIDTH, HEIGHT):

    # Import des boutons dans un dictionnaire
    buttons = {}
    for element in windowsdata[0]["tiles"]:
        button = pygame.Rect(
            int(element["x"] * WIDTH),
            int(element["y"] * HEIGHT),
            int(element["width"] * WIDTH),
            int(element["height"] * HEIGHT)
        )
        buttons[element["id"]] = button
    
    # Affichage du nom du menu principal
    pygame.display.set_caption("Menu principal")

    # Chargement des images
    background = pygame.image.load(r"assets/Menus/MainMenu/MainMenu.png").convert()
    play_button = pygame.image.load(r"assets/Menus/MainMenu/PlayButton.png").convert_alpha()
    leaderboard_button = pygame.image.load(r"assets/Menus/MainMenu/LeaderboardButton.png").convert_alpha()
    quit_button = pygame.image.load(r"assets/Menus/MainMenu/QuitButton.png").convert_alpha()

    #Adaptation de la taille des images
    display_background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    display_play_button = pygame.transform.scale(play_button, (buttons["play"].width, buttons["play"].height))
    display_leaderboard_button = pygame.transform.scale(leaderboard_button, (buttons["leaderboard"].width, buttons["leaderboard"].height))
    display_quit_button = pygame.transform.scale(quit_button, (buttons["quit"].width, buttons["quit"].height))

    # On mets toutes les textures dans un disctionnaire pour les libérer plus facilement lors du nettoyage
    ressources = {
        "background": background,
        "play_button": play_button,
        "leaderboard_button": leaderboard_button,
        "quit_button": quit_button,
        "display_background": display_background,
        "display_play_button": display_play_button,
        "display_leaderboard_button": display_leaderboard_button,
        "display_quit_button": display_quit_button
    }

    # On créé un dictionnaire pour stocker les textures des boutons afin de les réutiliser dans les animations
    buttons_textures = {
        "play": display_play_button,
        "leaderboard": display_leaderboard_button,
        "quit": display_quit_button
    }

    # Pour chaque bouton, on initialise une variable de progression d'animation à 0 dans un dictionnaire, la taille max de l'image et la vitesse de l'animation
    hover_state = {button_id: False for button_id in buttons}
    hover_progress = {button_id: 0.0 for button_id in buttons}
    hover_scale_max = 1.08
    hover_anim_speed = 12.0
    dt = 1 / 60

    #Chargement de l'effet sonore de hover:
    hover_sound = pygame.mixer.Sound("assets/sound/btn_hover.mp3")
    hover_sound.set_volume(0.3)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if buttons["play"].collidepoint(mouse_pos):
                    print("Play button clicked")
                    # On nettoie la fenetre et la mémoire avant de changer de menu
                    ressources = cleanup(screen, ressources, hover_sound)
                    print("Lancement du jeu")
                    return 'play'

                if buttons['leaderboard'].collidepoint(mouse_pos):
                    # On nettoie la fenetre et la mémoire avant de changer de menu
                    ressources = cleanup(screen, ressources, hover_sound)
                    return 'leaderboard'

                if buttons['quit'].collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
                
        # Affichage du fond et des boutons
        screen.blit(display_background, (0,0))
        screen.blit(display_play_button, (buttons["play"].x, buttons["play"].y))
        screen.blit(display_leaderboard_button, (buttons["leaderboard"].x, buttons["leaderboard"].y))
        screen.blit(display_quit_button, (buttons["quit"].x, buttons["quit"].y))

    # Pour chaque bouton, on met à jour la progression de l'animation pour chaque bouton en fonction de si la souris est dessus ou non
        for button_id, button in buttons.items():
            is_hover = button.collidepoint(mouse_pos)

            # Jouer le son UNIQUEMENT quand on entre sur le bouton
            if is_hover and not hover_state[button_id]:
                hover_sound.play()

            hover_state[button_id] = is_hover

            target = 1.0 if is_hover else 0.0
            hover_progress[button_id] += (target - hover_progress[button_id]) * min(1.0, hover_anim_speed * dt)
    
            progress = hover_progress[button_id]
            if progress <= 0.001:
                continue

            scale = 1.0 + (hover_scale_max - 1.0) * progress
            scaled_width = max(1, int(button.width * scale))
            scaled_height = max(1, int(button.height * scale))

            source_surface = buttons_textures[button_id]
            scaled_surface = pygame.transform.smoothscale(source_surface, (scaled_width, scaled_height))
            scaled_rect = scaled_surface.get_rect(center=button.center)
            screen.blit(scaled_surface, scaled_rect)

        pygame.display.flip()
        dt = clock.tick(60) / 1000