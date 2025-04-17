import random


class Card:
    # słownik symboli unicode
    unicode_dict = {'s': '\u2660', 'h': '\u2665', 'd': '\u2666', 'c': '\u2663'}

    def __init__(self, rank, suit):
        # definicja konstruktora, ma ustawiać pola rangi i koloru
        self.rank = rank
        self.suit = suit

    def get_value(self):
        # definicja metody (ma zwracać kartę w takiej reprezentacji, jak dotychczas, tzn. krotka)
        return (self.rank, self.suit)

    def __str__(self):
        # definicja metody, przydatne do wypisywania karty
        return f"{self.rank}{self.unicode_dict[self.suit]}"


class Deck:

    def __init__(self, *args):
        # definicja metody, ma tworzyć niepotasowaną talię (jak na poprzednich lab)
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['s', 'h', 'd', 'c']
        self.cards = [Card(rank, suit) for suit in suits for rank in ranks]

    def __str__(self):
        # definicja metody, przydatne do wypisywania talii
        return ", ".join(str(card) for card in self.cards)

    def shuffle(self):
        # definicja metody, tasowanie
        random.shuffle(self.cards)

    def deal(self, players):
        # definicja metody, otrzymuje listę graczy i rozdaje im karty wywołując na nich metodę take_card z Player
        if not players or len(self.cards) < 5 * len(players):
            return
        for player in players:
            for _ in range(5):
                if self.cards:
                    player.take_card(self.cards.pop(0))


class Player:

    def __init__(self, money, name=""):
        self.__stack_ = money
        self.__name_ = name
        self.__hand_ = []

    def take_card(self, card):
        self.__hand_.append(card)

    def get_stack_amount(self):
        return self.__stack_

    def change_card(self, card, idx):
        # przyjmuje nową kartę, wstawia ją za kartę o indeksie idx, zwraca kartę wymienioną
        if 0 <= idx < len(self.__hand_):
            old_card = self.__hand_[idx]
            self.__hand_[idx] = card
            return old_card
        return None

    def get_player_hand(self):
        return tuple(self.__hand_)

    def cards_to_str(self):
        # definicja metody, zwraca stringa z kartami gracza
        return ", ".join(str(card) for card in self.__hand_)