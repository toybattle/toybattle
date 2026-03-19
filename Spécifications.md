# Projet : Toy Battle

## I. Spécifications

### Titre du sujet
**Sujet 7 : Le jeu « Toy Battle »**

---

### Objectifs du projet

Le projet consiste à développer un jeu de société numérique nommé **Toy Battle**.

Le système sera composé de plusieurs éléments :

- Un jeu développé en Python avec la bibliothèque Pygame
- Un launcher en C# (WPF) permettant :
  - La mise à jour du jeu
  - Le suivi des actualités
- Un site web permettant :
  - D’expliquer les règles du jeu
  - D’afficher un leaderboard (classement des joueurs)
- Une base de données SQL distante (Supabase) pour :
  - Stocker les comptes joueurs
  - Enregistrer les parties et statistiques
- Un mode multijoueur utilisant *socket* 
  - Hébergement envisagé : Render ou Koyeb
- Utilisation de fichiers JSON pour :
  - Stocker les cartes des personnages
  - Définir les maps (Nom, image et cordonnées des cases)
- Conversion en .exe via la library pyinstaller

---

### Fonctionnalités détaillées

#### Outils

- Utilisation d'un fichier requirements.txt pour gérer les libraires nécessaires
```
pip install -r requirements.txt
```
- Utilisation de la base de données Supabase en ligne
- Utilisation de l'éditeur de registre pour stocker les données de connexion de l'utilisateur (pour éviter la reconnexion à chaque lancement)
#### Fonctions

- Connexion / inscription des joueurs
- Sauvegarde de l’authentification (registre système)
- Création d’un salon multijoueur
- Rejoindre un salon via un nom d'utilisateur
- Choix du mode de jeu :
  - Joueur vs Joueur
  - Joueur vs IA
- Attribution aléatoire :
  - De la map
  - Du camp (Rouge / Bleu)
- Système de tirage de cartes
- Gestion des tours de jeu
- Détection des conditions de victoire
- Mise à jour des statistiques en fin de partie
- Consultation du leaderboard

---

### Interfaces (IHM)

- Menu de connexion / inscription
- Menu principal du jeu
- Menu de création / rejoindre un salon
- Interface de jeu (plateau + cartes)
- Écran de fin de partie (Victoire / Défaite)
- Menu statistiques
- Menu leaderboard

---

## II. Conception détaillée

### Classes principales

- Joueur
- Partie
- Plateau

---

### Données (Tables SQL)

- Comptes joueurs
- Parties

---

### Fichiers (JSON)

- Plateaux
- Unités / Cartes

---

### Fonctions principales

#### Authentification
- SignIn()
- SignUp()
- SignOut()

#### Multijoueur
- CréerSalon()
- RejoindreSalon(idSalon)
- LancerPartie()

#### Gameplay
- JouerTour()
- PlacerCarte()
- PiocherCarte()
- VerifierConditionsVictoire()

#### Statistiques
- MettreAJourStats()

---

### Planning prévisionnel

| Tâche | Responsable | Date |
|------|------------|------|
| Conception du projet | Maxime/Louis | Semaine 1 |
| Base de données (Supabase) | Maxime | En paralèlle |
| Développement du jeu (Pygame) | Maxime/Louis | Semaines 2-4 |
| Mise en place du multijoueur | Maxime/Louis | Semaines 3-5 |
| Développement du launcher (C#) | Louis | Si il y a le temps |
| Création du site web | Louis | En parallèle |
| Tests et corrections | Maxime/Louis | Au fur et à mesure |

## Scripts extérieurs
- Récuperation d'un code pour gérer les effet de particule en ligne
- Utilisation de la librairie supabase (fonctions de connexions et de requêtes natives)