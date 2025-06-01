import pygame 
import copy
from UI_tools.BaseUi import BaseUI
from Board.Board_draw_tools import Board_draw_tools
from Game_ui.move_rules import Moves_rules
from UI_tools.win_screen import WinScreen

from Game_ui.Katarenga import Katarenga
from Game_ui.Congress import Congress
from Game_ui.Isolation import Isolation

class NetworkGameAdapter(BaseUI):
    
    def __init__(self, game_session, title="Network Game"):
        super().__init__(title)
        
        # Network game session
        self.session = game_session
        self.board = game_session.board
        self.game_type = game_session.game_type
        self.local_player = 1 if game_session.is_host else 2
        
        # Create an instance of the game to reuse its methods
        self.game_instance = self._create_game_instance()
        
        # Network game state
        self.selected_pawn = None
        self.current_player = 1
        self.game_finished = False
        self.status_message = ""
        self.status_color = (255, 255, 255)
        
        # Set up callbacks
        self.session.set_game_callbacks(
            board_update=self.on_board_update,
            player_change=self.on_player_change,
            game_end=self.on_game_end
        )
    
    def _create_game_instance(self):
        ai_disabled = False
        
        if self.game_type == 1:
            return Katarenga(ai_disabled, self.board)
        elif self.game_type == 2:
            # For Congress, we use the original file but configure network mode
            congress_instance = Congress(ai_disabled, self.board)
            # Replace the generated board with the network board
            congress_instance.board = self.board
            congress_instance.base_board = self._extract_base_board(self.board)
            # IMPORTANT: Configure network mode with callback
            congress_instance.set_network_mode(True, victory_callback=self._handle_local_victory)
            return congress_instance
        elif self.game_type == 3:
            return Isolation(ai_disabled, self.board)
        else:
            raise ValueError(f"Unknown game type: {self.game_type}")
    
    def _handle_local_victory(self, winner):
        #print(f"Victory callback received: Player {winner}")
        # Immediately trigger the victory screen
        self._trigger_victory(winner)
    
    def _extract_base_board(self, board_with_pawns):
        base_board = copy.deepcopy(board_with_pawns)
        
        for i in range(len(base_board)):
            for j in range(len(base_board[0])):
                # Keep only the base color (remove pawns)
                color_code = base_board[i][j] // 10
                base_board[i][j] = color_code * 10
        
        return base_board
    
    def run(self):
        self.session.start_game()
        
        while self.running and not self.game_finished:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        # Wait for user to close window after game ends
        if self.game_finished:
            waiting_for_close = True
            while waiting_for_close:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        waiting_for_close = False
                
                # Continue drawing the end screen
                self.draw()
                pygame.display.flip()
                self.clock.tick(60)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
    
    def handle_click(self, pos):
        # Check if clicking back button FIRST (should work regardless of turn)
        back_rect = pygame.Rect(20, 20, 120, 40)
        if back_rect.collidepoint(pos):
            self.running = False
            return
            
        # Check if clicking back button (if game instance has one)
        if hasattr(self.game_instance, 'back_button_rect'):
            if self.game_instance.back_button_rect.collidepoint(pos):
                self.running = False
                return
        
        # Check if it's the player's turn for game moves
        if self.current_player != self.local_player:
            self.set_status("It's not your turn", (255, 255, 100))
            return
        
        # Handle game-specific clicks
        if self.game_type in [1, 2]:  # Katarenga and Congress
            self._handle_board_click_katarenga_congress(pos)
        elif self.game_type == 3:  # Isolation
            self._handle_click_isolation(pos)
    
    def _handle_board_click_katarenga_congress(self, pos):
        row, col = self._get_board_position(pos)
        if row is None or col is None:
            return
        
        cell_value = self.board[row][col]
        player_on_cell = cell_value % 10
        
        if self.selected_pawn is None:
            # Selecting pawns but only own pawns
            if player_on_cell == self.local_player:
                self.selected_pawn = (row, col)
                self.set_status(f"Pawn selected at ({row}, {col})", (100, 255, 100))
            elif player_on_cell != 0:
                self.set_status("That's not your pawn!", (255, 100, 100))
            else:
                self.set_status("Select one of your pawns", (255, 255, 100))
        else:
            # Move or deselect
            if (row, col) == self.selected_pawn:
                self.selected_pawn = None
                self.set_status("Pawn deselected", (200, 200, 200))
            elif player_on_cell == self.local_player:
                # Switch to another own pawn
                self.selected_pawn = (row, col)
                self.set_status(f"New pawn selected at ({row}, {col})", (100, 255, 100))
            else:
                # Try to move to this position
                from_row, from_col = self.selected_pawn
                
                # Check if it's my own pawn
                if self.board[from_row][from_col] % 10 != self.local_player:
                    self.set_status("Error: Not your pawn!", (255, 100, 100))
                    self.selected_pawn = None
                    return
                
                # Attempt to make move through network
                if self.session.make_move((from_row, from_col), (row, col)):
                    self.selected_pawn = None
                    self.set_status("Move successful", (100, 255, 100))
                else:
                    self.set_status("Invalid move", (255, 100, 100))
    
    def _handle_click_isolation(self, pos):
        row, col = self._get_board_position(pos)
        if row is None or col is None:
            return
        
        # Attempt to place piece through network
        if self.session.make_move(None, (row, col)):
            self.set_status("Piece placed", (100, 255, 100))
            # CORRECTION: DO NOT check victory here - it's handled by GameSession
        else:
            self.set_status("Invalid placement", (255, 100, 100))
    
    def _get_board_position(self, pos):
        x, y = pos
        
        if hasattr(self.game_instance, 'left_offset'):
            left_offset = self.game_instance.left_offset
            top_offset = self.game_instance.top_offset
            cell_size = self.game_instance.cell_size
            grid_dim = self.game_instance.grid_dim
        else:
            # Fallback values
            left_offset = (self.get_width() - 600) // 2
            top_offset = 80
            cell_size = 60
            grid_dim = len(self.board)
        
        if not (left_offset <= x < left_offset + grid_dim * cell_size and
                top_offset <= y < top_offset + grid_dim * cell_size):
            return None, None
        
        col = (x - left_offset) // cell_size
        row = (y - top_offset) // cell_size
        
        if 0 <= row < grid_dim and 0 <= col < grid_dim:
            return row, col
        return None, None
    
    def on_board_update(self, new_board):
        self.board = new_board
        self.game_instance.board = new_board  # Sync with game instance
        
        # For Congress, also update the base_board
        if self.game_type == 2 and hasattr(self.game_instance, 'base_board'):
            self.game_instance.base_board = self._extract_base_board(new_board)
        
        # CORRECTION: No longer check victory here - it's handled by GameSession
        # Victory conditions are now handled centrally
        
        #print("Board updated")
    
    def _trigger_victory(self, winner):
        self.game_finished = True

        # Determine winner name
        if winner == self.local_player:
            winner_name = f"Player {winner}"
            self.set_status("You win!", (100, 255, 100))
        else:
            winner_name = f"Player {winner}"
            self.set_status("You lose!", (255, 100, 100))
        
        # Display win screen after setting the name
        WinScreen(winner_name)

        # Notify the network
        if hasattr(self.session, '_end_game'):
            try:
                self.session._end_game(winner)
            except Exception as e:
                #print(f"Error sending victory to network: {e}")
                pass
    
    def on_player_change(self, new_player):
        self.current_player = new_player
        if new_player == self.local_player:
            self.set_status("Your turn", (100, 255, 100))
        else:
            self.set_status("Opponent's turn", (255, 255, 100))
    
    def on_game_end(self, winner):
        self.game_finished = True
        if winner == "Disconnection":
            self.set_status("Opponent disconnected - Press Escape to quit", (255, 100, 100))
            if self.local_player == 1:
                WinScreen("Player 1 (You - Opponent disconnected)")
            else:
                WinScreen("Player 2 (You - Opponent disconnected)")
        elif winner == self.local_player:
            self.set_status("You win! Press Escape to quit", (100, 255, 100))
            WinScreen(f"Player {self.local_player} (You)")
        else:
            self.set_status("You lose! Press Escape to quit", (255, 100, 100))
            WinScreen(f"Player {3 - self.local_player}")
