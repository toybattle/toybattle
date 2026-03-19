from .db import supabase

def sign_in(email, password):
    """Connecter un utilisateur existant"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        print("✅ Connexion réussie!")
        print(f"Connecté: {response.user.email}")
        return response
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None