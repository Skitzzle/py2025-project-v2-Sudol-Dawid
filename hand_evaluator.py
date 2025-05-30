from collections import Counter


class HandEvaluator:
    @staticmethod
    def hand_rank(hand):
        """Zwracanie (rangi, wysokich kart) dla podanej ręki pokerowej."""
        if len(hand) != 5:
            return (0, [])

        ranks = [card.rank for card in hand]
        suits = [card.suit for card in hand]

        # Konwertowanie rang na wartości numeryczne do porównania
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                       '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

        values = sorted([rank_values[rank] for rank in ranks], reverse=True)
        rank_counts = Counter(values)
        counts = sorted(rank_counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = (values == list(range(values[0], values[0] - 5, -1)) or
                       values == [14, 5, 4, 3, 2])  # Specjalny przypadek dla A-2-3-4-5

        if is_straight and values == [14, 5, 4, 3, 2]:
            values = [5, 4, 3, 2, 1]  # Strit do asa

        # Poker królewski
        if is_flush and is_straight and values[0] == 14:
            return (9, values)

        # Poker
        if is_flush and is_straight:
            return (8, values)

        # Kareta
        if counts == [4, 1]:
            four_kind = [k for k, v in rank_counts.items() if v == 4][0]
            kicker = [k for k, v in rank_counts.items() if v == 1][0]
            return (7, [four_kind, kicker])

        # Full
        if counts == [3, 2]:
            three_kind = [k for k, v in rank_counts.items() if v == 3][0]
            pair = [k for k, v in rank_counts.items() if v == 2][0]
            return (6, [three_kind, pair])

        # Kolor
        if is_flush:
            return (5, values)

        # Strit
        if is_straight:
            return (4, values)

        # Trójka
        if counts == [3, 1, 1]:
            three_kind = [k for k, v in rank_counts.items() if v == 3][0]
            kickers = sorted([k for k, v in rank_counts.items() if v == 1], reverse=True)
            return (3, [three_kind] + kickers)

        # Dwie pary
        if counts == [2, 2, 1]:
            pairs = sorted([k for k, v in rank_counts.items() if v == 2], reverse=True)
            kicker = [k for k, v in rank_counts.items() if v == 1][0]
            return (2, pairs + [kicker])

        # Para
        if counts == [2, 1, 1, 1]:
            pair = [k for k, v in rank_counts.items() if v == 2][0]
            kickers = sorted([k for k, v in rank_counts.items() if v == 1], reverse=True)
            return (1, [pair] + kickers)

        # Wysoka karta
        return (0, values)

    @staticmethod
    def hand_name(rank):
        """Zwracanie nazwy układu dla danej rangi."""
        names = ["High Card", "One Pair", "Two Pair", "Three of a Kind",
                 "Straight", "Flush", "Full House", "Four of a Kind",
                 "Straight Flush", "Royal Flush"]
        return names[rank] if 0 <= rank < len(names) else "Unknown"

