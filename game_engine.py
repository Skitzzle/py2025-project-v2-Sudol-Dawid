from typing import List
from poker import Player, Deck, Card
from hand_evaluator import HandEvaluator
import random


class InvalidActionError(Exception):
    """Błąd nieprawidłowej akcji"""
    pass


class InsufficientFundsError(Exception):
    """Błąd niewystarczających środków"""
    pass


class GameEngine:
    def __init__(self, players: List[Player], deck: Deck = None,
                 small_blind: int = 25, big_blind: int = 50):
        self.players = players
        self.deck = deck or Deck()
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.pot = 0
        self.current_bet = 0
        self.dealer_position = 0
        self.game_over = False

    def play_round(self) -> None:
        """Przeprowadzanie jednej rundy gry."""
        players_with_chips = [p for p in self.players if p.stack > 0]
        if len(players_with_chips) < 2:
            self.game_over = True
            if len(players_with_chips) == 1:
                winner = players_with_chips[0]
                total_chips = sum(p.stack for p in self.players) + self.pot
                for player in self.players:
                    if player != winner:
                        player.stack = 0
                winner.stack = total_chips
                self.pot = 0
                return [("final_winner", winner, total_chips)]
            return None
        self.pot = 0
        self.current_bet = 0
        self.deck = Deck()
        for player in self.players:
            player.current_bet = 0
            player.clear_hand()
            player.is_active = player.stack > 0
        for _ in range(3):
            self.deck.shuffle()
        self._collect_blinds()
        self._deal_cards()
        self._betting_round()
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) <= 1:
            final_pot = self.pot
            winners = [(active_players[0], "Win by fold", None, final_pot, self._get_all_player_hands(), False)]
            active_players[0].stack += self.pot
            self.pot = 0
            return winners
        self._exchange_phase()
        self.current_bet = 0
        for player in self.players:
            player.current_bet = 0
        self._betting_round()
        winners = self._showdown()
        self._move_dealer_button()
        return winners

    def _deal_cards(self):
        """Rozdanie kart tylko graczom z żetonami."""
        active_players = [p for p in self.players if p.stack > 0]
        self.deck.deal(active_players, 5)

    def _move_dealer_button(self):
        """Przesuwanie przycisku rozdającego do następnego gracza z żetonami."""
        original_position = self.dealer_position
        while True:
            self.dealer_position = (self.dealer_position + 1) % len(self.players)
            if self.players[self.dealer_position].stack > 0:
                break
            if self.dealer_position == original_position:
                break

    def _collect_blinds(self):
        """Pobieranie blindów od graczy."""
        active_players = [p for p in self.players if p.stack > 0]
        if len(active_players) < 2:
            return
        sb_pos = self.dealer_position
        while True:
            sb_pos = (sb_pos + 1) % len(self.players)
            if self.players[sb_pos].stack > 0:
                break
        sb_player = self.players[sb_pos]
        sb_amount = min(self.small_blind, sb_player.stack)
        sb_player.bet(sb_amount)
        self.pot += sb_amount
        bb_pos = sb_pos
        while True:
            bb_pos = (bb_pos + 1) % len(self.players)
            if self.players[bb_pos].stack > 0:
                break
        bb_player = self.players[bb_pos]
        bb_amount = min(self.big_blind, bb_player.stack)
        bb_player.bet(bb_amount)
        self.pot += bb_amount
        self.current_bet = bb_amount

    def _betting_round(self):
        """Przeprowadzanie rundy zakładów."""
        active_players = [p for p in self.players if p.is_active and p.stack > 0]
        if len(active_players) <= 1:
            return
        current_pos = self.dealer_position
        while True:
            current_pos = (current_pos + 1) % len(self.players)
            if self.players[current_pos].stack > 0:
                break
        players_to_act = {p: True for p in active_players}
        last_raiser = None
        max_rounds = len(self.players) * 4
        round_count = 0
        while round_count < max_rounds:
            player = self.players[current_pos]
            if player.is_active and player.stack > 0 and players_to_act[player]:
                action = self.prompt_bet(player, self.current_bet)
                if action == "fold":
                    player.is_active = False
                    players_to_act.pop(player)
                    if len(players_to_act) <= 1:
                        break
                elif action == "call" or action == "check":
                    call_amount = max(0, self.current_bet - player.current_bet)
                    if call_amount > 0:
                        bet_amount = min(call_amount, player.stack)
                        player.bet(bet_amount)
                        self.pot += bet_amount
                    players_to_act[player] = False
                elif action.startswith("raise"):
                    try:
                        raise_amount = int(action.split()[1])
                        total_bet = self.current_bet + raise_amount
                        bet_needed = total_bet - player.current_bet
                        if bet_needed > player.stack:
                            raise InsufficientFundsError("Not enough chips")
                        player.bet(bet_needed)
                        self.pot += bet_needed
                        self.current_bet = total_bet
                        last_raiser = player
                        for p in players_to_act:
                            if p != player and p.is_active and p.stack > 0:
                                players_to_act[p] = True
                        players_to_act[player] = False
                    except (ValueError, InsufficientFundsError):
                        continue
            while True:
                current_pos = (current_pos + 1) % len(self.players)
                if self.players[current_pos].stack > 0 or current_pos == self.dealer_position:
                    break
            round_count += 1
            if all(not needed_to_act for needed_to_act in players_to_act.values()):
                break
            active_players = [p for p in self.players if p.is_active]
            if len(active_players) <= 1:
                break
            if all(not p.is_active or p.current_bet == self.current_bet or p.stack == 0 
                  for p in self.players if p in players_to_act):
                break

    def prompt_bet(self, player: Player, current_bet: int) -> str:
        """Pobieranie akcji od gracza."""
        if player.name == "You":
            return self._get_human_action(player, current_bet)
        else:
            return self._get_bot_action(player, current_bet)

    def _get_human_action(self, player: Player, current_bet: int) -> str:
        """Zwracanie akcji gracza (GUI lub prosta logika)."""
        call_amount = max(0, current_bet - player.current_bet)
        if call_amount == 0:
            return "check"
        elif call_amount >= player.stack:
            return "call"
        else:
            if random.random() < 0.7:
                return "call"
            else:
                return "fold"

    def _get_bot_action(self, player: Player, current_bet: int) -> str:
        """Stosowanie prostej logiki bota."""
        call_amount = max(0, current_bet - player.current_bet)
        if call_amount == 0:
            if random.random() < 0.8:
                return "check"
            else:
                return f"raise {self.big_blind}"
        elif call_amount >= player.stack:
            if random.random() < 0.3:
                return "call"
            else:
                return "fold"
        else:
            action_choice = random.random()
            if action_choice < 0.5:
                return "call"
            elif action_choice < 0.8:
                return "fold"
            else:
                return f"raise {self.big_blind}"

    def _exchange_phase(self):
        """Przeprowadzanie fazy wymiany kart."""
        for player in self.players:
            if player.is_active:
                if player.name == "You":
                    indices = self._get_human_exchange()
                else:
                    indices = self._get_bot_exchange()
                if indices:
                    new_hand = self.exchange_cards(player.hand, indices)
                    player.hand = new_hand
        self.deck.cards = [card for card in self.deck.cards if card is not None]

    def _get_human_exchange(self) -> List[int]:
        """Zwracanie indeksów kart do wymiany (GUI lub losowo)."""
        num_cards = random.randint(0, 3)
        if num_cards == 0:
            return []
        return random.sample(range(5), num_cards)

    def _get_bot_exchange(self) -> List[int]:
        """Stosowanie prostej logiki wymiany kart bota."""
        num_cards = random.randint(0, 3)
        if num_cards == 0:
            return []
        return random.sample(range(5), num_cards)

    def exchange_cards(self, hand: List[Card], indices: List[int]) -> List[Card]:
        """Wymienianie wskazanych kart."""
        if not indices:
            return hand
        if not all(0 <= idx <= 4 for idx in indices):
            raise IndexError("Card index must be between 0 and 4")
        new_hand = hand[:]
        old_cards = []
        new_cards = []
        for _ in indices:
            new_card = self.deck.draw()
            if new_card:
                new_cards.append(new_card)
        if len(new_cards) == len(indices):
            for i, idx in enumerate(indices):
                old_card = new_hand[idx]
                if old_card:
                    old_cards.append(old_card)
                new_hand[idx] = new_cards[i]
            for old_card in old_cards:
                if old_card:
                    self.deck.discard_to_bottom(old_card)
        return new_hand

    def _showdown(self):
        """Porównywanie układów i przyznawanie puli."""
        active_players = [p for p in self.players if p.is_active]
        final_pot = self.pot
        if len(active_players) <= 1:
            winner = active_players[0]
            winner.stack += self.pot
            self.pot = 0
            return [(winner, None, None, final_pot, self._get_all_player_hands(), False)]
        player_hands = []
        for player in active_players:
            rank, high_cards = HandEvaluator.hand_rank(player.hand)
            hand_name = HandEvaluator.hand_name(rank)
            player_hands.append((player, rank, high_cards, hand_name))
        player_hands.sort(key=lambda x: (x[1], x[2]), reverse=True)
        best_rank = player_hands[0][1]
        best_high_cards = player_hands[0][2]
        winners = [(ph[0], ph[3], ph[2]) for ph in player_hands
                  if ph[1] == best_rank and ph[2] == best_high_cards]
        is_draw = len(winners) > 1
        if is_draw:
            return [(w[0], w[1], w[2], final_pot, self._get_all_player_hands(), True) for w in winners]
        winner = winners[0][0]
        winner.stack += self.pot
        self.pot = 0
        return [(winners[0][0], winners[0][1], winners[0][2], final_pot, self._get_all_player_hands(), False)]

    def handle_draw_resolution(self, choice: str):
        """Obsługiwanie rozstrzygania remisu."""
        active_players = [p for p in self.players if p.is_active]
        if choice == "split":
            pot_share = self.pot // len(active_players)
            remainder = self.pot % len(active_players)
            for player in active_players:
                player.stack += pot_share
            if remainder > 0:
                random.choice(active_players).stack += remainder
            total_after = sum(p.stack for p in self.players)
            expected_total = sum(p.stack for p in self.players) + self.pot
            if total_after != expected_total:
                discrepancy = expected_total - total_after
                if discrepancy > 0:
                    random.choice(active_players).stack += discrepancy
            self.pot = 0
            return "split"
        elif choice == "continue":
            self.current_bet = 0
            for player in self.players:
                player.current_bet = 0
            self._betting_round()
            if len([p for p in self.players if p.is_active]) > 1:
                return self.handle_draw_resolution("split")
            else:
                winner = next(p for p in self.players if p.is_active)
                winner.stack += self.pot
                self.pot = 0
                return "winner"
        return None

    def verify_total_chips(self):
        """Sprawdzanie, czy suma żetonów w grze pozostaje stała."""
        total_chips = sum(p.stack for p in self.players) + self.pot
        return total_chips

    def _get_all_player_hands(self):
        """Zwracanie listy krotek z rękami graczy i ich statusem."""
        all_hands = []
        for player in self.players:
            status = "Active" if player.is_active else "Folded"
            if player.stack == 0:
                status = "Out"
            if player.hand:
                hand_name = None
                if player.is_active:
                    rank, high_cards = HandEvaluator.hand_rank(player.hand)
                    hand_name = HandEvaluator.hand_name(rank)
                all_hands.append({
                    'player_name': player.name,
                    'hand': player.hand,
                    'status': status,
                    'hand_name': hand_name
                })
        return all_hands

    def showdown(self) -> Player:
        """Zwracanie zwycięzcy w showdownie."""
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) == 1:
            return active_players[0]
        best_player = None
        best_rank = -1
        best_high_cards = []
        for player in active_players:
            rank, high_cards = HandEvaluator.hand_rank(player.hand)
            if rank > best_rank or (rank == best_rank and high_cards > best_high_cards):
                best_player = player
                best_rank = rank
                best_high_cards = high_cards
        return best_player

    def check_game_over(self) -> bool:
        """Sprawdzanie, czy gra powinna się zakończyć i obsłużenie końcowego zwycięzcy."""
        players_with_chips = [p for p in self.players if p.stack > 0]
        if len(players_with_chips) < 2:
            self.game_over = True
            return True
        return False

