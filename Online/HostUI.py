import pygame
from UI_tools.BaseUi import BaseUI
from Online.NetworkManager import NetworkManager
from Online.GameSession import GameSession
from Editor.Square_selector.SquareSelectorUi import SquareSelectorUi
from Online.NetworkGameAdapter import NetworkGameAdapter
import copy
import time
class HostUI(BaseUI):

    def __init__(self, title="Host Game"):
        super().__init__(title)
        
        self.network = NetworkManager()
        self.session = None
        self.selected_game = None
        
        self.server_started = False
        self.client_connected = False
        self.waiting_for_client = False
        self.board_selected = False
        
        self.title_font = pygame.font.SysFont(None, 48)
        self.button_font = pygame.font.SysFont(None, 36)
        self.info_font = pygame.font.SysFont(None, 24)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.title_surface = self.title_font.render("Host game", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.get_width() // 2, 80))
        
        self.back_button = pygame.Rect(20, 20, 120, 40)
        
        self.game_buttons = []
        games = [
            ("Katarenga", (70, 130, 180), 1),
            ("Congress", (60, 179, 113), 2),
            ("Isolation", (220, 20, 60), 3)
        ]
        
        button_width = 250
        button_height = 60
        spacing = 30
        start_y = 200
        center_x = self.get_width() // 2 - button_width // 2
        
        for i, (name, color, game_id) in enumerate(games):
            rect = pygame.Rect(center_x, start_y + i * (button_height + spacing), button_width, button_height)
            self.game_buttons.append({
                'name': name,
                'color': color,
                'game_id': game_id,
                'rect': rect
            })
        
        # Button for starting the server
        self.start_server_button = pygame.Rect(center_x, start_y + len(games) * (button_height + spacing) + 50, button_width, button_height)
        
        # Button for board selection (visible only when client is connected)
        self.select_board_button = pygame.Rect(center_x, start_y + len(games) * (button_height + spacing) + 130, button_width, button_height)
        
        self.info_y = self.get_height() - 200
    
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
    
    def handle_click(self, pos):
        if self.back_button.collidepoint(pos):
            self.running = False
            return
        
        if not self.server_started:
            # Game selection
            for button in self.game_buttons:
                if button['rect'].collidepoint(pos):
                    self.selected_game = button['game_id']
                    print(f"Game selected: {button['name']}")
                    return
            
            # Start server
            if self.start_server_button.collidepoint(pos) and self.selected_game:
                self.start_server()
        
        elif self.client_connected and not self.board_selected:
            # Board selection
            if self.select_board_button.collidepoint(pos):
                self.launch_board_selection()
    
    def start_server(self):
        if self.network.start_server():
            self.server_started = True
            self.waiting_for_client = True
            
            self.network.set_callbacks(
                message_callback=self.handle_network_message,
                disconnect_callback=self.handle_client_disconnect
            )
        else:
            pass
    
    def handle_network_message(self, message):
        # First message = client connected
        if not self.client_connected:
            self.client_connected = True
            self.waiting_for_client = False
            
            # Send confirmation to client
            if hasattr(self, 'network') and self.network:
                self.network.send_message("HOST_READY")
    
    def handle_client_disconnect(self):
        self.client_connected = False
        self.waiting_for_client = True
        self.board_selected = False
    
    def launch_board_selection(self):
        # Create game session
        self.session = GameSession(self.selected_game, self.network)
        
        # Launch board selection in NETWORK MODE
        selector = SquareSelectorUi(self.selected_game, network_mode=True)
        selector.run()
        
        # Get the created board
        if hasattr(selector, 'board') and selector.is_board_filled():
            self.board_selected = True
            
            # Prepare board according to game type
            if self.selected_game == 1:  # Katarenga
                pre_final_board = selector.board_obj.create_final_board(selector.board)
                final_board = selector.board_obj.add_border_and_corners(pre_final_board)
                # Place pawns for Katarenga
                final_board = self._place_pawns_katarenga(final_board)
                
            elif self.selected_game == 2:  # Congress
                # Pour Congress, utiliser directement le plateau 8x8 sans borders
                final_board = selector.board_obj.create_final_board(selector.board)
                # Place pawns for Congress
                final_board = self._place_pawns_congress(final_board)
                
            elif self.selected_game == 3:  # Isolation
                final_board = selector.board_obj.create_final_board(selector.board)
                # No pawn placement require for Isolation
            
            # Send board to client
            self.session.set_board(final_board)
            
            # Wait a moment for board to be sent
            time.sleep(0.5)
            
            # Launch network game
            self.launch_network_game()
        else:
            self.board_selected = False
    
    def launch_network_game(self):
        if self.session and self.board_selected:
            # Close host interface BEFORE launching game
            self.running = False
            
            # Create and launch network game adapter
            network_game = NetworkGameAdapter(self.session)
            network_game.run()
    
    def _place_pawns_katarenga(self, board):
        new_board = copy.deepcopy(board)
        
        # First row, columns 1 to 8 (top of the board) - Player 2
        for col in range(1, 9):
            if col < len(new_board[0]):
                color = new_board[1][col] // 10
                new_board[1][col] = color * 10 + 2  # Player 2
        
        # Last row, columns 1 to 8 - Player 1
        for col in range(1, 9):
            if col < len(new_board[0]) and len(new_board) > 8:
                color = new_board[8][col] // 10
                new_board[8][col] = color * 10 + 1  # Player 1
        
        return new_board
    
    def _place_pawns_congress(self, board):
        """Place pawns for Congress on 8x8 board"""
        new_board = copy.deepcopy(board)
        grid_dim = len(new_board)  # Should be 8 for Congress
        
        # Clean board first
        for i in range(grid_dim):
            for j in range(grid_dim):
                color_code = new_board[i][j] // 10
                new_board[i][j] = color_code * 10
        
        # Positions directes pour plateau 8x8 (sans décalage)
        black_pawns = [(0, 1), (0, 4), (1, 7), (3, 0), (4, 7), (6, 0), (7, 3), (7, 6)]
        white_pawns = [(0, 3), (0, 6), (1, 0), (3, 7), (4, 0), (6, 7), (7, 1), (7, 4)]
        
        # Place black pawns (Player 2)
        for r, c in black_pawns:
            if r < grid_dim and c < grid_dim:
                color = new_board[r][c] // 10
                new_board[r][c] = color * 10 + 2  # Player 2
        
        # Place white pawns (Player 1) 
        for r, c in white_pawns:
            if r < grid_dim and c < grid_dim:
                color = new_board[r][c] // 10
                new_board[r][c] = color * 10 + 1  # Player 1
        
        return new_board
    
    def draw(self):
        screen = self.get_screen()
        screen.fill((30, 30, 30))
        
        screen.blit(self.title_surface, self.title_rect)
        
        pygame.draw.rect(screen, (70, 70, 70), self.back_button)
        pygame.draw.rect(screen, (255, 255, 255), self.back_button, 2)
        back_text = self.button_font.render("Back", True, (255, 255, 255))
        screen.blit(back_text, back_text.get_rect(center=self.back_button.center))
        
        if not self.server_started:
            self.draw_game_selection(screen)
        else:
            self.draw_server_status(screen)
    
    def draw_game_selection(self, screen):
        for button in self.game_buttons:
            color = button['color']
            if self.selected_game == button['game_id']:
                # Highlight selected game
                pygame.draw.rect(screen, (255, 255, 255), button['rect'], 3)
            
            pygame.draw.rect(screen, color, button['rect'])
            pygame.draw.rect(screen, (255, 255, 255), button['rect'], 2)
            
            text = self.button_font.render(button['name'], True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=button['rect'].center))
        
        # Button for starting the server
        button_color = (100, 255, 100) if self.selected_game else (100, 100, 100)
        pygame.draw.rect(screen, button_color, self.start_server_button)
        pygame.draw.rect(screen, (255, 255, 255), self.start_server_button, 2)
        
        start_text = self.button_font.render("Start Server", True, (255, 255, 255))
        screen.blit(start_text, start_text.get_rect(center=self.start_server_button.center))
        
        # Instructions
        if not self.selected_game:
            instruction = "Select a game to host and click 'Start Server'"
        else:
            instruction = f"Game selected: {[b['name'] for b in self.game_buttons if b['game_id'] == self.selected_game][0]}"
        
        inst_surface = self.info_font.render(instruction, True, (200, 200, 200))
        screen.blit(inst_surface, (50, self.info_y))
    
    def update(self):
        pass
    
    def draw_server_status(self, screen):
        status = self.network.get_status()
        
        # Server information
        info_texts = [
            f"Server running on: {status['local_ip']}:5000",
            f"Connected clients: {status['clients_count']}/1"
        ]
        
        if self.waiting_for_client:
            info_texts.append("Waiting for client to connect...")
            status_color = (255, 255, 100)
        elif self.client_connected and not self.board_selected:
            info_texts.append("Player connected - Ready to select board")
            status_color = (100, 255, 100)
            
            # Display board selection button
            pygame.draw.rect(screen, (100, 255, 100), self.select_board_button)
            pygame.draw.rect(screen, (255, 255, 255), self.select_board_button, 2)
            board_text = self.button_font.render("Select Board", True, (255, 255, 255))
            screen.blit(board_text, board_text.get_rect(center=self.select_board_button.center))
            
        elif self.board_selected:
            info_texts.append("Game in progress...")
            status_color = (100, 255, 100)
        else:
            info_texts.append("No client connected")
            status_color = (255, 100, 100)
        
        # Print information texts
        for i, text in enumerate(info_texts):
            color = status_color if i == len(info_texts) - 1 else (255, 255, 255)
            surface = self.info_font.render(text, True, color)
            screen.blit(surface, (50, self.info_y + i * 30))

if __name__ == "__main__":
    app = HostUI()
    app.run()