# Five Card Draw Poker (py2025-project-v2)

## Opis projektu
Aplikacja symuluje rozgrywkę w pokera pięciokartowego dobieranego z graficznym interfejsem użytkownika (GUI). Pozwala na grę z botami, wymianę kart, licytację, zapisywanie i wczytywanie stanu gry oraz przeglądanie historii rozgrywek.

## Główne funkcjonalności
- Gra w pokera pięciokartowego z botami
- Interfejs graficzny (Tkinter): obsługa rozgrywki, wymiany kart, licytacji
- Zapisywanie i wczytywanie stanu gry (JSON)
- Przeglądanie historii i usuwanie zapisanych gier
- Prosta logika botów
- Ocena układów pokerowych (hand ranking)

## Wymagane biblioteki
- Python 3.8+
- Tkinter (standardowa biblioteka Pythona)

Nie są wymagane dodatkowe zewnętrzne biblioteki.

## Uruchamianie aplikacji
1. Upewnij się, że masz zainstalowanego Pythona (3.8 lub nowszy).
2. Uruchom aplikację poleceniem:

    python main.py

3. Po uruchomieniu pojawi się okno GUI, w którym można rozpocząć nową grę, zapisać/wczytać stan gry lub przeglądać historię.

## Zasady działania
- Gra rozpoczyna się od wyboru liczby graczy (2-6, jeden gracz to użytkownik, reszta to boty).
- Każdy gracz otrzymuje 5 kart, następnie odbywa się licytacja, wymiana kart i kolejna licytacja.
- Wygrywa gracz z najlepszym układem lub ostatni aktywny w rozdaniu.
- Stan gry można zapisać i wczytać w dowolnym momencie.

## Struktura projektu
- `main.py` – uruchamianie aplikacji
- `gui.py` – interfejs graficzny
- `game_engine.py` – logika rozgrywki
- `poker.py` – klasy Card, Deck, Player
- `hand_evaluator.py` – ocena układów pokerowych
- `session_manager.py` – zapisywanie/wczytywanie gier
- `data/` – katalog z zapisanymi stanami gier
