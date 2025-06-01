import pygame 
import copy
from collections import deque

from UI_tools.BaseUi import BaseUI
from Board.Board_draw_tools import Board_draw_tools
from Game_ui.move_rules import Moves_rules
from UI_tools.win_screen import WinScreen

class Congress(BaseUI):
    def __init__(self, ai, board, title="Congress"):
        super().__init__(title)

        if board is None:
            raise ValueError("Board cannot be None")

        # Create a deep copy of the initial board to avoid modifying the original
        self.base_board = copy.deepcopy(board)

        # Board and UI dimensions
        self.cell_size = 60
        self.grid_dim = 8
        self.grid_size = self.cell_size * self.grid_dim
        self.top_offset = 80
        self.left_offset = (self.get_width() - self.grid_size) // 2

        # Title font and text surface for display
        self.title_font = pygame.font.SysFont(None, 48)
        self.title_surface = self.title_font.render("Congress", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.get_width() // 2, 40))

        # Back button rectangle for navigation
        self.back_button_rect = pygame.Rect(20, 20, 120, 40)

        # Initialize the game board with pawns placed according to Congress rules
        self.board = self.place_pawn_congress(self.base_board)

        # Tools for board drawing and move validation
        self.board_ui = Board_draw_tools()
        self.moves_rules = Moves_rules(self.board)

        # Game state variables
        self.current_player = 1
        self.selected_pawn = None
        self.info_font = pygame.font.SysFont(None, 36)

        self.__ai = ai  # AI player flag or instance
        
        # Flags for victory handling
        self.network_mode = False
        self.victory_callback = None  # Callback for network mode

    def place_pawn_congress(self, base_board):
        new_board = copy.deepcopy(base_board)
        for i in range(self.grid_dim):
            for j in range(self.grid_dim):
                color_code = new_board[i][j] // 10
                new_board[i][j] = color_code * 10  # Clear pawns, keep base color

        # Direct placement of pawns
        black_pawns = [(0, 1), (0, 4), (1, 7), (3, 0), (4, 7), (6, 0), (7, 3), (7, 6)]
        white_pawns = [(0, 3), (0, 6), (1, 0), (3, 7), (4, 0), (6, 7), (7, 1), (7, 4)]

        for r, c in black_pawns:
            color = new_board[r][c] // 10
            new_board[r][c] = color * 10 + 2

        for r, c in white_pawns:
            color = new_board[r][c] // 10
            new_board[r][c] = color * 10 + 1

        return new_board

    def set_network_mode(self, network_mode=True, victory_callback=None):
        self.network_mode = network_mode
        self.victory_callback = victory_callback

    def run(self):
        # Main game loop: handles events, draws UI, updates display, and runs AI if active.
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

            # If AI is active and it is AI's turn (player 2)
            if self.__ai and self.current_player == 2:
                self.congress_ai()

    def handle_events(self):
        # Event handler for quitting, back button, and board clicks.
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(event.pos):
                    self.running = False
                else:
                    self.handle_board_click(event.pos)

    def handle_board_click(self, pos):
        # Handles clicks inside the board grid, converting pixel to grid coordinates.
        x, y = pos
        if (self.left_offset <= x < self.left_offset + self.grid_size and
            self.top_offset <= y < self.top_offset + self.grid_size):
            col = (x - self.left_offset) // self.cell_size
            row = (y - self.top_offset) // self.cell_size
            if 0 <= row < self.grid_dim and 0 <= col < self.grid_dim:
                self.process_move(row, col)

    def process_move(self, row, col):
        val = self.board[row][col]
        owner = val % 10

        if self.selected_pawn is None:
            # Select pawn if it belongs to current player
            if owner == self.current_player:
                self.selected_pawn = (row, col)
                print(f"Pawn selected at ({row}, {col})")
        else:
            sel_r, sel_c = self.selected_pawn
            if (row, col) == (sel_r, sel_c):
                # Deselect pawn if clicked again
                self.selected_pawn = None
                print("Pawn deselected")
            elif owner == self.current_player:
                # Change selection to another own pawn
                self.selected_pawn = (row, col)
                print(f"New pawn selected at ({row}, {col})")
            else:
                # Attempt move to empty square
                if self.board[row][col] % 10 == 0 and self.is_valid_move(sel_r, sel_c, row, col):
                    self.make_move(sel_r, sel_c, row, col)
                    self.selected_pawn = None
                    
                    # Always check for victory after a move
                    self.check_and_handle_victory()
                    
                    # If no victory, switch player
                    if self.running:  # Game is still running
                        self.switch_player()
                else:
                    print("Invalid move or square occupied")

    def check_and_handle_victory(self):
        winner = self.check_all_players_victory()
        if winner:
            if self.network_mode:
                # Network mode: notify via callback without displaying WinScreen
                print(f"Victory detected in network mode: Player {winner}")
                if self.victory_callback:
                    self.victory_callback(winner)
                # Game continues, NetworkGameAdapter handles display
            else:
                # Local mode: display WinScreen and stop the game
                print(f"Victory detected in local mode: Player {winner}")
                self.trigger_victory_local(winner)

    def is_valid_move(self, fr, fc, tr, tc):
        # Checks if move is valid by delegating to move rules verifier.
        case_color = self.board[fr][fc]
        return self.moves_rules.verify_move(case_color, fr, fc, tr, tc)

    def make_move(self, fr, fc, tr, tc):
        # Executes move on board: clears origin cell, places pawn on target cell.
        dest_color = self.base_board[tr][tc] // 10
        orig_color = self.base_board[fr][fc] // 10
        self.board[fr][fc] = orig_color * 10  # Clear origin cell
        self.board[tr][tc] = dest_color * 10 + self.current_player  # Place pawn at destination
        print(f"Moved from ({fr}, {fc}) to ({tr}, {tc})")

    def switch_player(self):
        # Switch current player between 1 and 2.
        self.current_player = 2 if self.current_player == 1 else 1
        print(f"Player {self.current_player}'s turn")

    def check_victory(self, player):
        positions = [(i, j) for i in range(self.grid_dim) for j in range(self.grid_dim)
                     if self.board[i][j] % 10 == player]
        if not positions:
            return False
        visited = set([positions[0]])
        queue = deque([positions[0]])
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.grid_dim and 0 <= ny < self.grid_dim and
                    (nx, ny) not in visited and self.board[nx][ny] % 10 == player):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        # Victory if all player's pawns are connected
        return len(visited) == len(positions)

    def check_all_players_victory(self):
        for player in [1, 2]:
            if self.check_victory(player):
                return player
        return None

    def trigger_victory_local(self, winner):
        # print(f"Local victory triggered: Player {winner} wins!")
        self.running = False
        
        try:
            # Display the win screen with the appropriate name
            if winner == 1:
                WinScreen("Player 1")
            elif winner == 2:
                if self.__ai:
                    WinScreen("Player 2 (AI)")
                else:
                    WinScreen("Player 2")
        except Exception as e:
            print(f"Error showing win screen: {e}")

    def draw(self):
        # Draw the full game screen: background, board grid, pawns, UI elements.
        screen = self.get_screen()

        # Draw background
        screen.blit(self.get_background(), (0, 0))

        # Draw title
        screen.blit(self.title_surface, self.title_rect)

        # Draw the board cells and pawns
        for row in range(self.grid_dim):
            for col in range(self.grid_dim):
                rect = pygame.Rect(
                    col * self.cell_size + self.left_offset,
                    row * self.cell_size + self.top_offset,
                    self.cell_size,
                    self.cell_size
                )
                base_val = self.base_board[row][col]
                color_code = base_val // 10
                color = self.board_ui.get_color_from_board(color_code)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)

                # Highlight selected...
