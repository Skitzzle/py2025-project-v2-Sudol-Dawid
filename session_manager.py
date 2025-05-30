import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple


class SessionManager:
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def save_session(self, session: Dict[str, Any]) -> str:
        """Zapisywanie stanu gry do pliku."""
        try:
            timestamp = datetime.now()
            game_id = f"poker_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            session['game_id'] = game_id
            session['timestamp'] = timestamp.isoformat()
            session['save_date'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            player_summary = [f"{player['name']}: ${player['stack']}" for player in session['players']]
            session['summary'] = f"Players: {len(session['players'])} - " + ", ".join(player_summary)
            filename = os.path.join(self.data_dir, f'session_{game_id}.json')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            return game_id
        except IOError as e:
            raise IOError(f"Failed to save session: {e}")

    def load_session(self, game_id: str) -> Dict[str, Any]:
        """Ładowanie sesji gry z pliku."""
        try:
            filename = os.path.join(self.data_dir, f'session_{game_id}.json')
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Session file not found: {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load session: {e}")

    def list_sessions(self) -> List[Tuple[str, str, str]]:
        """Zwracanie listy dostępnych sesji z metadanymi."""
        sessions = []
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.startswith('session_') and filename.endswith('.json'):
                    try:
                        filepath = os.path.join(self.data_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            game_id = data.get('game_id', filename[8:-5])
                            save_date = data.get('save_date', 'Unknown date')
                            summary = data.get('summary', 'No summary available')
                            sessions.append((game_id, save_date, summary))
                    except:
                        continue
        return sorted(sessions, key=lambda x: x[1], reverse=True)

    def create_session_data(self, game_engine) -> Dict[str, Any]:
        """Stworzenie danych sesji ze stanu silnika gry."""
        return {
            'players': [
                {
                    'name': player.name,
                    'stack': player.stack,
                    'is_active': player.is_active
                }
                for player in game_engine.players
            ],
            'pot': game_engine.pot,
            'current_bet': game_engine.current_bet,
            'dealer_position': game_engine.dealer_position,
            'small_blind': game_engine.small_blind,
            'big_blind': game_engine.big_blind,
            'stage': 'round_end'
        }

    def delete_session(self, game_id: str) -> bool:
        """Usuwanie zapisanej sesji."""
        try:
            filename = os.path.join(self.data_dir, f'session_{game_id}.json')
            if os.path.exists(filename):
                os.remove(filename)
                return True
            return False
        except:
            return False
