import pygame

# Base class for UI screens to avoid repeating common UI logic (screen, font, background, etc.)
class BaseUI:
    def __init__(self, title="Katarenga"):
        pygame.init()

        self.__title = title
        self.__screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Fullscreen mode
        pygame.display.set_caption(self.__title)

        display_info = pygame.display.Info()
        self.__width = display_info.current_w
        self.__height = display_info.current_h

        self.clock = pygame.time.Clock()  # Frame limiter
        self.running = True

        self.font = pygame.font.SysFont(None, 48)  # Default UI font

        self.background_surface = self.create_blue_gradient_background()  # Precomputed background

    def get_screen(self):
        return self.__screen

    def get_width(self):
        return self.__width

    def get_height(self):
        return self.__height

    def get_background(self):
        return self.background_surface

    # Creates a radial blue gradient for the background
    def create_blue_gradient_background(self):
        width, height = self.__width, self.__height
        surface = pygame.Surface((width, height))
        center_x, center_y = width // 2, height // 2
        max_dist = (center_x ** 2 + center_y ** 2) ** 0.5

        for y in range(height):
            for x in range(width):
                dx, dy = x - center_x, y - center_y
                dist = (dx ** 2 + dy ** 2) ** 0.5
                ratio = dist / max_dist

                # Gradient from light blue center to darker edges
                r = int((1 - ratio) * 100 + ratio * 10)
                g = int((1 - ratio) * 149 + ratio * 20)
                b = int((1 - ratio) * 237 + ratio * 60)

                surface.set_at((x, y), (r, g, b))

        return surface