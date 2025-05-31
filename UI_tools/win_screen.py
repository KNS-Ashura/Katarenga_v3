
from UI_tools.BaseUi import BaseUI

import pygame
import sys
import random

class WinScreen(BaseUI):
    def __init__(self, player_name):
        super().__init__(title="Victory")
        self.__player = player_name

        # Fonts
        self.button_font = pygame.font.SysFont(None, 36)
        self.title_font = pygame.font.SysFont(None, 72)
        self.text_font = pygame.font.SysFont(None, 48)

        # Buttons
        self.buttons = {
            "menu": pygame.Rect(self.get_width() // 2 - 100, self.get_height() // 2 + 50, 200, 50),
            "quit": pygame.Rect(self.get_width() // 2 - 100, self.get_height() // 2 + 120, 200, 50),
        }

        # Limited color palette (4 specific colors)
        self.allowed_colors = [
            (100, 160, 230),   # Blue
            (125, 190, 155),   # Green
            (240, 200, 80),    # Yellow
            (235, 115, 115)    # Red
        ]

        # Generate floating squares
        self.squares = []
        for _ in range(80):
            size = random.randint(40, 80)
            x = random.randint(0, self.get_width() - size)
            y = random.randint(0, self.get_height() - size)
            dx = random.uniform(-0.2, 0.2)
            dy = random.uniform(-0.2, 0.2)
            color = random.choice(self.allowed_colors)  # Only use allowed colors
            self.squares.append({"x": x, "y": y, "size": size, "dx": dx, "dy": dy, "color": color})

        self.mainloop()

    def draw(self):
        screen = self.get_screen()

        # Draw background
        screen.blit(self.get_background(), (0, 0))


        # Update and draw moving background squares
        for square in self.squares:
            square["x"] += square["dx"]
            square["y"] += square["dy"]

            # Bounce off edges
            if square["x"] < 0 or square["x"] + square["size"] > self.get_width():
                square["dx"] *= -1
            if square["y"] < 0 or square["y"] + square["size"] > self.get_height():
                square["dy"] *= -1

            pygame.draw.rect(
                screen,
                square["color"],
                pygame.Rect(int(square["x"]), int(square["y"]), square["size"], square["size"])
            )

        # Draw victory title
        title_surf = self.title_font.render("Victory", True, (255, 255, 255))
        screen.blit(title_surf, (self.get_width() // 2 - title_surf.get_width() // 2, 100))

        # Display the winner's name
        winner_text = f"The winner is: {self.__player}"
        winner_surf = self.text_font.render(winner_text, True, (255, 255, 255))
        screen.blit(winner_surf, (self.get_width() // 2 - winner_surf.get_width() // 2, 200))

        # Draw buttons
        for key, rect in self.buttons.items():
            pygame.draw.rect(screen, (255, 255, 255), rect)  # Button background
            pygame.draw.rect(screen, (21, 87, 36), rect, 2)   # Button border

            label = "Return to Menu" if key == "menu" else "Quit Game"
            text_surf = self.button_font.render(label, True, (21, 87, 36))
            screen.blit(
                text_surf,
                (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2)
            )

        pygame.display.flip()

    def mainloop(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.buttons["menu"].collidepoint(mouse_pos):
                        print("Returning to menu...")
                        self.running = False
                    elif self.buttons["quit"].collidepoint(mouse_pos):
                        print("Game exited.")
                        pygame.quit()
                        sys.exit()

            self.draw()
            self.clock.tick(60)  # Limit to 60 FPS