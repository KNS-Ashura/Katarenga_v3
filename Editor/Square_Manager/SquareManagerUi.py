import pygame
from Board.Board import Board
from Board.Board_draw_tools import Board_draw_tools
from UI_tools.BaseUi import BaseUI

class SquareManagerUi(BaseUI):
    def __init__(self, title="Square Manager"):
        super().__init__(title)

        self.board_obj = Board()
        self.board_ui = Board_draw_tools()
        self.board_obj.load_from_file("game_data.json")  # Load squares data from file
        self.square_list = self.board_obj.get_square_list()

        self.screen_w = self.get_width()
        self.screen_h = self.get_height()

        self.button_font = pygame.font.SysFont(None, 36)
        self.button_width = 220
        self.button_height = 60
        self.button_padding = 15

        self.list_y = self.screen_h // 2 + 50  # Y position for square buttons
        self.square_buttons = self.create_square_buttons()

        self.selected_square_name = None
        self.selected_square_data = None
        self.square_attached_to_mouse = False  # Track if square is being dragged

        largeur = 150
        hauteur = 150

        # Red box rect for deleting squares
        self.red_box_rect = pygame.Rect(
            self.screen_w // 2 - (largeur // 2),
            self.screen_h - 80 - hauteur,
            largeur,
            hauteur
        )

        self.cell_size = 60

        self.back_button_rect = pygame.Rect(20, 20, 100, 40)  # Back button rect

        # Position where selected square is displayed
        self.square_display_pos = (self.screen_w // 2 - 2 * self.cell_size, 240)
        
    def create_square_buttons(self):
        buttons = []
        square_names = list(self.square_list.keys())[4:]  # Skip first 4 squares

        # Calculate start X to center buttons horizontally
        total_width = len(square_names) * (self.button_width + self.button_padding) - self.button_padding
        start_x = (self.screen_w - total_width) // 2

        # Create buttons for each square
        for idx, name in enumerate(square_names):
            rect = pygame.Rect(
                start_x + idx * (self.button_width + self.button_padding),
                self.list_y,
                self.button_width,
                self.button_height
            )
            buttons.append((name, rect))
        return buttons

    def run(self):
        # Main loop
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.handle_release(event.pos)

    def handle_click(self, pos):
        x, y = pos

        # Click on back button closes app
        if self.back_button_rect.collidepoint(pos):
            self.running = False
            return

        # If a square is selected and not dragged yet, check if clicked inside it to start dragging
        if self.selected_square_data and not self.square_attached_to_mouse:
            square_rect = pygame.Rect(
                self.square_display_pos[0],
                self.square_display_pos[1],
                4 * self.cell_size,
                4 * self.cell_size
            )
            if square_rect.collidepoint(pos):
                self.square_attached_to_mouse = True
                return

        # Check if a square button is clicked — select it
        for name, rect in self.square_buttons:
            if rect.collidepoint(pos):
                self.selected_square_name = name
                self.selected_square_data = self.square_list[name]
                self.square_attached_to_mouse = False
                return

    def handle_release(self, pos):
        # On mouse release, if dragging a square and released over red box — delete square
        if self.square_attached_to_mouse:
            if self.red_box_rect.collidepoint(pos):
                self.delete_square()
                self.selected_square_data = None
                self.selected_square_name = None
            self.square_attached_to_mouse = False
            
    def delete_square(self):
        # Remove selected square from both local and board's list, save changes, update buttons
        if self.selected_square_name in self.square_list:
            del self.square_list[self.selected_square_name]

            square_list_obj = self.board_obj.get_square_list()
            if self.selected_square_name in square_list_obj:
                del square_list_obj[self.selected_square_name]

            self.board_obj.save_to_file_manager("game_data.json")

            self.square_buttons = self.create_square_buttons()

            print(f"Square '{self.selected_square_name}' deleted.")

    def draw(self):
        screen = self.get_screen()
        screen.fill((30, 30, 30))

        # Draw back button
        pygame.draw.rect(screen, (50, 100, 200), self.back_button_rect)
        label_back = self.button_font.render("Back", True, (255, 255, 255))
        screen.blit(label_back, label_back.get_rect(center=self.back_button_rect.center))

        # Draw all square buttons
        for name, rect in self.square_buttons:
            pygame.draw.rect(screen, (70, 70, 70), rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2)
            label = self.button_font.render(name, True, (255, 255, 255))
            screen.blit(label, label.get_rect(center=rect.center))

        # Draw red DELETE box
        pygame.draw.rect(screen, (180, 30, 30), self.red_box_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.red_box_rect, 3)
        label_delete = self.button_font.render("DELETE", True, (255, 255, 255))
        screen.blit(label_delete, label_delete.get_rect(center=self.red_box_rect.center))

        # Draw selected square grid, either at fixed position or following mouse when dragged
        if self.selected_square_data:
            if self.square_attached_to_mouse:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                top_left_x = mouse_x - 2 * self.cell_size
                top_left_y = mouse_y - 2 * self.cell_size
            else:
                top_left_x, top_left_y = self.square_display_pos

            for row in range(4):
                for col in range(4):
                    rect = pygame.Rect(
                        top_left_x + col * self.cell_size,
                        top_left_y + row * self.cell_size,
                        self.cell_size,
                        self.cell_size
                    )
                    value = self.selected_square_data[row][col]
                    color = self.board_ui.get_color_from_board(value // 10)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (255, 255, 255), rect, 1)

if __name__ == "__main__":
    app = SquareManagerUi()
    app.run()
