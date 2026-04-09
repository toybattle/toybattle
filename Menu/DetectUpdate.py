import asyncio
import threading
from supabase import acreate_client
import time
SUPABASE_URL = "https://okvqvwpnlzkjquwliuhy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rdnF2d3BubHpranF1d2xpdWh5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1MDgxNTIsImV4cCI6MjA4OTA4NDE1Mn0.qHIL64t-54JljDrCoX5QD4qgpMeOwCp83GtXcJdJpwc"

async def w(game_id):
    supabase = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
    print("client initialized")

    channel = supabase.channel("realtime-room-1234")
    print("Channel listened")

    player_found = asyncio.Event()

    def on_update(payload):
        new_data = payload.get("new", {})
        old_data = payload.get("old", {})

        if old_data.get("status", "").lower() == "waiting" and new_data.get("status", "").lower() == "started":
            print("Joueur trouvé")
            player_found.set()  # signal pour arrêter le timeout

    await channel.on_postgres_changes(
        "UPDATE",
        schema="public",
        table="games",
        filter=f"room_id=eq.{game_id}",
        callback=on_update
    ).subscribe()

    try:
        # Attend jusqu'à 5 secondes ou jusqu'à ce qu'un joueur soit trouvé
        await asyncio.wait_for(player_found.wait(), timeout=10)
        print("Matchmaking réussi")
        return True
    except asyncio.TimeoutError:
        await supabase.table('games').update({'status': 'timed_out'}).eq('room_id', game_id).execute()
        print("Matchmaking timed out")
        return False

# Wrapper pour thread
def wating_for_player(game_id):
    def run_asyncio():
        asyncio.run(w(game_id))  # crée un loop propre pour ce thread
    threading.Thread(target=run_asyncio, daemon=True).start()

# Exemple
wating_for_player(1350)


for i in range(10):
    print(i)
    time.sleep(3)