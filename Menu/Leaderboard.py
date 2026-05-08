import pygame
import sys
import os
import winreg
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'auth'))
from db import supabase
from Utils import load_path

def get_username():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ToyBattle") as key:
            username, _ = winreg.QueryValueEx(key, "username")
            return username
    except FileNotFoundError:
        return None
    except OSError:
        return None

def statsCalc(data):
    raw_stats = {}

    for game in data:
        host = game.get('host')
        client = game.get('client')
        winner = game.get('win')

        if winner == 'client':
            winner = client
        elif winner == 'host':
            winner = host

        for player in (host, client):
            if not player:
                continue

            if player not in raw_stats:
                raw_stats[player] = {
                    'victoires': 0,
                    'games': 0,
                    'winrate': 0
                }

            raw_stats[player]['games'] += 1
            if player == winner:
                raw_stats[player]['victoires'] += 1

            raw_stats[player]['winrate'] = round(
                raw_stats[player]['victoires'] / raw_stats[player]['games'] * 100,
                2
            )

    sorted_players = sorted(
        raw_stats.items(),
        key=lambda x: (x[1]['victoires'], x[1]['winrate'], x[1]['games'], x[0]),
        reverse=True
    )

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
        data = []

    print(data)
    
    leaderboard_tiles = []
    for window in windowsdata:
        if window.get("name") == "Leaderboard":
            leaderboard_tiles = window.get("tiles", [])
            break

    current_user = get_username()
    
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

        player_stats = statsCalc(data)
        sorted_tiles = sorted(leaderboard_tiles, key=lambda t: (round(t.get('y', 0), 1), t.get('x', 0)))

        # Group tiles by rows using y coordinate
        rows = []
        for tile in sorted_tiles:
            y_key = round(tile.get('y', 0), 1)
            if not rows or rows[-1][0] != y_key:
                rows.append((y_key, [tile]))
            else:
                rows[-1][1].append(tile)

        # Prepare top 3 and current user row
        top_players = [player for player in player_stats if player[0] != current_user][:3]
        current_player = next((player for player in player_stats if player[0] == current_user), None)

        leaderboard_rows = top_players[:3]
        if current_user:
            leaderboard_rows.append(current_player or (current_user, {'victoires': 0, 'games': 0, 'winrate': 0}))
        else:
            leaderboard_rows = player_stats[:4]

        for row_index, (_, row_tiles) in enumerate(rows):
            if row_index >= len(leaderboard_rows):
                break

            row_tiles = sorted(row_tiles, key=lambda t: t.get('x', 0))
            player = leaderboard_rows[row_index]
            values = [
                str(row_index + 1),
                player[0],
                str(player[1]['victoires']),
                f"{player[1]['winrate']}%"
            ]

            for col_index, tile in enumerate(row_tiles):
                if col_index >= len(values):
                    break

                x = int(tile['x'] * WIDTH)
                y = int(tile['y'] * HEIGHT)
                w = int(tile['width'] * WIDTH)
                h = int(tile['height'] * HEIGHT)
                text = values[col_index]
                mode_render = ui_font.render(text, True, (210, 210, 220))
                text_rect = mode_render.get_rect(center=(x + w // 2, y + h // 2))
                screen.blit(mode_render, text_rect)

        pygame.display.flip()
        clock.tick(60)