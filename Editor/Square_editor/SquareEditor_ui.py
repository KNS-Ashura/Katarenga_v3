import pygame
import sys

from Board.Board import Board
from Board.Board_draw_tools import Board_draw_tools
from UI_tools.BaseUi import BaseUI

class SquareEditorUi(BaseUI):
    def __init__(self, title="Square A Editor"):
        super().__init__(title)

        self.board_obj = Board()
        self.board_ui = Board_draw_tools()
        self.square = self.board_obj.get_default_square()

        self.cell_size = 100
        self.grid_size = self.cell_size * 4

        screen_width = self.get_width()

        # Title setup
        self.title_font = pygame.font.SysFont(None, 48)
        self.title_surface = self.title_font.render("Square Editor", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(screen_width // 2, 30))

        self.rule_font = pygame.font.SysFont(None, 24)
        self.rule_surface = self.rule_font.render(
            "Every square must contain four case with each color :" \
            " green ,red ,blue, yellow", True, (200, 200, 200)
        )
        self.rule_rect = self.rule_surface.get_rect(topright=(screen_width - 20, self.title_rect.bottom + 10))

        # Position offsets
        self.top_offset = self.title_rect.bottom + 40
        self.left_offset = (screen_width - self.grid_size) // 2

        self.button_font = pygame.font.SysFont(None, 36)

        # Back button rect
        self.back_button_rect = pygame.Rect(20, 20, 120, 40)

        # Text input box rect
        self.text_input_rect = pygame.Rect(self.left_offset, self.top_offset + self.grid_size + 20, self.grid_size, 40)
        self.text_input = ""
        self.text_active = False

        # Save button rect
        self.save_button_rect = pygame.Rect(self.left_offset, self.text_input_rect.bottom + 10, self.grid_size, 40)

    def run(self):
        # Main loop
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        # Handle events (quit, keypress, mouse click)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.text_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.text_input = self.text_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.text_active = False
                    else:
                        self.text_input += event.unicode

    def handle_click(self, position):
        x, y = position

        # Back button clicked: exit
        if self.back_button_rect.collidepoint(x, y):
            self.running = False
            return

        if self.save_button_rect.collidepoint(x, y):
            if self.text_input.strip() == "":
                print("Error: You must enter a name before saving.")
                return

            color_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            for row in self.square:
                for cell in row:
                    color = cell // 10
                    if color in color_counts:
                        color_counts[color] += 1

            if all(count >= 4 for count in color_counts.values()):
                print("Save pressed")
                self.board_obj.set_square_list(self.text_input, self.square)
                filename = "game_data.json"
                self.board_obj.check_or_create_file(filename)
                self.board_obj.save_to_file(filename)
                self.running = False
            else:
                return

        # Calculate clicked cell in grid
        col = (x - self.left_offset) // self.cell_size
        row = (y - self.top_offset) // self.cell_size

        # If click is inside the 4x4 grid
        if 0 <= row < 4 and 0 <= col < 4:
            value = self.square[row][col]
            color_code = value // 10
            print(f"Clicked cell ({row}, {col}): Value {value}, Color {color_code}")

            # Cycle color code (1 to 4)
            new_color_code = (color_code % 4) + 1
            self.square[row][col] = new_color_code * 10 + (value % 10)
            print(f"Updated board: {self.square}")

        # Activate text input if clicked inside input box
        if self.text_input_rect.collidepoint(x, y):
            self.text_active = True

    def draw(self):
        screen = self.get_screen()
        screen.fill((30, 30, 30))

        # Draw title
        screen.blit(self.title_surface, self.title_rect)

        screen.blit(self.rule_surface, self.rule_rect)

        # Draw 4x4 grid of squares
        for row in range(4):
            for col in range(4):
                rect = pygame.Rect(
                    col * self.cell_size + self.left_offset,
                    row * self.cell_size + self.top_offset,
                    self.cell_size,
                    self.cell_size
                )
                color = self.board_ui.get_color_from_board(self.square[row][col] // 10)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)

        # Draw back button
        pygame.draw.rect(screen, (70, 70, 70), self.back_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.back_button_rect, 2)
        back_text = self.button_font.render("Retour", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button_rect.center))

        # Draw save button
        pygame.draw.rect(screen, (70, 70, 70), self.save_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.save_button_rect, 2)
        save_text = self.button_font.render("Sauvegarder", True, (255, 255, 255))
        screen.blit(save_text, save_text.get_rect(center=self.save_button_rect.center))

        # Draw text input box and current text
        pygame.draw.rect(screen, (255, 255, 255), self.text_input_rect, 2)
        text_surface = pygame.font.SysFont(None, 36).render(self.text_input, True, (255, 255, 255))
        screen.blit(text_surface, (self.text_input_rect.x + 5, self.text_input_rect.y + 5))


if __name__ == "__main__":
    board = Board()
    app = SquareEditorUi()
    app.run()