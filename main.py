import sys
from gui import PokerGUI


def main():
    """Funkcja główna uruchamiająca GUI."""
    try:
        # Utworzenie i uruchomienie aplikacji GUI
        app = PokerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"Error starting game: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())