import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Optional
import threading
import time

from poker import Player, Deck
from game_engine import GameEngine
from session_manager import SessionManager


class PokerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Five Card Draw Poker")
        self.root.geometry("1000x700")

        self.game_engine: Optional[GameEngine] = None
        self.session_manager = SessionManager()
        self.human_player: Optional[Player] = None
        self.waiting_for_action = False
        self.human_action = None
        self.exchange_indices = []
        self.is_game_running = False
        self.update_scheduled = False

        self.setup_gui()

    def setup_gui(self):
        """Inicjalizacja głównych komponentów GUI"""
        # Pasek menu
        self.create_menu()

        # Główna ramka
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ramka z informacjami o grze
        self.create_game_info_frame(main_frame)

        # Ramka graczy
        self.create_players_frame(main_frame)

        # Ramka kart gracza
        self.create_cards_frame(main_frame)

        # Ramka przycisków akcji
        self.create_action_frame(main_frame)

        # Log gry
        self.create_log_frame(main_frame)

    def create_menu(self):
        """Tworzy pasek menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu gry
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_command(label="Save Game", command=self.save_game)
        game_menu.add_command(label="Load Game", command=self.show_load_dialog)
        game_menu.add_command(label="Delete Saved Game", command=self.show_delete_dialog)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit)

    def create_game_info_frame(self, parent):
        """Tworzy wyświetlanie informacji o grze"""
        info_frame = ttk.LabelFrame(parent, text="Game Info")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # Pula i stan gry
        self.pot_label = ttk.Label(info_frame, text="Pot: $0", font=("Arial", 12, "bold"))
        self.pot_label.pack(side=tk.LEFT, padx=10)

        self.phase_label = ttk.Label(info_frame, text="Phase: Waiting", font=("Arial", 12))
        self.phase_label.pack(side=tk.LEFT, padx=20)

        self.current_bet_label = ttk.Label(info_frame, text="Current bet: $0")
        self.current_bet_label.pack(side=tk.LEFT, padx=20)

    def create_players_frame(self, parent):
        """Tworzy wyświetlanie graczy"""
        players_frame = ttk.LabelFrame(parent, text="Players")
        players_frame.pack(fill=tk.X, pady=(0, 10))

        self.players_frame = players_frame
        self.player_labels = []

    def create_cards_frame(self, parent):
        """Tworzy wyświetlanie kart gracza"""
        cards_frame = ttk.LabelFrame(parent, text="Your Cards")
        cards_frame.pack(fill=tk.X, pady=(0, 10))

        self.cards_frame = ttk.Frame(cards_frame)
        self.cards_frame.pack(pady=10)

        self.card_buttons = []
        self.card_selected = [False] * 5

        for i in range(5):
            btn = tk.Button(self.cards_frame, text="[?]", width=8, height=4,
                            command=lambda idx=i: self.toggle_card_selection(idx))
            btn.pack(side=tk.LEFT, padx=5)
            self.card_buttons.append(btn)

    def create_action_frame(self, parent):
        """Tworzy przyciski akcji"""
        action_frame = ttk.LabelFrame(parent, text="Actions")
        action_frame.pack(fill=tk.X, pady=(0, 10))

        # Akcje licytacji
        betting_frame = ttk.Frame(action_frame)
        betting_frame.pack(pady=5)

        self.check_call_btn = ttk.Button(betting_frame, text="Check/Call",
                                         command=self.check_call_action)
        self.check_call_btn.pack(side=tk.LEFT, padx=5)

        self.raise_btn = ttk.Button(betting_frame, text="Raise",
                                    command=self.raise_action)
        self.raise_btn.pack(side=tk.LEFT, padx=5)

        self.raise_entry = ttk.Entry(betting_frame, width=10)
        self.raise_entry.pack(side=tk.LEFT, padx=5)

        self.fold_btn = ttk.Button(betting_frame, text="Fold",
                                   command=self.fold_action)
        self.fold_btn.pack(side=tk.LEFT, padx=5)

        # Akcja wymiany
        self.exchange_btn = ttk.Button(action_frame, text="Exchange Selected Cards",
                                       command=self.exchange_action)
        self.exchange_btn.pack(pady=5)

        self.disable_action_buttons()

    def create_log_frame(self, parent):
        """Tworzy log gry"""
        log_frame = ttk.LabelFrame(parent, text="Game History")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Konfiguracja tagów tekstowych dla różnych typów wiadomości
        self.log_text.tag_configure('win', foreground='green', font=('Arial', 10, 'bold'))
        self.log_text.tag_configure('loss', foreground='red', font=('Arial', 10, 'bold'))
        self.log_text.tag_configure('exchange', foreground='blue')
        self.log_text.tag_configure('raise', foreground='purple')
        self.log_text.tag_configure('fold', foreground='gray')
        self.log_text.tag_configure('check', foreground='dark green')
        self.log_text.tag_configure('call', foreground='orange')
        self.log_text.tag_configure('round', foreground='navy', font=('Arial', 10, 'bold'))
        self.log_text.tag_configure('error', foreground='red')
        self.log_text.tag_configure('default', foreground='black')
        self.log_text.tag_configure('shuffle', foreground='teal', font=('Arial', 10, 'italic'))
        self.log_text.tag_configure('deal', foreground='dark blue', font=('Arial', 10))

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def new_game(self):
        """Start a new game"""
        num_players = simpledialog.askinteger("New Game", "Number of players (2-6):",
                                              minvalue=2, maxvalue=6, initialvalue=4)
        if num_players:
            self.start_new_game(num_players)

    def start_new_game(self, num_players: int):
        """Initialize a new game"""
        # Stop any existing game
        self.is_game_running = False
        
        # Clear existing game state
        self.clear_game_state()
        
        # Create new game
        players = Player.create_players(num_players, 1000)
        self.game_engine = GameEngine(players, Deck())
        self.human_player = players[0]

        self.update_display()
        self.log_message("New game started!", 'round')
        self.log_message(f"Players: {num_players}", 'round')

        # Start game loop in separate thread
        self.is_game_running = True
        threading.Thread(target=self.game_loop, daemon=True).start()

    def game_loop(self):
        """Main game loop"""
        self.is_game_running = True
        
        while not self.game_engine.game_over and self.is_game_running:
            try:
                self.log_message("\n--- New Round ---", 'round')
                self.log_message(f"Dealer: {self.game_engine.players[self.game_engine.dealer_position].name}", 'round')
                self.log_message("🎲 Shuffling deck...", 'shuffle')
                self.update_display()

                # Override the human action methods
                original_get_human_action = self.game_engine._get_human_action
                original_get_human_exchange = self.game_engine._get_human_exchange

                self.game_engine._get_human_action = self.get_human_action_gui
                self.game_engine._get_human_exchange = self.get_human_exchange_gui

                winners = self.game_engine.play_round()
                if winners:
                    self._announce_winners(winners)
                    # If this was the final winner, break the loop
                    if winners[0][0] == "final_winner":
                        break
                self.update_display()
                
                # Check if game should end
                if self.game_engine.check_game_over():
                    break

                # Small delay between rounds
                self.root.after(1000)

            except Exception as e:
                self.log_message(f"Error during round: {e}", 'error')
                import traceback
                self.log_message(traceback.format_exc(), 'error')
            finally:
                # Restore original methods
                self.game_engine._get_human_action = original_get_human_action
                self.game_engine._get_human_exchange = original_get_human_exchange

        if self.game_engine.game_over:
            self.log_message("\n=== Game Over! ===", 'round')
            winner = max(self.game_engine.players, key=lambda p: p.stack)
            tag = 'win' if winner.name == "You" else 'loss'
            self.log_message(f"Final Winner: {winner.name} with ${winner.stack}", tag)
            self.update_display()

    def _announce_winners(self, winners):
        """Announce round winners and their hands"""
        # Check for final winner first
        if winners and winners[0][0] == "final_winner":
            _, winner, total_chips = winners[0]
            self.log_message("\n🏆 KONIEC GRY - ZWYCIĘZCA! 🏆", 'round')
            tag = 'win' if winner.name == "You" else 'loss'
            self.log_message(f"\n{winner.name} wygrywa całą grę z {total_chips} zł!", tag)
            self.log_message("\nPozostali gracze nie mają już żetonów.", 'loss')
            self.log_message("\n" + "="*50 + "\n", 'round')
            
            # Show game over dialog
            self.show_game_over_dialog(winner)
            return

        # Regular round announcement continues...
        # Show all player hands first
        self.log_message("\n📋 Koniec Rundy - Wszystkie Karty:", 'round')
        all_hands = winners[0][4]  # All winners have the same hand information
        
        # First show active players' hands
        self.log_message("\nAktywni Gracze:", 'round')
        for player_info in all_hands:
            if player_info['status'] == "Active":
                player_name = player_info['player_name']
                hand = player_info['hand']
                hand_name = player_info['hand_name']

                tag = 'win' if player_name == "You" else 'default'
                hand_str = " ".join(str(card) for card in hand) if hand else "---"
                hand_info = f"{hand_name} - " if hand_name else ""
                self.log_message(f"{player_name}: {hand_str} ({hand_info}Aktywny)", tag)

        # Then show folded players
        folded_players = [p for p in all_hands if p['status'] == "Folded"]
        if folded_players:
            self.log_message("\nGracze, którzy spasowali:", 'fold')
            for player_info in folded_players:
                player_name = player_info['player_name']
                hand = player_info['hand']
                hand_str = " ".join(str(card) for card in hand) if hand else "---"
                self.log_message(f"{player_name}: {hand_str}", 'fold')

        # Finally show players who are out
        out_players = [p for p in all_hands if p['status'] == "Out"]
        if out_players:
            self.log_message("\nGracze poza grą:", 'loss')
            for player_info in out_players:
                player_name = player_info['player_name']
                self.log_message(f"{player_name}: Brak żetonów", 'loss')

        # Then announce the result
        self.log_message("\n🏆 Wynik Rundy:", 'round')
        
        # Check if it's a draw
        is_draw = winners[0][5]  # Get draw flag
        if is_draw:
            self.handle_draw(winners)
        else:
            if len(winners) == 1:
                winner, hand_name, high_cards, pot_amount, _, _ = winners[0]
                if winner.name == "You":
                    tag = 'win'
                    self.log_message(f"WYGRYWASZ {pot_amount} zł" + (f" z układem {hand_name}!" if hand_name else " przez rezygnację pozostałych!"), tag)
                else:
                    tag = 'loss'
                    self.log_message(f"{winner.name} wygrywa {pot_amount} zł" + (f" z układem {hand_name}!" if hand_name else " przez rezygnację pozostałych!"), tag)

        self.log_message("\n" + "="*50 + "\n", 'round')  # Add separator between rounds

    def handle_draw(self, winners):
        """Handle a draw situation with a dialog for choosing the resolution"""
        # Create a dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Remis")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Show draw information
        pot_amount = winners[0][3]
        draw_info = f"Wykryto remis! Pula: {pot_amount} zł\n\nGracze z tym samym układem:"
        for winner, hand_name, _, _, _, _ in winners:
            draw_info += f"\n- {winner.name} z układem {hand_name}"

        info_label = ttk.Label(dialog, text=draw_info, wraplength=350)
        info_label.pack(pady=20)

        # Create a label for options
        options_label = ttk.Label(dialog, text="Wybierz sposób rozwiązania remisu:", font=("Arial", 10, "bold"))
        options_label.pack(pady=10)

        def on_split():
            dialog.destroy()
            result = self.game_engine.handle_draw_resolution("split")
            if result == "split":
                share = pot_amount // len(winners)
                self.log_message(f"🤝 Remis rozstrzygnięty: Pula ({pot_amount} zł) podzielona po równo", 'round')
                for winner, _, _, _, _, _ in winners:
                    self.log_message(f"{winner.name} otrzymuje {share} zł", 'default')
            self.update_display()

        def on_continue():
            dialog.destroy()
            self.log_message("🎲 Gracze zdecydowali się kontynuować licytację", 'round')
            result = self.game_engine.handle_draw_resolution("continue")
            if result == "split":
                final_share = self.game_engine.pot // len(winners)
                self.log_message(f"Końcowy podział: Każdy gracz otrzymuje {final_share} zł", 'round')
            elif result == "winner":
                winner = next(p for p in self.game_engine.players if p.is_active)
                self.log_message(f"Po dodatkowej licytacji: {winner.name} wygrywa {self.game_engine.pot} zł!", 
                               'win' if winner.name == "You" else 'loss')
            self.update_display()

        # Create buttons for options
        ttk.Button(dialog, text="Podziel pulę po równo", command=on_split).pack(pady=10)
        ttk.Button(dialog, text="Kontynuuj licytację", command=on_continue).pack(pady=10)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def get_human_action_gui(self, player: Player, current_bet: int) -> str:
        """Get human player action via GUI"""
        if player != self.human_player:
            return self.game_engine._get_bot_action(player, current_bet)

        self.root.after(0, self.enable_betting_buttons, current_bet)

        # Wait for human action
        self.waiting_for_action = True
        self.human_action = None

        while self.waiting_for_action:
            time.sleep(0.1)

        self.root.after(0, self.disable_action_buttons)
        return self.human_action

    def get_human_exchange_gui(self) -> List[int]:
        """Get human player card exchange via GUI"""
        self.root.after(0, self.enable_exchange_button)

        # Wait for human exchange
        self.waiting_for_action = True
        self.exchange_indices = []

        while self.waiting_for_action:
            time.sleep(0.1)

        self.root.after(0, self.disable_action_buttons)
        self.root.after(0, self.clear_card_selection)
        return self.exchange_indices

    def enable_betting_buttons(self, current_bet: int):
        """Enable betting buttons for human player"""
        call_amount = max(0, current_bet - self.human_player.current_bet)

        if call_amount == 0:
            self.check_call_btn.config(text="Check", state=tk.NORMAL)
        else:
            self.check_call_btn.config(text=f"Call ${call_amount}", state=tk.NORMAL)

        self.raise_btn.config(state=tk.NORMAL)
        self.fold_btn.config(state=tk.NORMAL)
        self.exchange_btn.config(state=tk.DISABLED)

        self.log_message(f"Your turn! Current bet: ${current_bet}, Your bet: ${self.human_player.current_bet}", 'check')

    def enable_exchange_button(self):
        """Enable exchange button for human player"""
        self.disable_action_buttons()
        self.exchange_btn.config(state=tk.NORMAL)
        self.log_message("Select cards to exchange (click cards to select/deselect)", 'exchange')

    def disable_action_buttons(self):
        """Disable all action buttons"""
        self.check_call_btn.config(state=tk.DISABLED)
        self.raise_btn.config(state=tk.DISABLED)
        self.fold_btn.config(state=tk.DISABLED)
        self.exchange_btn.config(state=tk.DISABLED)
        self.raise_entry.delete(0, tk.END)

    def check_call_action(self):
        """Handle check/call action"""
        if self.waiting_for_action:
            call_amount = max(0, self.game_engine.current_bet - self.human_player.current_bet)
            if call_amount == 0:
                self.human_action = "check"
                self.log_message("You check", 'check')
            else:
                self.human_action = "call"
                self.log_message(f"You call ${call_amount}", 'call')
            self.waiting_for_action = False
            self.update_display()

    def raise_action(self):
        """Handle raise action"""
        if self.waiting_for_action:
            try:
                raise_amount = int(self.raise_entry.get() or "0")
                if raise_amount <= 0:
                    messagebox.showerror("Error", "Raise amount must be positive")
                    return

                total_needed = self.game_engine.current_bet + raise_amount - self.human_player.current_bet
                if total_needed > self.human_player.stack:
                    messagebox.showerror("Error", "Not enough chips")
                    return

                self.human_action = f"raise {raise_amount}"
                self.log_message(f"You raise by ${raise_amount}", 'raise')
                self.waiting_for_action = False
                self.raise_entry.delete(0, tk.END)
                self.update_display()

            except ValueError:
                messagebox.showerror("Error", "Invalid raise amount")

    def fold_action(self):
        """Handle fold action"""
        if self.waiting_for_action:
            self.human_action = "fold"
            self.log_message("You fold", 'fold')
            self.waiting_for_action = False
            self.update_display()

    def exchange_action(self):
        """Handle card exchange action"""
        if self.waiting_for_action:
            self.exchange_indices = [i for i, selected in enumerate(self.card_selected) if selected]
            num_cards = len(self.exchange_indices)
            if num_cards > 0:
                self.log_message(f"🔄 You exchange {num_cards} card{'s' if num_cards > 1 else ''}", 'exchange')
            else:
                self.log_message("✋ You stand pat (no cards exchanged)", 'exchange')
            self.waiting_for_action = False
            self.update_display()

    def toggle_card_selection(self, index: int):
        """Toggle card selection for exchange"""
        if not self.waiting_for_action or not self.human_player or not self.human_player.hand:
            return
        self.card_selected[index] = not self.card_selected[index]
        self.update_card_display()

    def clear_card_selection(self):
        """Clear all card selections"""
        self.card_selected = [False] * 5
        self.update_card_display()

    def update_display(self):
        """Schedule a display update if one isn't already pending"""
        if not self.update_scheduled:
            self.update_scheduled = True
            self.root.after(100, self._perform_update)

    def _perform_update(self):
        """Perform the actual display update"""
        try:
            if self.game_engine:
                # Update game info
                self.pot_label.config(text=f"Pot: ${self.game_engine.pot}")
                self.current_bet_label.config(text=f"Current bet: ${self.game_engine.current_bet}")
                
                # Update players display
                self.update_players_display()
                
                # Update cards display
                self.update_card_display()
        except Exception as e:
            self.log_message(f"Display update error: {e}", 'error')
        finally:
            self.update_scheduled = False

    def update_players_display(self):
        """Update players information"""
        try:
            # Clear existing labels
            for label in self.player_labels:
                label.destroy()
            self.player_labels.clear()

            # Create new labels
            for i, player in enumerate(self.game_engine.players):
                if player.stack == 0:
                    status = "❌ Poza grą"
                    text = f"{player.name}: 0 zł ({status})"
                    label = ttk.Label(self.players_frame, text=text,
                                    font=("Arial", 10), foreground='red')
                else:
                    status = "Aktywny" if player.is_active else "Spasował"
                    text = f"{player.name}: {player.stack} zł ({status})"
                    if player.current_bet > 0:
                        text += f" - Zakład: {player.current_bet} zł"
                    if i == self.game_engine.dealer_position and player.stack > 0:
                        text += " [D]"
                    label = ttk.Label(self.players_frame, text=text,
                                    font=("Arial", 10, "bold" if player == self.human_player else "normal"))

                label.pack(anchor=tk.W, padx=10, pady=2)
                self.player_labels.append(label)
        except Exception as e:
            self.log_message(f"Błąd aktualizacji wyświetlania graczy: {e}", 'error')

    def update_card_display(self):
        """Update human player's cards display"""
        if not self.human_player or not self.human_player.hand:
            for i, btn in enumerate(self.card_buttons):
                btn.config(text="🎴", bg="SystemButtonFace")  # Use card emoji for empty slots
            return

        for i, card in enumerate(self.human_player.hand):
            card_text = str(card) if card else "🎴"
            bg_color = "yellow" if self.card_selected[i] else "SystemButtonFace"
            self.card_buttons[i].config(text=card_text, bg=bg_color)

    def log_message(self, message: str, tag='default'):
        """Add message to game log with specified color"""
        self.root.after(0, self._log_message_safe, message, tag)

    def _log_message_safe(self, message: str, tag='default'):
        """Thread-safe log message with color"""
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            # Force GUI update
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error logging message: {e}")

    def save_game(self):
        """Save current game state"""
        if not self.game_engine:
            messagebox.showwarning("Warning", "No game in progress")
            return

        try:
            session_data = self.session_manager.create_session_data(self.game_engine)
            game_id = self.session_manager.save_session(session_data)
            messagebox.showinfo("Success", f"Game saved successfully!\nGame ID: {game_id}")
            self.log_message(f"Game saved: {game_id}", 'round')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save game: {e}", 'error')

    def show_load_dialog(self):
        """Show dialog to load a saved game"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Game")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create and pack widgets
        label = ttk.Label(dialog, text="Select a saved game to load:")
        label.pack(pady=10)

        # Create frame for combobox and refresh button
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.X, padx=10)

        # Create combobox
        self.saved_games_var = tk.StringVar()
        self.saved_games_combo = ttk.Combobox(frame, textvariable=self.saved_games_var, width=50, state="readonly")
        self.saved_games_combo.pack(side=tk.LEFT, padx=(0, 5))

        # Refresh button
        refresh_btn = ttk.Button(frame, text="↻", width=3, command=lambda: self.refresh_saved_games(dialog))
        refresh_btn.pack(side=tk.LEFT)

        # Create text widget for game details
        details_text = tk.Text(dialog, height=10, width=60, wrap=tk.WORD, state=tk.DISABLED)
        details_text.pack(pady=10, padx=10)

        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        load_btn = ttk.Button(btn_frame, text="Load",
                            command=lambda: self.load_selected_game(dialog))
        load_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel",
                             command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind selection event
        def on_select(event):
            selection = self.saved_games_var.get()
            if selection:
                game_id = selection.split(" - ")[0]
                try:
                    session_data = self.session_manager.load_session(game_id)
                    details_text.config(state=tk.NORMAL)
                    details_text.delete(1.0, tk.END)
                    details_text.insert(tk.END, f"Game ID: {game_id}\n")
                    details_text.insert(tk.END, f"Saved on: {session_data.get('save_date', 'Unknown')}\n\n")
                    details_text.insert(tk.END, f"Players:\n")
                    for player in session_data['players']:
                        details_text.insert(tk.END, f"- {player['name']}: ${player['stack']}\n")
                    details_text.config(state=tk.DISABLED)
                except Exception as e:
                    details_text.config(state=tk.NORMAL)
                    details_text.delete(1.0, tk.END)
                    details_text.insert(tk.END, f"Error loading game details: {e}")
                    details_text.config(state=tk.DISABLED)

        self.saved_games_combo.bind('<<ComboboxSelected>>', on_select)

        # Initial population of saved games
        self.refresh_saved_games(dialog)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def refresh_saved_games(self, dialog):
        """Refresh the list of saved games in the combobox"""
        saved_games = self.session_manager.list_sessions()
        if not saved_games:
            self.saved_games_combo['values'] = ['No saved games available']
            self.saved_games_combo.set('No saved games available')
            return

        # Format the combobox entries
        formatted_games = [f"{game_id} - {save_date}" for game_id, save_date, _ in saved_games]
        self.saved_games_combo['values'] = formatted_games
        self.saved_games_combo.set(formatted_games[0])  # Select the most recent game

    def load_selected_game(self, dialog):
        """Load the selected game"""
        selection = self.saved_games_var.get()
        if not selection or selection == 'No saved games available':
            messagebox.showwarning("Warning", "Please select a valid game to load")
            return

        game_id = selection.split(" - ")[0]
        try:
            session_data = self.session_manager.load_session(game_id)
            self.restore_game_state(session_data)
            dialog.destroy()
            messagebox.showinfo("Success", "Game loaded successfully!")
            self.log_message(f"Game loaded: {game_id}", 'round')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load game: {e}", 'error')

    def show_delete_dialog(self):
        """Show dialog to delete a saved game"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Saved Game")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        label = ttk.Label(dialog, text="Select a game to delete:")
        label.pack(pady=10)

        # Create frame for combobox and refresh button
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.X, padx=10)

        # Create combobox
        delete_games_var = tk.StringVar()
        delete_games_combo = ttk.Combobox(frame, textvariable=delete_games_var, width=50, state="readonly")
        delete_games_combo.pack(side=tk.LEFT, padx=(0, 5))

        # Refresh button
        refresh_btn = ttk.Button(frame, text="↻", width=3,
                               command=lambda: self.refresh_delete_games(delete_games_combo))
        refresh_btn.pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def delete_game():
            selection = delete_games_var.get()
            if not selection or selection == 'No saved games available':
                messagebox.showwarning("Warning", "Please select a valid game to delete")
                return

            game_id = selection.split(" - ")[0]
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this saved game?\n{selection}"):
                if self.session_manager.delete_session(game_id):
                    messagebox.showinfo("Success", "Game deleted successfully!")
                    self.refresh_delete_games(delete_games_combo)
                else:
                    messagebox.showerror("Error", "Failed to delete game")

        delete_btn = ttk.Button(btn_frame, text="Delete", command=delete_game)
        delete_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Initial population of saved games
        self.refresh_delete_games(delete_games_combo)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def refresh_delete_games(self, combo):
        """Refresh the list of saved games in the delete dialog"""
        saved_games = self.session_manager.list_sessions()
        if not saved_games:
            combo['values'] = ['No saved games available']
            combo.set('No saved games available')
            return

        formatted_games = [f"{game_id} - {save_date} - {summary}" for game_id, save_date, summary in saved_games]
        combo['values'] = formatted_games
        combo.set(formatted_games[0])

    def restore_game_state(self, session_data: dict):
        """Restore game state from session data"""
        # Create players from session data
        players = []
        for player_data in session_data['players']:
            player = Player(player_data['stack'], player_data['name'])
            player.is_active = player_data['is_active']
            players.append(player)

        # Create game engine
        self.game_engine = GameEngine(
            players,
            Deck(),
            session_data.get('small_blind', 25),
            session_data.get('big_blind', 50)
        )

        # Restore game state
        self.game_engine.pot = session_data.get('pot', 0)
        self.game_engine.current_bet = session_data.get('current_bet', 0)
        self.game_engine.dealer_position = session_data.get('dealer_position', 0)

        self.human_player = players[0]
        self.update_display()

        # Start game loop
        threading.Thread(target=self.game_loop, daemon=True).start()

    def clear_game_state(self):
        """Clear all game-related state"""
        if hasattr(self, 'card_selected'):
            self.card_selected = [False] * 5
        
        # Clear display elements
        for label in self.player_labels:
            label.destroy()
        self.player_labels.clear()
        
        # Reset game state variables
        self.waiting_for_action = False
        self.human_action = None
        self.exchange_indices = []
        self.update_scheduled = False
        
        # Clear log
        if hasattr(self, 'log_text'):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

    def show_game_over_dialog(self, winner):
        """Show game over dialog with final results"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Koniec Gry!")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create a frame for the content
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Trophy emoji and game over text
        title_label = ttk.Label(frame, 
                              text="🏆 Koniec Gry! 🏆",
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Winner announcement
        winner_text = f"Zwycięzca: {winner.name}\nKońcowy stan konta: {winner.stack} zł"
        winner_label = ttk.Label(frame, 
                               text=winner_text,
                               font=("Arial", 12))
        winner_label.pack(pady=(0, 20))

        # Congratulatory message
        if winner.name == "You":
            congrats_text = "Gratulacje! Wygrałeś grę! 🎉"
        else:
            congrats_text = f"Koniec gry! {winner.name} wygrał grę."
        
        congrats_label = ttk.Label(frame, 
                                 text=congrats_text,
                                 font=("Arial", 10))
        congrats_label.pack(pady=(0, 20))

        # Buttons frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=(20, 0))

        def new_game():
            dialog.destroy()
            self.new_game()

        def quit_game():
            dialog.destroy()
            self.root.quit()

        # Add buttons
        ttk.Button(button_frame, 
                  text="Rozpocznij Nową Grę",
                  command=new_game).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, 
                  text="Wyjdź",
                  command=quit_game).pack(side=tk.LEFT, padx=5)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        finally:
            self.is_game_running = False  # Ensure game loop stops if GUI is closed
