import pygame
import sys
from Editor.EditorMenu import EditorMenu
from UI_tools.BaseUi import BaseUI
from Editor.Square_selector.SquareSelectorUi import SquareSelectorUi
from Online.HostUI import HostUI
from Online.JoinUI import JoinUI

class MainMenuUI(BaseUI):
    def __init__(self, title="Katarenga"):
        super().__init__(title)

        # Main button layout setup
        btn_width = 300
        btn_height = 80
        spacing = 40
        num_buttons = 5

        total_height = num_buttons * btn_height + (num_buttons - 1) * spacing
        start_y = (self.get_height() - total_height) // 2
        x_center = (self.get_width() - btn_width) // 2

        labels_colors = [
            ("Katarenga", (70, 130, 180)),
            ("Congress", (60, 179, 113)),
            ("Isolation", (220, 20, 60)),
            ("Board Editor", (255, 140, 0)),
            ("Leave Game", (186, 85, 211))
        ]

        self.buttons = []
        for i, (label, color) in enumerate(labels_colors):
            rect = pygame.Rect(x_center, start_y + i * (btn_height + spacing), btn_width, btn_height)
            self.buttons.append({"label": label, "rect": rect, "color": color})

        # Side buttons (Host/Join)
        side_x = 80
        side_btn_width = 200
        side_spacing = 120
        side_total_height = 2 * btn_height + side_spacing
        side_y = (self.get_height() - side_total_height) // 2

        self.buttons.append({
            "label": "Host a game",
            "rect": pygame.Rect(side_x, side_y, side_btn_width, btn_height),
            "color": (100, 149, 237)
        })

        self.buttons.append({
            "label": "Join a game",
            "rect": pygame.Rect(side_x, side_y + btn_height + side_spacing, side_btn_width, btn_height),
            "color": (72, 209, 204)
        })

        self.info_font = pygame.font.SysFont(None, 24)

    def run(self):
        # Main loop
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_events(self):
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def handle_click(self, position):
        # Button click logic
        for button in self.buttons:
            if button["rect"].collidepoint(position):
                label = button["label"]
                print(f"Launching {label}...")

                if label == "Katarenga":
                    self.launch_square_selector(1)
                elif label == "Congress":
                    self.launch_square_selector(2)
                elif label == "Isolation":
                    self.launch_square_selector(3)
                elif label == "Board Editor":
                    self.launch_editor_menu()
                elif label == "Leave Game":
                    self.running = False
                elif label == "Host a game":
                    self.launch_host_interface()
                elif label == "Join a game":
                    self.launch_join_interface()

    def launch_square_selector(self, gamemode):
        
        try:
            selector = SquareSelectorUi(gamemode)
            # Integrated into our main loop
            while selector.running and self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        selector.running = False
                        self.running = False
                        break
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        selector.running = False
                        break
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        selector.handle_click(event.pos)
                    elif event.type == pygame.KEYDOWN and selector.holding_square:
                        if event.key == pygame.K_r:
                            selector.rotate_square_right()
                        elif event.key == pygame.K_l:
                            selector.rotate_square_left()
                        elif event.key == pygame.K_f:
                            selector.flip_square()

                selector.draw()
                pygame.display.flip()
                selector.clock.tick(60)

        except Exception as e:
            print(f"Error launching selector: {e}")

    def launch_editor_menu(self):
        """✅ Launch board editor menu in integrated mode"""
        try:
            editor = EditorMenu()
            while editor.running and self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        editor.running = False
                        self.running = False
                        break
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        editor.running = False
                        break
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        editor.handle_click(event.pos)

                editor.draw()
                pygame.display.flip()
                editor.clock.tick(60)

        except Exception as e:
            print(f"Error launching editor: {e}")

    def launch_host_interface(self):
        """✅ Launch host interface in integrated mode"""
        try:
            host_interface = HostUI()
            while host_interface.running and self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        host_interface.running = False
                        self.running = False
                        break
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        host_interface.running = False
                        break
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        host_interface.handle_click(event.pos)

                host_interface.update()
                host_interface.draw()
                pygame.display.flip()
                host_interface.clock.tick(60)

        except Exception as e:
            print(f"Error launching host interface: {e}")

    def launch_join_interface(self):
        """✅ Launch join interface in integrated mode"""
        try:
            join_interface = JoinUI()
            while join_interface.running and self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        join_interface.running = False
                        self.running = False
                        break
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            join_interface.running = False
                            break
                        elif join_interface.ip_active:
                            join_interface.handle_text_input(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        join_interface.handle_click(event.pos)

                join_interface.update()
                join_interface.draw()
                pygame.display.flip()
                join_interface.clock.tick(60)

        except Exception as e:
            print(f"Error during join interface: {e}")

    def draw(self):
        # Drawing buttons
        self.get_screen().blit(self.get_background(), (0, 0))
        for button in self.buttons:
            pygame.draw.rect(self.get_screen(), button["color"], button["rect"], border_radius=12)
            self.draw_text(button["label"], button["rect"])

    def draw_text(self, text, rect):
        # Centered text rendering
        txt_surface = self.font.render(text, True, (255, 255, 255))
        txt_rect = txt_surface.get_rect(center=rect.center)
        self.get_screen().blit(txt_surface, txt_rect)

if __name__ == "__main__":
    # App launch
    app = MainMenuUI()
    app.run()