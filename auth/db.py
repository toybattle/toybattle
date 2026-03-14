import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

def conn():
    current_dir = Path(__file__).parent.absolute()
    env_path = current_dir / "db.env"

    load_dotenv(env_path)
    
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

supabase = conn()