# Online/JoinUI.py
import pygame
import threading
from UI_tools.BaseUi import BaseUI
from Online.NetworkManager import NetworkManager
from Online.GameSession import GameSession
from Online.NetworkGameAdapter import NetworkGameAdapter

class JoinUI(BaseUI):
    
    def __init__(self, title="Join a game"):
        super().__init__(title)
        
        self.network = NetworkManager()
        self.session = None
        
        self.connected = False
        self.connecting = False
        self.board_received = False
        self.game_started = False
        
        self.ip_text = "127.0.0.1"
        self.ip_active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        
        self.status_message = ""
        self.status_color = (255, 255, 255)
        
        self.title_font = pygame.font.SysFont(None, 48)
        self.button_font = pygame.font.SysFont(None, 36)
        self.input_font = pygame.font.SysFont(None, 32)
        self.info_font = pygame.font.SysFont(None, 24)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.title_surface = self.title_font.render("Join a game", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.get_width() // 2, 80))
        
        self.back_button = pygame.Rect(20, 20, 120, 40)
        
        center_x = self.get_width() // 2
        center_y = self.get_height() // 2
        
        self.ip_input_rect = pygame.Rect(center_x - 200, center_y - 100, 400, 50)
        self.connect_button = pygame.Rect(center_x - 100, center_y - 30, 200, 50)
        
        # Button to launch game (visible when board is received)
        self.start_game_button = pygame.Rect(center_x - 100, center_y + 30, 200, 50)
        
        self.info_y = center_y + 100
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        if self.network:
            self.network.disconnect()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            
            elif event.type == pygame.KEYDOWN and self.ip_active:
                self.handle_text_input(event)
    
    def handle_click(self, pos):
        # Back button
        if self.back_button.collidepoint(pos):
            self.running = False
            return
        
        # IP input zone
        if not self.connected:
            self.ip_active = self.ip_input_rect.collidepoint(pos)
            
            # Connection button
            if self.connect_button.collidepoint(pos) and not self.connecting and not self.connected:
                self.attempt_connection()
        
        # Button to start game
        elif self.board_received and self.start_game_button.collidepoint(pos):
            self.launch_network_game()
    
    def handle_text_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.ip_text = self.ip_text[:-1]
        elif event.key == pygame.K_RETURN:
            if not self.connecting and not self.connected:
                self.attempt_connection()
        elif event.unicode.isprintable() and len(self.ip_text) < 15:
            # Only allow printable characters and limit length for ip adress
            if event.unicode.isdigit() or event.unicode == ".":
                self.ip_text += event.unicode
    
    def attempt_connection(self):
        if not self.ip_text.strip():
            self.set_status("Please enter an IP address", (255, 100, 100))
            return
        
        self.connecting = True
        self.set_status("Connection in progress...", (255, 255, 100))
        
        # Launch connection in separate thread
        threading.Thread(target=self.connect_to_server, daemon=True).start()
    
    def connect_to_server(self):
        if self.network.connect_to_server(self.ip_text.strip()):
            # Connection SUCCESS
            self.connected = True
            self.connecting = False
            self.set_status("Connected! Waiting for board...", (100, 255, 100))
            
            self.network.set_callbacks(
                message_callback=self.handle_network_message,
                disconnect_callback=self.handle_server_disconnect
            )
            
            self.network.send_message("CLIENT_READY")
            
        else:
            self.connecting = False
            self.set_status("Unable to connect", (255, 100, 100))
    
    def handle_network_message(self, message):
        try:
            import json
            data = json.loads(message)
            
            if data.get('type') == 'BOARD_DATA':
                # Reception of board data
                self.board_received = True
                self.session = GameSession(data['game_type'], self.network)
                self.session.set_board(data['board'])
                self.set_status("Board received! Ready to play", (100, 255, 100))
            
            elif data.get('type') == 'GAME_START':
                self.game_started = True
                self.set_status("Game started!", (100, 255, 100))
                # Auto-launch game when host starts
                if self.board_received:
                    self.launch_network_game()

        except json.JSONDecodeError:
            if "READY" in message.upper() or "CLIENT_READY" in message:
                self.set_status("Server ready", (100, 255, 100))
    
    def handle_server_disconnect(self):
        self.connected = False
        self.connecting = False
        self.board_received = False
        self.game_started = False
        self.set_status("Server disconnected", (255, 100, 100))
    
    def launch_network_game(self):
        if self.session and self.board_received:
            # Close join interface BEFORE launching game
            self.running = False
            
            # Create and launch network game adapter
            network_game = NetworkGameAdapter(self.session)
            network_game.run()
    
    def set_status(self, message, color):
        self.status_message = message
        self.status_color = color
    
    def update(self):
        self.cursor_timer += self.clock.get_time()
        if self.cursor_timer >= 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self):
        screen = self.get_screen()
        screen.fill((30, 30, 30))
        
        screen.blit(self.title_surface, self.title_rect)
        
        # Back button
        pygame.draw.rect(screen, (70, 70, 70), self.back_button)
        pygame.draw.rect(screen, (255, 255, 255), self.back_button, 2)
        back_text = self.button_font.render("Back", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button.center))
        
        if not self.connected and not self.game_started:
            self.draw_connection_interface(screen)
        else:
            self.draw_game_interface(screen)
    
    def draw_connection_interface(self, screen):
        # Label for IP input
        label = self.button_font.render("Server IP address:", True, (255, 255, 255))
        label_rect = label.get_rect(centerx=self.get_width() // 2, y=self.ip_input_rect.y - 40)
        screen.blit(label, label_rect)
        
        input_color = (100, 100, 100) if self.ip_active else (70, 70, 70)
        pygame.draw.rect(screen, input_color, self.ip_input_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.ip_input_rect, 2)
        
        text_surface = self.input_font.render(self.ip_text, True, (255, 255, 255))
        text_x = self.ip_input_rect.x + 10
        text_y = self.ip_input_rect.y + (self.ip_input_rect.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))
        
        if self.ip_active and self.cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y1 = text_y + 2
            cursor_y2 = text_y + text_surface.get_height() - 2
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        
        # Connection button
        button_color = (70, 130, 180)
        if self.connecting:
            button_color = (100, 100, 100)
        elif not self.ip_text.strip():
            button_color = (50, 50, 50)
        
        pygame.draw.rect(screen, button_color, self.connect_button)
        pygame.draw.rect(screen, (255, 255, 255), self.connect_button, 2)
        
        button_text = "Connecting..." if self.connecting else "Connect"
        connect_surface = self.button_font.render(button_text, True, (255, 255, 255))
        screen.blit(connect_surface, connect_surface.get_rect(center=self.connect_button.center))
        
        if self.status_message:
            status_surface = self.info_font.render(self.status_message, True, self.status_color)
            status_rect = status_surface.get_rect(centerx=self.get_width() // 2, y=self.info_y)
            screen.blit(status_surface, status_rect)
        
        # Instructions
        instructions = [
            "Enter the IP address of the server",
            "The address should be shown in the host UI",
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surface = self.info_font.render(instruction, True, (200, 200, 200))
            inst_rect = inst_surface.get_rect(centerx=self.get_width() // 2, y=self.info_y + 50 + i * 25)
            screen.blit(inst_surface, inst_rect)
    
    def draw_game_interface(self, screen):
        info_texts = [
            f"Connected to: {self.ip_text}",
            f"Status: {self.status_message}"
        ]
        
        if self.session:
            status = self.session.get_status()
            info_texts.extend([
                f"Game type: {['', 'Katarenga', 'Congress', 'Isolation'][status.get('game_type', 0)]}",
                f"You are player: {status.get('local_player', 2)}"
            ])
        
        start_y = self.get_height() // 2 - len(info_texts) * 15
        for i, text in enumerate(info_texts):
            color = self.status_color if i == 1 else (255, 255, 255)
            surface = self.info_font.render(text, True, color)
            screen.blit(surface, (50, start_y + i * 30))
        
        # Button to manually launch game if not started yet
        if self.board_received and not self.game_started:
            pygame.draw.rect(screen, (100, 255, 100), self.start_game_button)
            pygame.draw.rect(screen, (255, 255, 255), self.start_game_button, 2)
            start_text = self.button_font.render("Join Game", True, (255, 255, 255))
            screen.blit(start_text, start_text.get_rect(center=self.start_game_button.center))
            
            instruction = "Board ready! Click to start game."
        elif self.game_started:
            instruction = "Game in progress!"
        else:
            instruction = "Waiting for board data..."
        
        inst_surface = self.button_font.render(instruction, True, (255, 255, 100))
        inst_rect = inst_surface.get_rect(centerx=self.get_width() // 2, y=start_y + len(info_texts) * 30 + 50)
        screen.blit(inst_surface, inst_rect)

if __name__ == "__main__":
    app = JoinUI()
    app.run()