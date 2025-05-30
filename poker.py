import random


class Card:
    # Słownik symboli unicode dla kolorów kart
    unicode_dict = {'s': '\u2660', 'h': '\u2665', 'd': '\u2666', 'c': '\u2663'}

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def get_value(self):
        return (self.rank, self.suit)

    def __str__(self):
        return f"{self.rank}{self.unicode_dict[self.suit]}"


class Deck:
    def __init__(self):
        self.cards = []
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['s', 'h', 'd', 'c']

        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(rank, suit))

    def __str__(self):
        return ', '.join(str(card) for card in self.cards)

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, players, cards_per_player=5):
        for _ in range(cards_per_player):
            for player in players:
                if self.cards:
                    player.take_card(self.cards.pop())

    def draw(self):
        if self.cards:
            return self.cards.pop()
        return None

    def discard_to_bottom(self, card):
        self.cards.insert(0, card)


class Player:
    def __init__(self, money, name=""):
        self.__stack = money
        self.__name = name
        self.__hand = []
        self.is_active = True
        self.current_bet = 0

    def take_card(self, card):
        self.__hand.append(card)

    @property
    def stack(self):
        return self.__stack

    @stack.setter
    def stack(self, value):
        self.__stack = max(0, value)

    @property
    def name(self):
        return self.__name

    @property
    def hand(self):
        return self.__hand[:]

    @hand.setter
    def hand(self, new_hand):
        self.__hand = new_hand[:]

    def get_stack_amount(self):
        return self.__stack

    def change_card(self, card, idx):
        if 0 <= idx < len(self.__hand):
            old_card = self.__hand[idx]
            self.__hand[idx] = card
            return old_card
        raise IndexError("Invalid card index")

    def get_player_hand(self):
        return tuple(self.__hand)

    def cards_to_str(self):
        return ', '.join(str(card) for card in self.__hand)

    def bet(self, amount):
        if amount > self.__stack:
            raise ValueError("Insufficient funds")
        self.__stack -= amount
        self.current_bet += amount
        return amount

    def clear_hand(self):
        self.__hand = []
        self.current_bet = 0

    @classmethod
    def create_players(cls, num_players, starting_money=1000):
        """Stworzenie listy graczy: jeden gracz i reszta boty."""
        players = [cls(starting_money, "You")]
        for i in range(num_players - 1):
            players.append(cls(starting_money, f"Bot {i + 1}"))
        return players
