import pygame
import copy
import time
import random
from UI_tools.win_screen import WinScreen
from UI_tools.BaseUi import BaseUI
from Board.Board_draw_tools import Board_draw_tools
from Game_ui.move_rules import Moves_rules


class Katarenga(BaseUI):
    def __init__(self, ai, board, title="Katarenga"):
        super().__init__(title)

        if board is None:
            raise ValueError("Board can't be None")  # check input

        self.board = self.place_pawn_katarenga(board)  # setup pawns
        self.board_ui = Board_draw_tools()  # drawing helper
        self.moves_rules = Moves_rules(self.board)  # move rules

        self.cell_size = 60  # size of one cell
        self.grid_dim = 10  # 10x10 grid
        self.grid_size = self.cell_size * self.grid_dim  # total size

        self.top_offset = 80  # vertical offset
        self.left_offset = (self.get_width() - self.grid_size) // 2  # center horizontally

        self.title_font = pygame.font.SysFont(None, 48)  # font for title
        self.title_surface = self.title_font.render("Katarenga", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.get_width() // 2, 40))

        self.back_button_rect = pygame.Rect(20, 20, 120, 40)  # back button

        self.current_player = 1  # player 1 starts
        self.selected_pawn = None  # no pawn selected

        self.__ai = ai  # AI mode on/off

        self.info_font = pygame.font.SysFont(None, 36)  # font for info text

        # Movement directions by pawn color
        self.directions = {
            1: [(dx, dy) for dx in [-1,0,1] for dy in [-1,0,1] if dx != 0 or dy != 0],  # blue = all around
            2: [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)],  # green = knight moves
            3: [(-1,-1),(-1,1),(1,-1),(1,1)],  # yellow = diagonals
            4: [(-1,0),(1,0),(0,-1),(0,1)]  # red = straight lines
        }

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

            if self.__ai and self.current_player == 2:
                time.sleep(1)
                self.play_ai_turn()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False  # quit game
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(event.pos):
                    self.running = False  # back clicked
                else:
                    self.handle_board_click(event.pos)  # board clicked

    def handle_board_click(self, pos):
        x, y = pos
        if (self.left_offset <= x < self.left_offset + self.grid_size and
            self.top_offset <= y < self.top_offset + self.grid_size):

            col = (x - self.left_offset) // self.cell_size
            row = (y - self.top_offset) // self.cell_size

            if 0 <= row < self.grid_dim and 0 <= col < self.grid_dim:
                self.process_move(row, col)

    def place_pawn_katarenga(self, board):
        new_board = copy.deepcopy(board)  # copy board to avoid mutation

        # Player 2 pawns top row
        for col in range(1, 9):
            color = new_board[1][col] // 10
            new_board[1][col] = color * 10 + 2

        # Player 1 pawns bottom row
        for col in range(1, 9):
            color = new_board[8][col] // 10
            new_board[8][col] = color * 10 + 1

        return new_board

    def process_move(self, row, col):
        cell_value = self.board[row][col]
        player_on_cell = cell_value % 10
        
        if self.selected_pawn is None:
            if player_on_cell == self.current_player:
                self.selected_pawn = (row, col)
                print(f"Pion sélectionné à ({row}, {col})")
        else:
            selected_row, selected_col = self.selected_pawn
            
            if (row, col) == self.selected_pawn:
                self.selected_pawn = None
                print("Pion désélectionné")
            elif player_on_cell == self.current_player:
                self.selected_pawn = (row, col)
                print(f"Nouveau pion sélectionné à ({row}, {col})")
            else:
                if self.current_player == 1 and 1 <= selected_col <= 9 and selected_row == 1 and (row, col) in [(0, 0), (0, 9)]:
                    self.make_move(selected_row, selected_col, row, col)
                    self.selected_pawn = None
                    winner = self.check_victory()
                    if winner == 0:
                        self.switch_player()
                elif self.current_player == 2 and 1 <= selected_col <= 9 and selected_row == 8 and (row, col) in [(9, 0), (9, 9)]:
                    self.make_move(selected_row, selected_col, row, col)
                    self.selected_pawn = None
                    winner = self.check_victory()
                    if winner == 0:
                        self.switch_player()
                elif self.is_valid_move(selected_row, selected_col, row, col):
                    self.make_move(selected_row, selected_col, row, col)
                    self.selected_pawn = None
                    winner = self.check_victory()
                    if winner == 0:
                        self.switch_player()
                else:
                    print("invalid movement")

    def is_valid_move(self, fr, fc, tr, tc):
        case_color = self.board[fr][fc]
        return self.moves_rules.verify_move(case_color, fr, fc, tr, tc)

    def make_move(self, fr, fc, tr, tc):
        dest_color = self.board[tr][tc] // 10
        origin_color = self.board[fr][fc] // 10
        self.board[fr][fc] = origin_color * 10  # empty old spot
        self.board[tr][tc] = dest_color * 10 + self.current_player  # place pawn
        print(f"Moved from ({fr},{fc}) to ({tr},{tc})")

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        print(f"Player {self.current_player}'s turn")

    def play_ai_turn(self):
        # Simple AI for local mode
        player_pawns = []
        for row in range(self.grid_dim):
            for col in range(self.grid_dim):
                if self.board[row][col] % 10 == 2:
                    player_pawns.append((row, col))
        
        if not player_pawns:
            return
        
        random.shuffle(player_pawns)
        for from_row, from_col in player_pawns:
            possible_moves = []
            for to_row in range(self.grid_dim):
                for to_col in range(self.grid_dim):
                    if self.is_valid_move(from_row, from_col, to_row, to_col):
                        possible_moves.append((to_row, to_col))
            
            if possible_moves:
                to_row, to_col = random.choice(possible_moves)
                self.make_move(from_row, from_col, to_row, to_col)
                
                if self.check_victory() == 0:
                    self.switch_player()
                return

    def draw_pawn(self, screen, rect, player_code):
        center = rect.center
        radius = self.cell_size // 3
        
        if player_code == 1:
            pygame.draw.circle(screen, (255, 255, 255), center, radius)
            pygame.draw.circle(screen, (0, 0, 0), center, radius, 2)
        elif player_code == 2:
            pygame.draw.circle(screen, (0, 0, 0), center, radius)
            pygame.draw.circle(screen, (255, 255, 255), center, radius, 2)

    def draw(self):
        #Draw the full game screen: background, board grid, pawns, UI elements.
        screen = self.get_screen()

        # Draw background
        screen.blit(self.get_background(), (0, 0))

        # Draw title
        screen.blit(self.title_surface, self.title_rect)  # draw title

        for row in range(self.grid_dim):
            for col in range(self.grid_dim):
                rect = pygame.Rect(
                    col * self.cell_size + self.left_offset,
                    row * self.cell_size + self.top_offset,
                    self.cell_size,
                    self.cell_size
                )
                value = self.board[row][col]
                color_code = value // 10
                player_code = value % 10

                color = self.board_ui.get_color_from_board(color_code)
                pygame.draw.rect(screen, color, rect)

                if self.selected_pawn == (row, col):
                    pygame.draw.rect(screen, (255, 255, 0), rect, 4)  # highlight selected

                pygame.draw.rect(screen, (255, 255, 255), rect, 1)  # grid lines

                if player_code > 0:
                    self.draw_pawn(screen, rect, player_code)  # draw pawn

                if player_code > 0:
                    self.draw_pawn(screen, rect, player_code)
        
        # Draw back button
        pygame.draw.rect(screen, (70, 70, 70), self.back_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.back_button_rect, 2)
        back_text = pygame.font.SysFont(None, 36).render("Retour", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button_rect.center))
        
        # Draw game info
        self.draw_game_info(screen)


    def draw_pawn(self, screen, rect, player):
        center_x = rect.centerx
        center_y = rect.centery
        radius = self.cell_size // 4
        
        
        if player == 1:
            pawn_color = (0, 0, 255)  # Blue for player 1
        elif player == 2:
            pawn_color = (255, 0, 0)  # Red for player 2
        else:
            return
        
        # Draw pawn 
        pygame.draw.circle(screen, pawn_color, (center_x, center_y), radius)
        pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), radius, 2)
        

    def draw_game_info(self, screen):

        # Display current player
        player_text = f"Tour du joueur {self.current_player}"
        player_color = (0, 0, 255) if self.current_player == 1 else (255, 0, 0)
        
        text_surface = self.info_font.render(player_text, True, player_color)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (self.left_offset, self.top_offset + self.grid_size + 40)
        screen.blit(text_surface, text_rect)
        
        # Display instructions
        if self.selected_pawn:
            instruction = "Click a case to move the selected pawn"
        else:
            instruction = "Click on a pawn to select it, then click a case to move it"
        
        instruction_surface = pygame.font.SysFont(None, 24).render(instruction, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect()
        instruction_rect.topleft = (self.left_offset, text_rect.bottom + 10)
        screen.blit(instruction_surface, instruction_rect)

    def count_pawns(self):
        player1_count = 0
        player2_count = 0
        
        for row in range(10):
            for col in range(10):
                player = self.board[row][col] % 10
                if player == 1:
                    player1_count += 1
                elif player == 2:
                    player2_count += 1
        
        return player1_count, player2_count
    
    def check_victory(self):
        player1_count, player2_count = self.count_pawns()
        
        if player1_count == 0:
            print("The player 2 has won (no pawns left for player 1)!")
            self.running = False
            WinScreen("Player 2")
            return 2
        if player2_count == 0:
            print("The player 1 has won (no pawns left for player 2)!")
            WinScreen("Player 1")
            self.running = False
            return 1

        if self.board[9][0] % 10 == 2 and self.board[9][9] % 10 == 2:
            print("The player 1 has won (occupied the corners bottom left and right)!")
            WinScreen("Player 1")   
            self.running = False
            return 1

        if self.board[0][0] % 10 == 1 and self.board[0][9] % 10 == 1:
            print("the player 2 has won (occupied the corners top left and right)!")
            WinScreen("Player 2")
            self.running = False
            return 2

        return 0
    
    def play_ai_turn(self):
        from random import choice, shuffle

        if self.current_player != 2:
            return

        pawns = []
        for x in range(10):
            for y in range(10):
                if self.board[x][y] % 10 == 2:
                    pawns.append((x, y))

        shuffle(pawns)

        for x, y in pawns:
            couleur = self.board[x][y] // 10
            dir_list = self.directions.get(couleur, [])
            shuffle(dir_list)

            for dx, dy in dir_list:
                steps = 1
                while True:
                    new_x = x + dx * steps
                    new_y = y + dy * steps

                    if not (0 <= new_x < 10 and 0 <= new_y < 10):
                        break

                    if self.moves_rules.verify_move(self.board[x][y], x, y, new_x, new_y):
                        self.make_move(x, y, new_x, new_y)
                        print(f"IA a joué de ({x}, {y}) à ({new_x}, {new_y})")

                        winner = self.check_victory()
                        if winner == 0:
                            self.switch_player()
                        return

                    if couleur in [1, 2]:
                        break

                    if self.board[new_x][new_y] != 0:
                        break

                    steps += 1

        print("L'IA n'a pas trouvé de coup valide.")