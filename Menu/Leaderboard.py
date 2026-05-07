import pygame
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'auth'))
from db import supabase
from Utils import load_path

def statsCalc(data):
    raw_stats = {}
    stats = {}

    for game in data:
        for player in [game['client'], game['host']]:

            if player not in raw_stats:
                raw_stats[player] = {
                    'victoires': 0,
                    'games': 0,
                    'winrate': 0
                }

            raw_stats[player]['games'] += 1

            if game['win'] == player:
                raw_stats[player]['victoires'] += 1

            raw_stats[player]['winrate'] = round(raw_stats[player]['victoires'] / raw_stats[player]['games'] * 100, 2)
            
            
    # Tri des joueurs par victoires décroissante
    sorted_players = sorted(raw_stats.items(), key=lambda x: x[1]['victoires'], reverse=True)
    
    return sorted_players


def leaderboard(screen, clock, windowsdata, WIDTH, HEIGHT):

    leaderboard = pygame.image.load(load_path("assets/Menus/Leaderboard", "Leaderboard.png")).convert()
    display_leaderboard = pygame.transform.scale(leaderboard, (WIDTH, HEIGHT))
    
    ui_font = pygame.font.SysFont(None, 24)

    try: 
        (response, count) = (supabase
        .table("games")
        .select("*")
        .execute()
        )
        data = response[1]

    except Exception as error:
        print(f"Erreur lors du fetch leaderboard : {error}")

    print(data)
    
    leaderboard_tiles = []
    for window in windowsdata:
        if window.get("name") == "Leaderboard":
            leaderboard_tiles = window.get("tiles", [])
            break
        
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
        
        for tile in leaderboard_tiles:
            x = int(tile["x"] * WIDTH)
            y = int(tile["y"] * HEIGHT)
            w = int(tile["width"] * WIDTH)
            h = int(tile["height"] * HEIGHT)
            mode_text = tile.get("text", "Tile")
            mode_render = ui_font.render(mode_text, True, (210, 210, 220))
            # Centrage horizontal et vertical du texte dans le tile
            text_rect = mode_render.get_rect(center=(x + w // 2, y + h // 2))
            screen.blit(mode_render, text_rect)
            
        pygame.display.flip()
        clock.tick(60)