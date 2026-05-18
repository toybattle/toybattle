Tableau de DB
Structure/architecture du projet


Le contenu indicatif peut être :
➢ Un sommaire,
➢ Une introduction,
➢ Rappel des spécifications et de la conception détaillée,
➢ Méthode générale de résolution,
➢ Détail éventuel des parties difficiles ou originales,
➢ Problèmes rencontrés et solutions apportées,
➢ Les écarts par rapport au cahier des charges,
➢ Bilan : ce que le projet vous a apporté (les +, les -),
➢ Conclusion : Discussion des résultats, prolongements possibles, améliorations, ...
Le code commenté sera également à déposer au format numérique sur ENT. Il devra
être compressé (format .zip), et devra contenir tout ce qui est nécessaire pour que votre
enseignant.e puisse l’exécuter. 

# Projet 7 : Toybattle

## Sommaire

## Comparaison objectifs et réalisation:

### Jeu, launcher et site web :

- ✅ Un jeu développé en Python avec la bibliothèque Pygame

- Un launcher en C# (WPF) permettant :
  - ✅ La mise à jour du jeu
  - ❌ Le suivi des actualités

- Un site web permettant :
  - ✅ D’expliquer les règles du jeu
  - ✅ D’afficher un leaderboard (classement des joueurs)

#### → Réalisation
- Un launcher en C# (WPF) permettant de se connecter ou créer un compte
- Gestion automatique de la mise a jours du jeu et téléchargement si jeu non existant.
- Site web codé en php, html, css, javascript, et postgress sql pour la base de donner lier a supabase permetant d'afficher le leaderboard ansi que le nombre de parties jouées et le nombre de joueurs.

##### URL du site web: https://toybattle.rf.gd/, hébergé chez: https://www.infinityfree.com/

---

### Base de données 

- Une base de données SQL distante (Supabase) pour :
  - ✅ Stocker les comptes joueurs
  - ✅ Enregistrer les parties et statistiques

#### → Réalisation:

- Base de données hebergée chez supabase
- Utilisation de l'authentification native fournie par supabase (via librairie)

#### Schéma de base de donnée

#### `games`

| Colonne | Type | Description |
|---|---|---|
| id | int4 | Id de partie auto-incrémenté |
| created_at | timestampz | Moment où la partie a été créée |
| host | text | Username de l'utilisateur qui a créé la partie |
| client | text | Username de l'utilisateur qui a rejoint la partie |
| room_id | int4 | Id de 4 chiffre générée aléatoirement dans le code |
| status | text | Status de la partie (WAITING, TIMED OUT ou STARTED) |
| win | text | Username du vainqueur |e le client a rejoint une partie, 

---
  
### Mode Multijoueur
- ➡️ Un mode multijoueur utilisant *socket* 
  - Hébergement envisagé : Render ou Koyeb

→ Réalisation:

- Un mode multijoueur utilisant `Flask` (utilisation pour sa facilité à créer un serveur avec lequel on peux communiquer via API hebergée sur Render)<br>
###### Limite: Contrairement à `socket` qui permet de faire du realtime grâce au flux qu'il ouvre, flask est un serveur api. Il faut donc utiliser des requêtes asyncrones créant un léger retard qui n'est cependant, dans notre cas contrairement à un jeu de tir, pas très impactant. Le gain de temps à sa mise en place (déjà utilisé dans d'anciens projets personnels) a été priviligé à l'utilisation d'une nouvelle bibliothèque.

---

### Utilisation de fichiers

- Utilisation de fichiers JSON pour :
  - ✅ Stocker les cartes des personnages
  - ✅ Définir les maps (Nom, image et coordonnées des cases)
  
→ Réalisation:

- Fichiers JSON:
    - `datacards.json` (contenant la structure de chaque carte):
    ```
    {
        "id": 1,
        "name": "Skully",
        "image_path": "Skully.png",
        "strength": 1,
        "ability_desc": "Piocher 2 cartes"
    }
    ```
    
    - `map_data.json` (contenant les caractéristques de chaque map):
    ```
    "MapGlace": {
        "image_path": "assets/map/MapGlace.jpg",
        "tiles": [
            {
                "id": 0,
                "x": 0.10946745562130178,
                "y": 0.8696428571428572,
                "w": 0.14792899408284022,
                "h": 0.07857142857142851,
                "type": "start",
                "player": "player1"
            }
        ],
        "links": [
            [
                2,
                4
            ]
        ],
        "star_zones": [
            {
                "required_tiles": [
                    4,
                    5,
                    11,
                    13
                ],
                "area": {
                    "x": 0.3391304347826087,
                    "y": 0.4276315789473684,
                    "w": 0.07173913043478264,
                    "h": 0.20526315789473687
                }
            },
        ],
        "num_stars": 7
    }
    ```

    - `windows_data.json` (contenant les informations pour le placement et l'intéraction des composants visuels):
    ```
     {
        "name": "MainMenu",
        "image_path": "assets/MainMenu.jpg",
        "tiles": [
            {
                "id": "play",
                "x": 0.3655555555555556,
                "y": 0.42,
                "width": 0.29333333333333333,
                "height": 0.15
            }
        ]
    }
    ```

- Conversion en .exe via la library pyinstaller

-> Réalisation:

- Utilisation de pyinsaller pour cree lee .exe

    ```
    pyinstaller --onefile --name "ToyBattle" --add-data "Menu;Menu" --add-data "Game;Game" --add-data "assets;assets" Menu\main.py
    ```
---

- Utilisation d'un fichier requirements.txt pour gérer les libraires nécessaires

-> Réalisation:

- 2 fichier requirements on était utilsier 1 pour le jeu téléchargent les libréries 
    - requirements.txt utiliser pour le jeu
    - render_requirements.txt dédier au server Render car ne support pas pygame

---

- Utilisation de l'éditeur de registre pour stocker les données de connexion de l'utilisateur (pour éviter la reconnexion à chaque lancement)

-> Réalisation:
- Donner sauvgarder sous: Software\ToyBattle en HKEY_CURRENT_USER ce qui ne sessesite pas de lancer le jeu ni le launcher en version administarteur
- Le launcher vas enregister les donner dans le registre
- le jeu vas lire les donnés

- Connexion / inscription des joueurs

-> Réalisation: 

- Comme sité précédament dans []()

--- 

- Sauvegarde de l’authentification (registre système)

-> Réalisation: 

- Comme sité précédament dans []()

--- 

- Création d’un salon multijoueur

-> Réalisation:

- Fichier Room.py qui gère la version multi jpoueur et solo
    - Celui qui lance une partie click sur Server, cela fais un apppelle a l'endpoint /create_game qui vas inserrer une nouvelle ligen dans la base de donner.
    - Celui qui rejoint la partie, devars metre dans l'input number l'id de la room et cela fais appelle a l'endpoint /join_game qui initialiseras la partie
    - Le bouton solo lancera une parti contre le robot et ne seras pas s'auvgarder dans la base de donner

--- 

- Rejoindre un salon via un nom d'utilisateur

-> Réalisation:

- Remplacement du nom d'utilisateur par l'id de la room

---

- Choix du mode de jeu 

-> Réalisation:

- Les deux fonctionnliter on était mise en place. Pour l'ia uniqment de l'aléatoire a était utiliser. Une versaion avec PyTorch pour metre en place du deep learing est a prévoir. Améliorant considérablement l'ia

---

- Attribution aléatoire

-> Réalisation:

- Celaui qui host la parti seras toujours celui qui commance
- pour la map un random a était utiliser