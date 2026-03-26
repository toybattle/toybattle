import pygame
import random
import math

# Initialisation de Pygame
pygame.init()

# Constantes
LARGEUR = 800
HAUTEUR = 600
FPS = 60

# Couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)
ORANGE = (255, 165, 0)
JAUNE = (255, 255, 0)

class Particule:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
        # Direction aléatoire (angle en radians)
        angle = random.uniform(0, 2 * math.pi)
        vitesse = random.uniform(2, 8)
        
        self.vx = math.cos(angle) * vitesse
        self.vy = math.sin(angle) * vitesse
        
        # Durée de vie de la particule (en frames)
        self.duree_vie = random.randint(20, 40)
        self.duree_vie_max = self.duree_vie
        
        # Taille et couleur
        self.taille = random.randint(2, 5)
        # Choix aléatoire entre rouge, orange et jaune
        self.couleur = random.choice([ROUGE, ORANGE, JAUNE])
    
    def update(self):
        # Déplacement
        self.x += self.vx
        self.y += self.vy
        
        # Ralentissement (frottement)
        self.vx *= 0.98
        self.vy *= 0.98
        
        # Gravité légère
        self.vy += 0.1
        
        # Réduction de la durée de vie
        self.duree_vie -= 1
    
    def draw(self, screen):
        if self.duree_vie > 0:
            # Plus la particule vieillit, plus elle devient transparente
            alpha = int(255 * (self.duree_vie / self.duree_vie_max))
            
            # Création d'une surface avec transparence
            surface = pygame.Surface((self.taille * 2, self.taille * 2), pygame.SRCALPHA)
            
            # Dessin d'un cercle avec transparence
            couleur_alpha = (*self.couleur, alpha)
            pygame.draw.circle(surface, couleur_alpha[:3], 
                             (self.taille, self.taille), self.taille)
            
            # Ajout de la transparence
            surface.set_alpha(alpha)
            
            # Positionnement sur l'écran
            screen.blit(surface, (int(self.x - self.taille), int(self.y - self.taille)))
    
    def est_vivant(self):
        return self.duree_vie > 0

class SystemeParticules:
    def __init__(self):
        self.particules = []
    
    def create_particles(self, x, y, nombre=30):
        """Crée une explosion de particules à la position (x, y)"""
        for _ in range(nombre):
            self.particules.append(Particule(x, y))
    
    def update(self):
        # Met à jour toutes les particules
        for particule in self.particules:
            particule.update()
        
        # Supprime les particules mortes
        self.particules = [p for p in self.particules if p.est_vivant()]
    
    def draw(self, screen):
        for particule in self.particules:
            particule.draw(screen)

# def main():
#     # Configuration de l'écran
#     screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
#     pygame.display.set_caption("Effet de particules - Clic pour exploser !")
#     clock = pygame.time.Clock()
    
#     # Création du système de particules
#     systeme_particules = SystemeParticules()
    
#     # Police pour le texte
#     font = pygame.font.Font(None, 36)
    
#     running = True
    
#     while running:
#         # Gestion des événements
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False
            
#             elif event.type == pygame.MOUSEBUTTONDOWN:
#                 if event.button == 1:  # Clic gauche
#                     x, y = pygame.mouse.get_pos()
#                     # Crée une explosion à la position du curseur
#                     systeme_particules.create_particles(x, y, nombre=40)
        
#         # Mise à jour
#         systeme_particules.update()
        
#         # Dessin
#         screen.fill(NOIR)
        
#         # Dessine le système de particules
#         systeme_particules.draw(screen)
        
#         # Affiche le nombre de particules
#         texte = font.render(f"Particules: {len(systeme_particules.particules)}", 
#                           True, BLANC)
#         screen.blit(texte, (10, 10))
        
#         # Instructions
#         texte_instructions = font.render("Cliquez n'importe où pour une explosion !", 
#                                         True, BLANC)
#         screen.blit(texte_instructions, (10, HAUTEUR - 40))
        
#         pygame.display.flip()
#         clock.tick(FPS)
    
#     pygame.quit()

# if __name__ == "__main__":
#     main()
