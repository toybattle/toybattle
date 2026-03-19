class Card():
    def __init__(self, name, strengh, capacity, isjoker=False):
        self.name = name
        self.strengh = strengh
        self.capacity = capacity
        self.isjoker = isjoker
        self.is_eat = False

    def can_eat(self, other_card):
        if self.isjoker:
            return True
        if self.strengh > other_card.strengh:
            return True
        return False