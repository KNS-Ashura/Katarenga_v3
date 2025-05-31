
import pygame
import random
import time
from UI_tools.BaseUi import BaseUI
from Board.Board_draw_tools import Board_draw_tools
from Game_ui.move_rules import Moves_rules
from UI_tools.win_screen import WinScreen

class Isolation(BaseUI):
    def __init__(self, ai, board, title="Isolation"):
        super().__init__(title)
        self.board = board
        self.rules = Moves_rules(board)
        self.board_ui = Board_draw_tools()

        self.cell_size = 60
        self.grid_dim = 8
        self.grid_size = self.cell_size * self.grid_dim

        self.top_offset = 80
        self.left_offset = (self.get_width() - self.grid_size) // 2

        self.title_font = pygame.font.SysFont(None, 48)
        self.title_surface = self.title_font.render("Isolation", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.get_width() // 2, 40))

        self.back_button_rect = pygame.Rect(20, 20, 120, 40)

        self.current_player = 1
        self.total_moves = 0
        self.max_moves = self.grid_dim * self.grid_dim

        self.__AI = ai  # AI opponent enabled if True

    def run(self):
        self.running = True
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

            # If AI is player 2, make AI move after a short delay
            if self.__AI and self.current_player == 2 and self.running:
                time.sleep(2)
                self.play_ai_move()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(event.pos):
                    self.running = False
                else:
                    self.handle_click(event.pos)

    def handle_click(self, pos):
        if self.__AI and self.current_player == 2:
            return  # Ignore clicks if AI's turn

        x, y = pos
        col = (x - self.left_offset) // self.cell_size
        row = (y - self.top_offset) // self.cell_size

        # Check if click is inside the grid
        if 0 <= row < self.grid_dim and 0 <= col < self.grid_dim:
            case = self.board[row][col]
            # Check if the cell is free and not under threat
            if case % 10 == 0 and not self.in_prise(row, col):
                color = case // 10
                self.board[row][col] = color * 10 + self.current_player
                self.total_moves += 1
                # Check for game end conditions
                if self.total_moves >= self.max_moves or not self.can_play():
                    print(f"Player {self.current_player} wins!")
                    WinScreen(f"Player {self.current_player}")
                    self.running = False
                else:
                    # Switch player
                    self.current_player = 2 if self.current_player == 1 else 1

    def in_prise(self, x, y):
        # Check if the move at (x,y) is under attack by any opponent move
        for i in range(self.grid_dim):
            for j in range(self.grid_dim):
                case = self.board[i][j]
                if case % 10 != 0:
                    if self.rules.verify_move(case, i, j, x, y):
                        return True
        return False

    def can_play(self):
        # Check if current player has any valid moves left
        for i in range(self.grid_dim):
            for j in range(self.grid_dim):
                case = self.board[i][j]
                if case not in (0, 50, 60) and case % 10 == 0 and not self.in_prise(i, j):
                    return True
        return False

    def draw(self):
        #Draw the full game screen: background, board grid, pawns, UI elements.
        screen = self.get_screen()
        # Draw background
        screen.blit(self.get_background(), (0, 0))
        # Draw title
        screen.blit(self.title_surface, self.title_rect)  # draw title

        # Draw the game board grid and pieces
        for row in range(self.grid_dim):
            for col in range(self.grid_dim):
                rect = pygame.Rect(
                    col * self.cell_size + self.left_offset,
                    row * self.cell_size + self.top_offset,
                    self.cell_size,
                    self.cell_size
                )
                value = self.board[row][col]
                color = self.board_ui.get_color_from_board(value // 10)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)

                # Draw player pieces
                if value % 10 != 0:
                    center = rect.center
                    radius = self.cell_size // 3
                    if value % 10 == 1:
                        pygame.draw.circle(screen, (255, 0, 0), center, radius)
                    elif value % 10 == 2:
                        pygame.draw.circle(screen, (0, 0, 255), center, radius)

        # Draw back button
        pygame.draw.rect(screen, (70, 70, 70), self.back_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.back_button_rect, 2)
        back_text = pygame.font.SysFont(None, 36).render("Back", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button_rect.center))

    def play_ai_move(self):
        possibles = []
        # Collect all possible moves for AI player
        for i in range(self.grid_dim):
            for j in range(self.grid_dim):
                case = self.board[i][j]
                if case not in (0, 50, 60) and case % 10 == 0 and not self.in_prise(i, j):
                    possibles.append((i, j))

        if not possibles:
            print("AI can't move, Player 1 wins!")
            try:
                WinScreen("Player 1")
            except Exception as e:
                print(f"Error showing win screen: {e}")
            self.running = False
            return

        # Random pick valid move
        i, j = random.choice(possibles)
        case = self.board[i][j]
        color = case // 10
        self.board[i][j] = color * 10 + 2
        self.total_moves += 1

        
        if self.total_moves >= self.max_moves or not self.can_play():
            print("AI (Player 2) wins!")
            try:
                WinScreen("Player 2 (AI)")
            except Exception as e:
                print(f"Error showing win screen: {e}")
            self.running = False
        else:
            self.current_player = 1