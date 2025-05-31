import pygame

from Board.Board import Board
from Board.Board_draw_tools import Board_draw_tools
from UI_tools.BaseUi import BaseUI
from Game_ui.Katarenga import Katarenga
from Game_ui.Congress import Congress
from Game_ui.Isolation import Isolation

class SquareSelectorUi(BaseUI):
    def __init__(self, gamemode, title="Select your square", network_mode=False):
        super().__init__(title)

        self.board_obj = Board()
        self.board_ui = Board_draw_tools()
        self.board = self.board_obj.get_default_board()
        
        self.gamemode = gamemode
        self.network_mode = network_mode  # Flag to distinguish network vs local mode

        self.cell_size = 50
        self.grid_dim = 8
        self.grid_size = self.cell_size * self.grid_dim
        self.board_width = self.grid_size

        self.title_font = pygame.font.SysFont(None, 48)
        self.button_font = pygame.font.SysFont(None, 36)

        # Position where selected square is displayed
        self.square_display_pos = (self.get_width() // 2 - 2 * self.cell_size, 240)

        # Board reference coordinates for placing control buttons
        self.board_x = self.square_display_pos[0]
        self.board_y = self.square_display_pos[1]

        self.transform_button_size = 60
        x = self.board_x + self.board_width + 40
        y = self.board_y

        self.rotate_right_button = pygame.Rect(x, y, self.transform_button_size, self.transform_button_size)
        self.rotate_left_button = pygame.Rect(x, y + 80, self.transform_button_size, self.transform_button_size)
        self.flip_button = pygame.Rect(x, y + 160, self.transform_button_size, self.transform_button_size)

        # Set title depending on mode
        if self.network_mode:
            title_text = "Select Board for Network Game"
        else:
            title_text = "Square Editor"
        
        self.title_surface = self.title_font.render(title_text, True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.get_width() // 2, 40))
        self.top_offset = self.title_rect.bottom + 20
        self.left_offset = (self.get_width() - self.grid_size) // 2

        self.back_button_rect = pygame.Rect(20, 20, 120, 40)
        self.start_button_rect = pygame.Rect(self.get_width() // 2 - 100, self.get_height() - 70, 200, 50)

        # Load predefined squares from file
        self.board_obj.load_from_file("game_data.json")
        self.square_list = self.board_obj.get_square_list()
        self.square_buttons = self.create_square_buttons()

        self.selected_square = None
        self.holding_square = False 
        self.held_square_data = None
        
        # AI toggle checkbox (only for local games)
        self.__ai = False
        self.checkbox_rect = pygame.Rect(20, 220, 20, 20)
        
    def is_board_filled(self):
        # Check if the board has no empty cells (0 means empty)
        for row in self.board:
            for cell in row:
                if cell == 0:
                    return False
        return True

    def create_square_buttons(self):
        buttons = []
        button_width = 150
        button_height = 40
        padding = 10

        total_width = len(self.square_list) * (button_width + padding) - padding
        start_x = (self.get_width() - total_width) // 2
        y = self.top_offset + self.grid_size + 30

        for idx, name in enumerate(self.square_list.keys()):
            x = start_x + idx * (button_width + padding)
            rect = pygame.Rect(x, y, button_width, button_height)
            buttons.append((name, rect))

        return buttons

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            # Quit game on close or ESC
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

            # Left mouse click
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)

            # Keyboard inputs to rotate or flip held square
            elif event.type == pygame.KEYDOWN and self.holding_square:
                if event.key == pygame.K_r:
                    self.rotate_square_right()
                elif event.key == pygame.K_l:
                    self.rotate_square_left()
                elif event.key == pygame.K_f:
                    self.flip_square()

    def handle_click(self, position):
        x, y = position
        square_rect = None

        # Back button clicked
        if self.back_button_rect.collidepoint(x, y):
            self.running = False
            return

        # Place held square on board if click inside board area
        if self.holding_square:
            if self.is_on_board(x, y):
                row = (y - self.top_offset) // self.cell_size
                col = (x - self.left_offset) // self.cell_size
                self.place_square_on_board(row, col)
                self.holding_square = False
                self.held_square_data = None
                return

        # Check if a square button is clicked to select it
        for name, rect in self.square_buttons:
            if rect.collidepoint(position):
                self.selected_square = name
                self.held_square_data = None
                self.holding_square = False
                print(f"Square selected: {name}")
                return

        # If a square is selected, check if clicked inside preview to "hold" it for placement
        if self.selected_square:
            square_cell_size = 40
            square_width = 4 * square_cell_size
            square_offset_x = (self.get_width() - square_width) // 2
            square_offset_y = self.square_buttons[0][1].bottom + 30
            square_rect = pygame.Rect(square_offset_x, square_offset_y, square_width, square_width)

            if square_rect.collidepoint(position):
                self.held_square_data = self.square_list[self.selected_square]
                self.holding_square = True
                print(f"Square attached: {self.selected_square}")
                return
            
        # AI checkbox toggle only in local mode
        if not self.network_mode and self.checkbox_rect.collidepoint(x, y):
            self.__ai = not self.__ai
            return
            
        # Start/Confirm button clicked
        if self.start_button_rect.collidepoint(x, y):
            if self.is_board_filled():
                if self.network_mode:
                    # Network mode: just confirm and exit UI
                    print("[NETWORK] Board selection completed for network game")
                    self.running = False
                    return
                else:
                    # Local mode: prepare and launch selected game mode
                    print("Launching local game")
                    
                    pre_final_board = self.board_obj.create_final_board(self.board)
                    final_board = self.board_obj.add_border_and_corners(pre_final_board)
                    
                    if self.gamemode == 1:
                        katarenga = Katarenga(self.__ai, final_board)
                        katarenga.run()
                    elif self.gamemode == 2:
                        congress = Congress(self.__ai, pre_final_board)
                        congress.run()
                    elif self.gamemode == 3:
                        isolation = Isolation(self.__ai, pre_final_board)
                        isolation.run()
            else:
                print("Board not completely filled.")
                return
            
        if self.rotate_right_button.collidepoint(position) and self.held_square_data != None:
            self.rotate_square_right()
            return

        if self.rotate_left_button.collidepoint(position) and self.held_square_data != None:
            self.rotate_square_left()
            return

        if self.flip_button.collidepoint(position) and self.held_square_data != None :
            self.flip_square()
            return

    def is_on_board(self, x, y):
        # Check if pixel (x,y) is within board grid area
        return (
            self.left_offset <= x < self.left_offset + self.grid_size
            and self.top_offset <= y < self.top_offset + self.grid_size
        )

    def place_square_on_board(self, row, col):
        if self.held_square_data is None:
            return

        # Snap placement to quadrants (0 or 4)
        row = 0 if row < 4 else 4
        col = 0 if col < 4 else 4

        # Place 4x4 square data on board starting at (row, col)
        for i in range(4):
            for j in range(4):
                self.board[row + i][col + j] = self.held_square_data[i][j]

        print(f"Square placed in quadrant ({row}, {col})")

    def rotate_square_right(self):
        # Rotate held square 90 degrees clockwise
        self.held_square_data = self.board_obj.rotate_right(self.held_square_data)
        print("Square rotated right")

    def rotate_square_left(self):
        # Rotate held square 90 degrees counter-clockwise
        self.held_square_data = self.board_obj.rotate_left(self.held_square_data)
        print("Square rotated left")

    def flip_square(self):
        # Flip held square horizontally
        self.held_square_data = self.board_obj.flip_horizontal(self.held_square_data)
        print("Square flipped horizontally")

    def draw(self):
        screen = self.get_screen()
        screen.fill((30, 30, 30))
        screen.blit(self.title_surface, self.title_rect)

        # Draw board grid cells
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(
                    col * self.cell_size + self.left_offset,
                    row * self.cell_size + self.top_offset,
                    self.cell_size,
                    self.cell_size
                )
                color = self.board_ui.get_color_from_board(self.board[row][col] // 10)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)

        # Draw shrortcuts text
        font = pygame.font.SysFont(None, 24)
        shortcuts = ["R : rotate right", "L : rotate left", "F : flip side"]
        for idx, text in enumerate(shortcuts):
            txt = font.render(text, True, (255, 255, 255))
            screen.blit(txt, (10, 100 + idx * 40))

        # Draw back button
        pygame.draw.rect(screen, (70, 70, 70), self.back_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.back_button_rect, 2)
        back_text = self.button_font.render("Back", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button_rect.center))
        
        # Draw start/confirm button (green if ready, gray otherwise)
        is_ready = self.is_board_filled()
        button_color = (0, 200, 0) if is_ready else (100, 100, 100)

        pygame.draw.rect(screen, button_color, self.start_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.start_button_rect, 2)

        if self.network_mode:
            start_text = self.button_font.render("Confirm Board", True, (255, 255, 255))
        else:
            start_text = self.button_font.render("Launch Game", True, (255, 255, 255))
        screen.blit(start_text, start_text.get_rect(center=self.start_button_rect.center))

        # Draw square buttons for selection
        for name, rect in self.square_buttons:
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 1)
            text_surface = self.button_font.render(name, True, (255, 255, 255))
            screen.blit(text_surface, text_surface.get_rect(center=rect.center))

        # Draw preview of selected square if any
        if self.selected_square:
            preview_size = 40
            preview_width = 4 * preview_size
            preview_x = (self.get_width() - preview_width) // 2
            preview_y = self.square_buttons[0][1].bottom + 30

            preview_rect = pygame.Rect(preview_x, preview_y, preview_width, preview_width)
            pygame.draw.rect(screen, (50, 50, 50), preview_rect)
            pygame.draw.rect(screen, (255, 255, 255), preview_rect, 1)

            square_data = self.square_list[self.selected_square]

            for i in range(4):
                for j in range(4):
                    cell_val = square_data[i][j]
                    color = self.board_ui.get_color_from_board(cell_val // 10)
                    cell_rect = pygame.Rect(
                        preview_x + j * preview_size,
                        preview_y + i * preview_size,
                        preview_size,
                        preview_size
                    )
                    pygame.draw.rect(screen, color, cell_rect)
                    pygame.draw.rect(screen, (255, 255, 255), cell_rect, 1)

        # Draw held square next to mouse if any
        if self.holding_square and self.held_square_data:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            preview_size = 30
            for i in range(4):
                for j in range(4):
                    cell_val = self.held_square_data[i][j]
                    color = self.board_ui.get_color_from_board(cell_val // 10)
                    cell_rect = pygame.Rect(
                        mouse_x + j * preview_size,
                        mouse_y + i * preview_size,
                        preview_size,
                        preview_size
                    )
                    pygame.draw.rect(screen, color, cell_rect)
                    pygame.draw.rect(screen, (255, 255, 255), cell_rect, 1)

        # Draw AI toggle checkbox (only in local mode)
        if not self.network_mode:
            pygame.draw.rect(screen, (255, 255, 255), self.checkbox_rect, 2)
            if self.__ai:
                pygame.draw.line(screen, (0, 255, 0), self.checkbox_rect.topleft, self.checkbox_rect.bottomright, 3)
                pygame.draw.line(screen, (0, 255, 0), self.checkbox_rect.topright, self.checkbox_rect.bottomleft, 3)
            ai_text = self.button_font.render("Play vs AI", True, (255, 255, 255))
            screen.blit(ai_text, (self.checkbox_rect.right + 10, self.checkbox_rect.top - 2))

        #pygame.draw.rect(screen, (70, 70, 70), self.rotate_right_button)
        pygame.draw.rect(screen, (70, 70, 70), self.rotate_left_button)
        pygame.draw.rect(screen, (70, 70, 70), self.flip_button)

        pygame.draw.rect(screen, (255, 255, 255), self.rotate_right_button, 2)
        pygame.draw.rect(screen, (255, 255, 255), self.rotate_left_button, 2)
        pygame.draw.rect(screen, (255, 255, 255), self.flip_button, 2)

        font = pygame.font.SysFont(None, 24)
        label_r = font.render("R", True, (255, 255, 255))
        label_l = font.render("L", True, (255, 255, 255))
        label_f = font.render("F", True, (255, 255, 255))

        screen.blit(label_r, label_r.get_rect(center=self.rotate_right_button.center))
        screen.blit(label_l, label_l.get_rect(center=self.rotate_left_button.center))
        screen.blit(label_f, label_f.get_rect(center=self.flip_button.center))
