# Rapport Final — Projet Python 2025-2026
## Sujet 7 : Le jeu « Toy Battle »

**CPII deuxième année**
**Binôme :** Maxime Beaudoin & Louis Denarie
**Date de soutenance :** 26/05/2026

---

## Sommaire

1. [Introduction](#1-introduction)
2. [Rappel des spécifications et de la conception détaillée](#2-rappel-des-spécifications-et-de-la-conception-détaillée)
3. [Méthode générale de résolution](#3-méthode-générale-de-résolution)
4. [Détail des parties difficiles ou originales](#4-détail-des-parties-difficiles-ou-originales)
5. [Problèmes rencontrés et solutions apportées](#5-problèmes-rencontrés-et-solutions-apportées)
6. [Écarts par rapport au cahier des charges](#6-écarts-par-rapport-au-cahier-des-charges)
7. [Bilan](#7-bilan)
8. [Conclusion](#8-conclusion)

---

## 1. Introduction

Dans le cadre du projet Python de deuxième année CPII, nous avons choisi de développer une version numérique du jeu de société **Toy Battle**, classé parmi les sujets difficiles. Ce jeu de plateau stratégique oppose deux joueurs qui s'affrontent en jouant des cartes sur un plateau commun, avec pour objectif de contrôler des zones d'étoiles pour remporter la victoire.

Ce projet nous a permis de mobiliser et d'approfondir de nombreuses compétences : la programmation orientée objet, la conception d'interfaces graphiques avec Pygame, la mise en réseau via une API REST, et la gestion de données avec une base de données distante Supabase.

L'ambition du projet allait au-delà du seul jeu : nous avons souhaité livrer un produit complet, comprenant un lanceur (launcher), un site web public et un serveur de jeu hébergé dans le cloud.

---

## 2. Rappel des spécifications et de la conception détaillée

### 2.1 Objectifs initiaux

Le projet visait à produire un ensemble cohérent d'outils autour du jeu Toy Battle :

| Composant | Description |
|---|---|
| **Jeu (Python/Pygame)** | Application graphique jouable en solo (vs IA) et en multijoueur réseau |
| **Launcher (C#/WPF)** | Application de gestion des mises à jour et de connexion au compte |
| **Site web** | Présentation des règles et affichage du classement (leaderboard) |
| **Base de données (Supabase)** | Stockage des comptes joueurs, des parties et des statistiques |
| **Serveur multijoueur** | Hébergé sur Render, assurant la synchronisation des parties en ligne |

### 2.2 Fonctionnalités prévues

- Connexion / inscription des joueurs
- Sauvegarde de l'authentification (registre système Windows)
- Création et rejoindre un salon multijoueur
- Choix du mode de jeu : Joueur vs Joueur ou Joueur vs IA
- Attribution aléatoire de la map et du camp (Rouge / Bleu)
- Système de tirage et de pose de cartes
- Gestion des tours de jeu
- Détection des conditions de victoire (contrôle des zones d'étoiles)
- Mise à jour des statistiques en fin de partie
- Consultation du leaderboard

### 2.3 Conception détaillée

#### Classes principales

- **`Cards`** : Représente une carte avec ses attributs (id, nom, force, description de capacité, chemin d'image).
- **`GameMulti`** / **`GameSolo`** : Contiennent la logique complète d'une partie (multijoueur réseau ou solo contre l'IA).
- **`MenuMaker`** : Gère le rendu des interfaces à partir des données JSON de `windows_data.json`.
- **`Room`** : Gère la création et le rejoindre d'un salon multijoueur.
- **`Leaderboard`** : Affiche le classement depuis la base de données.
- **`DetectUpdate`** : Vérifie si une mise à jour du jeu est disponible.

#### Structure des fichiers de données

**`datacards.json`** — Définition de chaque carte :
```json
{
    "id": 1,
    "name": "Skully",
    "image_path": "Skully.png",
    "strength": 1,
    "ability_desc": "Piocher 2 cartes"
}
```

**`map_data.json`** — Définition de chaque plateau (cases, liens entre cases, zones d'étoiles) :
```json
"MapGlace": {
    "image_path": "assets/map/MapGlace.jpg",
    "tiles": [ { "id": 0, "x": 0.10, "y": 0.86, "type": "start", "player": "player1" } ],
    "links": [ [2, 4] ],
    "star_zones": [ { "required_tiles": [4, 5, 11, 13] } ],
    "num_stars": 7
}
```

**`windows_data.json`** — Position et dimensions des composants visuels de chaque écran.

#### Schéma de la base de données (Supabase)

Table **`games`** :

| Colonne | Type | Description |
|---|---|---|
| id | int4 | Identifiant auto-incrémenté |
| created_at | timestampz | Horodatage de création |
| host | text | Nom du joueur hôte |
| client | text | Nom du joueur client |
| room_id | int4 | Code de salle à 4 chiffres |
| status | text | État : WAITING, TIMED OUT, STARTED |
| win | text | Nom du vainqueur |

L'authentification (comptes joueurs) est gérée nativement par Supabase Auth.

#### Planning prévisionnel

| Tâche | Responsable | Période |
|---|---|---|
| Conception du projet | Maxime / Louis | Semaine 1 |
| Base de données (Supabase) | Maxime | En parallèle |
| Développement du jeu (Pygame) | Maxime / Louis | Semaines 2–4 |
| Mise en place du multijoueur | Maxime / Louis | Semaines 3–5 |
| Développement du launcher (C#) | Louis | En parallèle |
| Création du site web | Louis | En parallèle |
| Tests et corrections | Maxime / Louis | Au fil du projet |

---

## 3. Méthode générale de résolution

### 3.1 Architecture globale

Le projet est organisé en trois couches distinctes qui communiquent entre elles :

```
[Launcher C#] ──→ [Registre Windows] ──→ [Jeu Pygame]
                                              │
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
                  [Serveur Flask]        [Supabase]          [Fichiers JSON]
                  (Render, API REST)    (Auth + BDD)       (cartes, maps, UI)
```

Le **launcher** vérifie les mises à jour, gère la connexion et stocke le token d'authentification dans le registre Windows. Le **jeu** lit ce token au démarrage pour identifier le joueur sans lui demander de se reconnecter.

### 3.2 Navigation entre les écrans

La navigation est gérée dans `Main.py` par une boucle principale qui reçoit des chaînes de caractères en retour de chaque module (`"mainMenu"`, `"play"`, `"multi"`, `"solo"`, `"leaderboard"`) et instancie l'écran correspondant.

### 3.3 Rendu graphique (Pygame)

Tous les menus sont définis dans `windows_data.json` avec des coordonnées relatives (proportions de l'écran) pour garantir l'adaptabilité à toutes les résolutions. La fenêtre est redimensionnable. La classe `MenuMaker` interprète ces données pour placer et détecter les clics sur les composants.

### 3.4 Multijoueur réseau

Le mode multijoueur repose sur un serveur **Flask** hébergé sur **Render**. Les deux joueurs communiquent via des requêtes HTTP asynchrones à des endpoints REST :
- `POST /create_game` : création d'une nouvelle partie en BDD
- `POST /join_game` : rejoindre une partie existante
- `GET /game_state` / `POST /update_state` : synchronisation de l'état du jeu entre les deux joueurs pendant la partie

### 3.5 Persistance des données

- **Registre Windows** (`HKEY_CURRENT_USER\Software\ToyBattle`) : stockage du token de session, écrit par le launcher et lu par le jeu.
- **Supabase** : comptes utilisateurs (Auth native) et historique des parties (table `games`).
- **Fichiers JSON** : données statiques des cartes et des maps, embarquées dans l'exécutable via PyInstaller.

---

## 4. Détail des parties difficiles ou originales

### 4.1 Multijoueur sans WebSocket

L'une des originalités techniques du projet est d'avoir mis en place un multijoueur réseau en temps réel sans utiliser de WebSocket ni de module `socket`. Le serveur Flask expose une API REST que les clients interrogent en boucle (polling asynchrone). Cette approche présente un léger délai inhérent, mais qui reste imperceptible pour un jeu de plateau au tour par tour, contrairement à un jeu de tir en temps réel.

### 4.2 Plateaux définis par coordonnées relatives

Les maps ne sont pas des grilles fixes : chaque case est définie par ses coordonnées proportionnelles dans l'image (`x`, `y`, `w`, `h` entre 0 et 1). Cela permet d'utiliser n'importe quelle image de plateau artistique tout en conservant un positionnement précis des pions. Un outil `MapMaker.py` a été développé pour créer ces données interactivement.

### 4.3 Zones d'étoiles conditionnelles

La victoire est liée au contrôle de "zones d'étoiles" : des zones du plateau qui ne s'activent que lorsque toutes leurs cases requises sont occupées par le même joueur. Cette logique multi-cases nécessite une vérification continue de l'état de toutes les zones à chaque tour.

### 4.4 Interface graphique pilotée par données (data-driven UI)

Plutôt que de coder les positions de chaque bouton en dur, l'interface est entièrement décrite dans un fichier JSON. Cela permet d'ajouter ou de modifier des écrans sans toucher au code Python, et garantit un rendu correct à toutes les résolutions.

### 4.5 Distribution via PyInstaller et launcher C#

Le jeu est distribué sous forme d'un exécutable `.exe` généré par PyInstaller, incluant toutes les ressources. Le launcher C# vérifie au démarrage si la version locale est à jour par rapport à la dernière release GitHub, et télécharge automatiquement la mise à jour si nécessaire.

---

## 5. Problèmes rencontrés et solutions apportées

### 5.1 Incompatibilité PyGame et serveur Render

**Problème :** Le serveur Flask hébergé sur Render ne peut pas installer Pygame (dépendances graphiques absentes en environnement serveur Linux).

**Solution :** Deux fichiers de dépendances distincts ont été créés : `requirements.txt` pour le jeu (avec Pygame) et `render_requirements.txt` pour le serveur (sans Pygame). Render utilise le second fichier.

### 5.2 Gestion du redimensionnement de la fenêtre

**Problème :** Pygame ne recalcule pas automatiquement les positions et tailles des éléments lors du redimensionnement de la fenêtre.

**Solution :** Un système de layout dynamique a été mis en place : toutes les coordonnées sont stockées comme proportions (flottants entre 0 et 1) et recalculées à chaque redimensionnement via une fonction `update_layout()`.

### 5.3 Latence du polling réseau

**Problème :** L'interrogation périodique du serveur Flask pour synchroniser l'état de la partie introduisait un délai visible.

**Solution :** Les requêtes réseau ont été déplacées dans des threads séparés (`threading`) pour ne pas bloquer le rendu graphique. Le délai reste présent mais n'impacte plus la fluidité de l'affichage.

### 5.4 Embarquement des ressources dans l'exécutable

**Problème :** PyInstaller ne gère pas automatiquement les chemins relatifs aux ressources (images, JSON) une fois l'application compilée.

**Solution :** Une fonction utilitaire `load_path()` a été développée pour résoudre les chemins correctement que l'application soit lancée depuis le code source ou depuis l'exécutable.

---

## 6. Écarts par rapport au cahier des charges

| Fonctionnalité prévue | Réalisée | Commentaire |
|---|:---:|---|
| Jeu Python/Pygame | ✅ | Fonctionnel, avec solo et multijoueur |
| Mode multijoueur réseau | ✅ | Via Flask/Render plutôt que socket brut |
| Launcher C# avec mises à jour | ✅ | Connexion + mise à jour automatique |
| Suivi des actualités dans le launcher | ❌ | Manque de temps |
| Site web avec règles et leaderboard | ✅ | PHP/HTML/CSS/JS, hébergé sur InfinityFree |
| Base de données (comptes + parties) | ✅ | Supabase avec Auth native |
| IA adversaire | ⚠️ | Implémentée mais uniquement aléatoire (pas de deep learning) |
| Multiples plateaux | ✅ | Plusieurs maps disponibles, sélectionnées aléatoirement |
| Rejoindre un salon par nom d'utilisateur | ⚠️ | Remplacé par un code de salle à 4 chiffres |

**Écarts justifiés :**
- Le suivi des actualités dans le launcher a été abandonné au profit de la stabilisation du multijoueur.
- Le code de salle est plus simple et plus robuste qu'une recherche par nom d'utilisateur.
- L'IA aléatoire est fonctionnelle ; une IA avec apprentissage (PyTorch) est identifiée comme amélioration future.

---

## 7. Bilan

### Ce que le projet nous a apporté

**Points positifs :**
- Maîtrise de Pygame et du rendu graphique redimensionnable
- Découverte du déploiement d'une API Flask dans le cloud (Render)
- Utilisation d'une base de données cloud (Supabase) dans un projet réel
- Approfondissement de la notion de projet multi-composants (jeu + serveur + launcher + site web)
- Gestion de fichiers JSON comme source de données de configuration

**Points négatifs / difficultés :**
- La coordination entre plusieurs composants (launcher, jeu, serveur, BDD) a complexifié les tests
- Le polling réseau est un compromis acceptable mais techniquement limité par rapport aux WebSockets
- PyInstaller a généré de nombreuses difficultés lors de la compilation avec les ressources embarquées

---

## 8. Conclusion

Le projet Toy Battle a abouti à un jeu de plateau numérique complet et fonctionnel, jouable en solo contre une intelligence artificielle ou en multijoueur réseau. L'ambition initiale d'aller au-delà du simple jeu Python a été en grande partie tenue : un launcher de mise à jour, un serveur cloud, un site web public et une base de données distante complètent l'expérience.

**Prolongements possibles :**
- Remplacer le polling HTTP par une communication WebSocket (bibliothèque `python-socketio`) pour un multijoueur plus réactif
- Développer une IA basée sur du deep learning (PyTorch/AlphaZero-style) pour un adversaire plus difficile
- Ajouter un éditeur de cartes intégré au jeu
- Proposer un tournoi en ligne avec bracket automatique
- Porter le jeu sur d'autres systèmes d'exploitation (Linux, macOS) via une distribution Python native

Ce projet a représenté un défi technique significatif qui nous a permis d'acquérir une vision concrète du développement logiciel complet, de la conception à la distribution en passant par le déploiement cloud.
