import pygame
import sys
import os
import requests
import asyncio
import time
import random
import threading
from DetectUpdate import wating_for_player

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'auth'))
from db import supabase

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
    
    def insert(host, game_id):
        try:
            response = (
                supabase.table("games")
                .insert([
                    {"host": host, "client": "WAITING", "room_id": game_id, "status": "WAITING"},
                ])
                .execute()
            )
            return response
        except Exception as exception:
            return exception
        
    def update(client, game_id):
        try:
            response = (
                supabase.table("games")
                .update([
                    {"client": client, "status": "started"},
                ])
                .eq("room_id", game_id)
                .execute()
            )
            return response
        except Exception as exception:
            return exception
    
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
    # BASE_URL = "https://flask-production-2976.up.railway.app"
    BASE_URL = "https://toybattle.onrender.com"

    # Requête API pour créer une partie
    def create_game():
        try:
            # On augmente le timeout à 20s car le serveur Railway peut mettre du temps à démarrer (cold start)
            r = requests.post(f"{BASE_URL}/create_game", timeout=20)
            data = r.json()
            print(f"Create game response: {data}")
            return data.get("game_id"), data.get("map_id")
        except Exception as e:
            print(f"Erreur lors de la création de la partie: {e}, génération locale")
            game_id = "".join(str(random.randint(0,9)) for _ in range(4))
            map_id = random.randint(0,1)
            print(f"Généré localement: game_id={game_id}, map_id={map_id}")
            return game_id, map_id

    # Requête API pour rejoindre une partie
    def join_game(game_id, player):
        try:
            r = requests.post(f"{BASE_URL}/join_game", json={
                "game_id": game_id,
                "player": player
            }, timeout=20)
            return r.json()
        except Exception as e:
            print(f"Erreur lors de l'accès à la partie: {e}, simulation réussite")
            return {"game": {"map_id": random.randint(0,1)}}

    game_id = ""
    map_id = None

    waiting = False
    player_joined = False
    start_time = 0

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
                    # Si on n'a pas déjà un code, on en crée un
                    if not text:
                        new_game_id, new_map_id = create_game()
                        if new_game_id:
                            game_id, map_id = new_game_id, new_map_id
                            res = join_game(game_id, "server")
                            text = game_id  # Afficher le code généré dans la zone d'input
                            print(f"Partie créée avec l'ID: {game_id}")
                            insert_result = insert("server", game_id)
                            print(f"Insert result: {insert_result}")
                            waiting = True
                            start_time = time.time()
                            def wait_thread():
                                nonlocal player_joined
                                result = asyncio.run(wating_for_player(game_id))
                                player_joined = result
                            threading.Thread(target=wait_thread, daemon=True).start()
                        else:
                            text = "Erreur création partie"
                            print("Échec de la création de la partie via l'API")

                    # On ne retourne plus ici pour rester dans le menu et afficher l'ID

                if buttons['client'].collidepoint(mouse_pos):
                    if len(text) > 0:
                        game_id = text
                        res = join_game(game_id, "client")
                        if "error" not in res:
                            # On récupère les infos de la partie depuis le serveur
                            game_info = res.get("game", {})
                            update("client", game_id)
                            map_id = game_info.get("map_id", 0)
                            gamedata = {'game_id' : game_id, 'role' : 'client', 'map' : map_id}
                            return ['multi', gamedata]
                        else:
                            print(f"Erreur lors de la connexion: {res.get('error')}")

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

        if waiting and player_joined:
            game_info = res.get("game", {})
            map_id = game_info.get("map_id", 0)
            gamedata = {'game_id' : game_id, 'role' : 'server', 'map' : map_id}
            return ['multi', gamedata]
        elif waiting and time.time() - start_time > 10:
            text = "Recherche de joueur expirée"
            time.sleep(2)
            return ['menu']

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