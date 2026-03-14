from .db import supabase

def sign_up(email, password):
    """Connecter un utilisateur existant"""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print("✅ Inscription réussie!")
        print(f"Connecté: {response.user.email}")
        return response
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None