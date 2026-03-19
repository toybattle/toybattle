from .db import supabase

def sign_out():
    """Déconnexion"""
    try:
        supabase.auth.sign_out()
        print("\n✅ Déconnecté avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")