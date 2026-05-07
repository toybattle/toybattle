import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'auth'))
from db import supabase


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
            
            
    # // Tri des joueurs par winrate décroissante
    sorted_players = sorted(raw_stats.items(), key=lambda x: x[1]['victoires'], reverse=True)
    
    return sorted_players
try: 
    (response, count) = (supabase
        .table("games")
        .select("*")
        .execute()
        )
    data = response[1]
    
    # print(data)

except Exception as error:
    print(f"Erreur lors du fetch leaderboard : {error}")

print(statsCalc(data))