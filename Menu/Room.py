import pygame
import sys
import requests

from Utils import cleanup, load_path

def room(screen, clock, windowsdata, WIDTH, HEIGHT):

    def compute_buttons(w, h):
        btns = {}
        for element in windowsdata[1]["tiles"]:
            btn = pygame.Rect(
                int(element["x"] * w),
                int(element["y"] * h),
                int(element["width"] * w),
                int(element["height"] * h)
            )
            btns[element["id"]] = btn
        return btns
    
    def scale_surfaces(w, h, btns):
        return (
            pygame.transform.scale(background_orig, (w, h)),
            pygame.transform.scale(server_orig, (btns["server"].width, btns["server"].height)),
            pygame.transform.scale(client_orig, (btns["client"].width, btns["client"].height)),
        )
    
    pygame.display.set_caption("Room")

    # Définition des couleurs
    GREY = (208, 208, 208)


    background_orig = pygame.image.load(load_path("assets/Menus/Room", "Room.png")).convert()
    server_orig = pygame.image.load(load_path("assets/Menus/Room", "Server.png")).convert_alpha()
    client_orig = pygame.image.load(load_path("assets/Menus/Room", "Client.png")).convert_alpha()

    current_width, current_height = WIDTH, HEIGHT
    buttons = compute_buttons(current_width, current_height)
    display_background, display_server_button, display_client_button = scale_surfaces(current_width, current_height, buttons)

    ressources = {
        "background_orig": background_orig,
        "server_orig": server_orig,
        "client_orig": client_orig,

        "background": display_background,
        "server": display_server_button,
        "client": display_client_button
    }

    buttons_textures = {
        "server": display_server_button,
        "client": display_client_button
    }

    hover_state = {button_id: False for button_id in buttons}
    hover_progress = {button_id: 0.0 for button_id in buttons}
    hover_scale_max = 1.08
    hover_anim_speed = 12.0
    dt = 1 / 60

    hover_sound = pygame.mixer.Sound(load_path("assets/sound", "btn_hover.mp3"))
    hover_sound.set_volume(0.3)

    # Création de la case pour entrer le game_id
    input_box = buttons['input']
    active = False
    text = ""

    # Url du serveur de jeu
    BASE_URL = "http://127.0.0.1:8000"
    # BASE_URL = "flask-production-2976.up.railway.app"

    # Requête API pour créer une partie
    def create_game():
        r = requests.post(f"{BASE_URL}/create_game")
        data = r.json()
        print(data)
        return data["game_id"], data["map_id"]

    # Requête API pour rejoindre une partie
    def join_game(game_id, player):
        r = requests.post(f"{BASE_URL}/join_game", json={
            "game_id": game_id,
            "player": player
        })
        print(r.json())

    game_id = ""  # Déplacer game_id en dehors de la boucle

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


            if event.type == pygame.VIDEORESIZE:
                current_width, current_height = max(480, event.w), max(270, event.h)
                screen = pygame.display.set_mode((current_width, current_height), pygame.RESIZABLE)
                buttons = compute_buttons(current_width, current_height)
                display_background, display_server_button, display_client_button = scale_surfaces(current_width, current_height, buttons)


            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if buttons["server"].collidepoint(mouse_pos):
                    # On nettoie la fenetre et la mémoire avant de changer de menu
                    ressources = cleanup(screen, ressources, hover_sound)
                    game_id, map_id = create_game()
                    join_game(game_id, "server")
                    text = game_id  # afficher l'ID dans l'input
                    gamedata = {'game_id' : game_id, 'role' : 'server', 'map' : map_id}
                    # return ['play', gamedata]

                if buttons['client'].collidepoint(mouse_pos):
                    # On nettoie la fenetre et la mémoire avant de changer de menu
                    ressources = cleanup(screen, ressources, hover_sound)
                    if len(text) > 0:
                        game_id = text
                        join_game(game_id, "client")
                        gamedata = {'game_id' : game_id, 'role' : 'client', 'map' : map_id}
                        # return ['play', gamedata]

                if buttons["input"].collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                    

            if event.type == pygame.KEYDOWN and active:
                # Gestion de l'input du code
                if event.key == pygame.K_RETURN:
                    game_id = text
                    print(f"Entered text: {game_id}")
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    # Vérification si le caractère entré est un chiffre
                    if event.unicode.isdigit() and len(text) < 4:
                        text += event.unicode

        screen.blit(display_background, (0,0))
        screen.blit(display_server_button, (buttons["server"].x, buttons["server"].y))
        screen.blit(display_client_button, (buttons["client"].x, buttons["client"].y))

        # Créer une surface temporaire pour l'input (transparente)
        input_surf = pygame.Surface((input_box.w, input_box.h), pygame.SRCALPHA)
        input_surf.fill((255, 255, 255, 0))  # semi-transparent

        # Calculer une police dynamique pour remplir l'input
        dynamic_font_size = int(input_box.h * 0.7)  # 70% de la hauteur de l'input
        dynamic_font = pygame.font.Font(None, dynamic_font_size)

        # Rendre le texte
        txt_surface = dynamic_font.render(text, True, GREY)

        # Centrer le texte dans la boîte
        txt_rect = txt_surface.get_rect(center=(input_box.w // 2, input_box.h // 2))

        # Afficher la boîte et le texte
        screen.blit(input_surf, (input_box.x, input_box.y))
        screen.blit(txt_surface, (input_box.x + txt_rect.x, input_box.y + txt_rect.y))


        for button_id, button in buttons.items():
            is_hover = button.collidepoint(mouse_pos)
            # Jouer le son UNIQUEMENT quand on entre sur le bouton
            if is_hover and not hover_state[button_id] and (button_id != "input"):
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

            if(button_id != "input"):
                source_surface = buttons_textures[button_id] 
                scaled_surface = pygame.transform.smoothscale(source_surface, (scaled_width, scaled_height))
                scaled_rect = scaled_surface.get_rect(center=button.center)
                screen.blit(scaled_surface, scaled_rect)

        pygame.display.flip()
        dt = clock.tick(60) / 1000