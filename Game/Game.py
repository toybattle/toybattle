import json
import random

datacards = json.load(open("datacards.json", "r"))

list_cards = []
for card in datacards:
    list_cards.append(card)

pioche_host_cards = list_cards.copy()*3
random.shuffle(pioche_host_cards)

pioche_client_cards = list_cards.copy()*3
random.shuffle(pioche_client_cards)

host_cards = []

for cardindex in range(3):
    host_cards.append(pioche_host_cards[cardindex - 1])
    pioche_host_cards.remove(pioche_host_cards[cardindex - 1])

client_cards = []

for cardindex in range(4):
    client_cards.append(pioche_client_cards[cardindex - 1])
    pioche_client_cards.remove(pioche_client_cards[cardindex - 1])


import pygame
import sys
import json

pygame.init()

# Dimensions de la fenêtre
WIDTH = 1000
HEIGHT = 800

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Carte du menu")

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
    for card in host_cards:
        img = pygame.image.load(card["image_path"])
        screen.blit(img, (100, 100 + host_cards.index(card) * 100))

    for card in client_cards:
        img = pygame.image.load(card["image_path"])
        screen.blit(img, (400, 100 + client_cards.index(card) * 100))

    pygame.display.flip()
    clock.tick(60)