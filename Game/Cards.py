import json
import random
from Utils import load_path

def init_cards(target_size=20):
    datacards = json.load(open(load_path("data", "datacards.json"), "r", encoding="utf-8"))
    deck = []
    while len(deck) < target_size:
        deck.extend(datacards)
    deck = deck[:target_size]

    random.shuffle(deck)
    pioche_host_cards = deck.copy()
    random.shuffle(pioche_host_cards)

    pioche_client_cards = deck.copy()
    random.shuffle(pioche_client_cards)

    return pioche_host_cards, pioche_client_cards


def draw_initial_cards(deck, count):
    hand = []
    for _ in range(min(count, len(deck))):
        hand.append(deck.pop(0))
    return hand


def host_cards(pioche_host_cards):
    return draw_initial_cards(pioche_host_cards, 3)


def client_cards(pioche_client_cards):
    return draw_initial_cards(pioche_client_cards, 4)
