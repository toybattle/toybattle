# Cahier des charges — Toy Battle
**Projet Python — CPII 2ème année**
**Sujet 7 : Le jeu « Toy Battle »**

---

## 1. Objectifs du projet

Développer un jeu de plateau en tour par tour, *Toy Battle*, en Python avec une interface graphique via **pygame**. Le jeu se joue à 2 joueurs en réseau local, avec une option contre l'ordinateur.

---

## 2. Fonctionnalités principales

### 2.1 Gestion des joueurs
- Création de compte (pseudo + mot de passe)
- Connexion / déconnexion
- Consultation des statistiques (victoires, défaites, parties jouées)

### 2.2 Modes de jeu
- Joueur vs Joueur en réseau local *(obligatoire)*
- Joueur vs Ordinateur *(optionnel mais recommandé)*

### 2.3 Plateau de jeu
- Affichage graphique du plateau avec pygame
- Gestion des unités (déplacement, attaque, points de vie)
- Gestion des tours (alternance entre les joueurs)
- Détection de fin de partie (conditions de victoire)
- Idéalement : plusieurs plateaux disponibles

### 2.4 Interface graphique
- Menu principal (jouer, statistiques, quitter)
- Écran de connexion / inscription
- Affichage du plateau en temps réel
- Affichage des informations de jeu (tour en cours, unités restantes…)

---

## 3. Architecture technique

### 3.1 Classes envisagées

| Classe | Rôle |
|--------|------|
| `Joueur` | Pseudo, mot de passe, statistiques |
| `Partie` | Plateau, joueurs, tour en cours |
| `Plateau` | Grille, cases |
| `Unite` | Type, points de vie, attaque, déplacement |
| `Reseau` | Gestion client/serveur (sockets) |

### 3.2 Stockage des données
- Fichier **JSON** ou base **SQLite** pour les comptes et statistiques des joueurs

### 3.3 Réseau
- Communication client/serveur via le module `socket` de Python
- Un joueur héberge la partie (serveur), l'autre se connecte (client)

---

## 4. IHM — Interfaces

### Écran 1 : Menu principal
```
[ Toy Battle ]
  > Se connecter
  > Créer un compte
  > Quitter
```

### Écran 2 : Menu de jeu (après connexion)
```
[ Bienvenue, <pseudo> ]
  > Jouer en réseau
  > Jouer contre l'ordinateur
  > Voir mes statistiques
  > Se déconnecter
```

### Écran 3 : Plateau de jeu
- Grille de jeu affichée graphiquement
- Panneau latéral : unités, points de vie, tour en cours
- Bouton / touche pour passer son tour ou quitter

---

## 5. Planning prévisionnel

| Séance | Tâche | Responsable |
|--------|-------|-------------|
| S1 | Spécifications + conception détaillée | Binôme |
| S2 | Structure du projet, classes de base, affichage plateau | Joueur A |
| S2 | Gestion des comptes + stockage | Joueur B |
| S3 | Logique du jeu (tours, attaques, victoire) | Joueur A |
| S3 | Communication réseau (sockets) | Joueur B |
| S4 | Intégration + tests | Binôme |
| S5 | Finitions, rapport, soutenance | Binôme |

---

## 6. Points d'attention

- Le **réseau est obligatoire** pour ce sujet — c'est la partie la plus complexe, à commencer tôt
- Bien séparer la **logique de jeu** de l'**affichage** (facilite les tests)
- Prévoir une **synchronisation des états** du plateau entre les deux machines
- Commenter le code dès le début
- Utiliser impérativement **pygame** pour l'interface graphique
