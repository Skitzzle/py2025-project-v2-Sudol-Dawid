import random
from typing import List


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

from typing import List


class GameEngine:
    def __init__(self, players: List[Player], deck: Deck,
                 small_blind: int = 25, big_blind: int = 50):
        self.players = players
        self.deck = deck
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.pot = 0
        self.current_bet = 0

    def play_round(self) -> None:
        self.pot = 0
        if len(self.players) < 2:
            print("Za mało graczy.")
            return
        self.players[0]._Player__stack_ -= self.small_blind
        self.players[1]._Player__stack_ -= self.big_blind
        self.pot += self.small_blind + self.big_blind
        self.current_bet = self.big_blind

        self.deck.shuffle()
        self.deck.deal(self.players)
        for player in self.players:
            print(f"{player._Player__name_} karty: {player.cards_to_str()}")

        for player in self.players:
            try:
                action = self.prompt_bet(player, self.current_bet)
                print(f"{player._Player__name_} akcja: {action}")
            except Exception as e:
                print(f"Błąd akcji: {e}")

        for player in self.players:
            try:
                indices = input(f"{player._Player__name_}, które karty wymienić (np. 0 2 4)? ").split()
                indices = list(map(int, indices))
                player._Player__hand_ = self.exchange_cards(player._Player__hand_, indices)
                print("Nowa ręka:", player.cards_to_str())
            except (ValueError, IndexError):
                print("Niepoprawne indeksy – pominięto wymianę.")

        winner = self.showdown()
        winner._Player__stack_ += self.pot
        print(f"Zwycięzca: {winner._Player__name_}, otrzymuje {self.pot} żetonów.")

    def prompt_bet(self, player: Player, current_bet: int) -> str:
        action = input(f"{player._Player__name_}, akcja (check/call/raise/fold): ").strip().lower()

        if action not in ['check', 'call', 'raise', 'fold']:
            raise ValueError("Nieprawidłowa akcja.")

        if action == 'call':
            call_amount = self.current_bet
            if player._Player__stack_ >= call_amount:
                player._Player__stack_ -= call_amount
                self.pot += call_amount
            else:
                raise ValueError("Za mało żetonów na call.")
        elif action == 'raise':
            try:
                raise_amount = int(input("Podaj kwotę podbicia (musi być większa niż obecny zakład): "))
                if raise_amount <= self.current_bet:
                    raise ValueError("Kwota musi być większa niż obecny zakład.")
                if player._Player__stack_ >= raise_amount:
                    player._Player__stack_ -= raise_amount
                    self.current_bet = raise_amount
                    self.pot += raise_amount
                else:
                    raise ValueError("Za mało żetonów na raise.")
            except ValueError:
                raise ValueError("Nieprawidłowa kwota raise.")
        elif action == 'check':
            if self.current_bet > 0:
                raise ValueError("Nie możesz zrobić check przy aktywnym zakładzie (użyj call lub fold).")
        elif action == 'fold':
            # prosta wersja - gracz pasuje, ale w tym silniku to nie kończy gry
            print(f"{player._Player__name_} spasował – (brak pełnej obsługi fold w tej wersji).")

        return action

    def exchange_cards(self, hand: List[Card], indices: List[int]) -> List[Card]:
        if any(idx < 0 or idx >= 5 for idx in indices):
            raise IndexError("Indeks spoza zakresu 0–4.")
        new_cards = [self.deck.cards.pop(0) for _ in indices]
        for i, idx in enumerate(indices):
            self.deck.cards.append(hand[idx])  # stara karta na spód
            hand[idx] = new_cards[i]
        return hand

    def showdown(self) -> Player:
        rank_order = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                      '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        best_player = self.players[0]
        best_value = max(rank_order[card.rank] for card in best_player._Player__hand_)

        for player in self.players[1:]:
            player_max = max(rank_order[card.rank] for card in player._Player__hand_)
            if player_max > best_value:
                best_value = player_max
                best_player = player

        return best_player

def main():
    print("Witamy w prostej grze pokerowej!")

    name1 = input("Podaj nazwę gracza 1: ")
    name2 = input("Podaj nazwę gracza 2: ")

    player1 = Player(money=500, name=name1)
    player2 = Player(money=500, name=name2)

    deck = Deck()
    game = GameEngine(players=[player1, player2], deck=deck)

    while True:
        print("\n--- Nowa runda ---")
        game.play_round()

        for player in game.players:
            print(f"{player.__name_} ma teraz {player.get_stack_amount()} żetonów.")

        cont = input("Czy chcesz zagrać kolejną rundę? (t/n): ").strip().lower()
        if cont != 't':
            print("Koniec gry!")
            break

if __name__ == "__main__":
    main()
