import json
import random


def init_cards():
    datacards = json.load(open("data/datacards.json", "r"))

    list_cards = []
    for card in datacards:
        list_cards.append(card)

    pioche_host_cards = list_cards.copy()*3
    random.shuffle(pioche_host_cards)

    pioche_client_cards = list_cards.copy()*3
    random.shuffle(pioche_client_cards)
    
    return pioche_host_cards, pioche_client_cards
    
def host_cards(pioche_host_cards):
    host_cards = []

    for cardindex in range(3):
        host_cards.append(pioche_host_cards[cardindex - 1])
        pioche_host_cards.remove(pioche_host_cards[cardindex - 1])

    return host_cards

def client_cards(pioche_client_cards):
    client_cards = []

    for cardindex in range(4):
        client_cards.append(pioche_client_cards[cardindex - 1])
        pioche_client_cards.remove(pioche_client_cards[cardindex - 1])

    return client_cards
