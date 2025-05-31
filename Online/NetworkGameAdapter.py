import pygame
from UI_tools.BaseUi import BaseUI
from Board.Board_draw_tools import Board_draw_tools
from Game_ui.move_rules import Moves_rules
from UI_tools.win_screen import WinScreen

from Game_ui.Katarenga import Katarenga
from Game_ui.Congress import Congress
from Game_ui.Isolation import Isolation

class NetworkGameAdapter(BaseUI):
    
    def __init__(self, game_session, title="Network Game"):
        super().__init__(title)
        
        # Network game session
        self.session = game_session
        self.board = game_session.board
        self.game_type = game_session.game_type
        self.local_player = 1 if game_session.is_host else 2
        
        # Create an instance of the game to reuse its methods
        self.game_instance = self._create_game_instance()
        
        # Network game state
        self.selected_pawn = None
        self.current_player = 1
        self.game_finished = False
        self.status_message = ""
        self.status_color = (255, 255, 255)
        
        
        # Set up callbacks
        self.session.set_game_callbacks(
            board_update=self.on_board_update,
            player_change=self.on_player_change,
            game_end=self.on_game_end
        )
    
    def _create_game_instance(self):
        ai_disabled = False
        
        if self.game_type == 1:
            return Katarenga(ai_disabled, self.board)
        elif self.game_type == 2:
            # Pour Congress, on utilise le fichier original mais on configure le mode réseau
            congress_instance = Congress(ai_disabled, self.board)
            # Remplacer le plateau généré par celui du réseau
            congress_instance.board = self.board
            congress_instance.base_board = self._extract_base_board(self.board)
            # IMPORTANT: Configurer le mode réseau avec callback
            congress_instance.set_network_mode(True, victory_callback=self._handle_local_victory)
            return congress_instance
        elif self.game_type == 3:
            return Isolation(ai_disabled, self.board)
        else:
            raise ValueError(f"Unknown game type: {self.game_type}")
    
    def _handle_local_victory(self, winner):
        """Callback appelé par Congress quand une victoire est détectée localement"""
        print(f"Victory callback received: Player {winner}")
        # Déclencher immédiatement l'affichage de victoire
        self._trigger_victory(winner)
    
    def _extract_base_board(self, board_with_pawns):
        """Extrait le plateau de base (sans pions) à partir du plateau avec pions"""
        import copy
        base_board = copy.deepcopy(board_with_pawns)
        
        for i in range(len(base_board)):
            for j in range(len(base_board[0])):
                # Garde seulement la couleur de base (retire les pions)
                color_code = base_board[i][j] // 10
                base_board[i][j] = color_code * 10
        
        return base_board
    
    def run(self):
        self.session.start_game()
        
        while self.running and not self.game_finished:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        # Wait for user to close window after game ends
        if self.game_finished:
            waiting_for_close = True
            while waiting_for_close:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        waiting_for_close = False
                
                # Continue drawing the end screen
                self.draw()
                pygame.display.flip()
                self.clock.tick(60)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
    
    def handle_click(self, pos):
        # Check if clicking back button FIRST (should work regardless of turn)
        back_rect = pygame.Rect(20, 20, 120, 40)
        if back_rect.collidepoint(pos):
            self.running = False
            return
            
        # Check if clicking back button (if game instance has one)
        if hasattr(self.game_instance, 'back_button_rect'):
            if self.game_instance.back_button_rect.collidepoint(pos):
                self.running = False
                return
        
        # Check if it's the player's turn for game moves
        if self.current_player != self.local_player:
            self.set_status("It's not your turn", (255, 255, 100))
            return
        
        # Handle game-specific clicks
        if self.game_type in [1, 2]:  # Katarenga and Congress
            self._handle_board_click_katarenga_congress(pos)
        elif self.game_type == 3:  # Isolation
            self._handle_click_isolation(pos)
    
    def _handle_board_click_katarenga_congress(self, pos):
        row, col = self._get_board_position(pos)
        if row is None or col is None:
            return
        
        cell_value = self.board[row][col]
        player_on_cell = cell_value % 10
        
        if self.selected_pawn is None:
            # Selection for pawns but only selecting own pawns
            if player_on_cell == self.local_player:
                self.selected_pawn = (row, col)
                self.set_status(f"Pawn selected at ({row}, {col})", (100, 255, 100))
            elif player_on_cell != 0:
                self.set_status("That's not your pawn!", (255, 100, 100))
            else:
                self.set_status("Select one of your pawns", (255, 255, 100))
        else:
            # Movement or deselection
            if (row, col) == self.selected_pawn:
                self.selected_pawn = None
                self.set_status("Pawn deselected", (200, 200, 200))
            elif player_on_cell == self.local_player:
                # Switch to different own pawn
                self.selected_pawn = (row, col)
                self.set_status(f"New pawn selected at ({row}, {col})", (100, 255, 100))
            else:
                # Try to move to this position
                from_row, from_col = self.selected_pawn
                
                # check if its my own pawn
                if self.board[from_row][from_col] % 10 != self.local_player:
                    self.set_status("Error: Not your pawn!", (255, 100, 100))
                    self.selected_pawn = None
                    return
                
                # Attempt to make move through network
                if self.session.make_move((from_row, from_col), (row, col)):
                    self.selected_pawn = None
                    self.set_status("Move successful", (100, 255, 100))
                else:
                    self.set_status("Invalid move", (255, 100, 100))
    
    def _handle_click_isolation(self, pos):
        row, col = self._get_board_position(pos)
        if row is None or col is None:
            return
        
        # Attempt to place piece through network
        if self.session.make_move(None, (row, col)):
            self.set_status("Piece placed", (100, 255, 100))
            
            # Vérifier immédiatement la victoire après un placement réussi
            self._check_local_victory()
        else:
            self.set_status("Invalid placement", (255, 100, 100))
    
    def _get_board_position(self, pos):
        x, y = pos
        
        if hasattr(self.game_instance, 'left_offset'):
            left_offset = self.game_instance.left_offset
            top_offset = self.game_instance.top_offset
            cell_size = self.game_instance.cell_size
            grid_dim = self.game_instance.grid_dim
        else:
            # Fallback values
            left_offset = (self.get_width() - 600) // 2
            top_offset = 80
            cell_size = 60
            grid_dim = len(self.board)
        
        if not (left_offset <= x < left_offset + grid_dim * cell_size and
                top_offset <= y < top_offset + grid_dim * cell_size):
            return None, None
        
        col = (x - left_offset) // cell_size
        row = (y - top_offset) // cell_size
        
        if 0 <= row < grid_dim and 0 <= col < grid_dim:
            return row, col
        return None, None
    
    def on_board_update(self, new_board):
        self.board = new_board
        self.game_instance.board = new_board  # Sync with game instance
        
        # Pour Congress, on met aussi à jour le base_board
        if self.game_type == 2 and hasattr(self.game_instance, 'base_board'):
            self.game_instance.base_board = self._extract_base_board(new_board)
        
        # Vérifier les conditions de victoire après chaque mise à jour du plateau
        # SEULEMENT pour Katarenga et Isolation (Congress gère via callback)
        if self.game_type in [1, 3]:
            self._check_local_victory()
        
        print("Board updated")
    
    def _check_local_victory(self):
        
        if self.game_finished:
            return
            
        winner = None
        
        if self.game_type == 1:  # Katarenga
            winner = self._check_katarenga_victory()
        elif self.game_type == 3:  # Isolation
            winner = self._check_isolation_victory()
        # Congress est géré via callback, pas ici
        
        if winner:
            print(f"Local victory detected: Player {winner} wins!")
            # Déclencher la fin de partie avec animation
            self._trigger_victory(winner)
    
    def _trigger_victory(self, winner):
        
        self.game_finished = True

        # Déterminer le nom du gagnant
        if winner == self.local_player:
            winner_name = f"Player {self.local_player} (You)"
            self.set_status("You win!", (100, 255, 100))
        else:
            winner_name = f"Player {winner} (Opponent)"
            self.set_status("You lose!", (255, 100, 100))
        
        # Afficher l'écran de victoire après avoir défini le nom
        self.win_screen = WinScreen(winner_name)
            
        

        # Notifier le réseau
        if hasattr(self.session, '_end_game'):
            try:
                self.session._end_game(winner)
            except Exception as e:
                print(f"Error sending victory to network: {e}")

    def _check_katarenga_victory(self):
        """Vérification de victoire pour Katarenga"""
        player1_count = 0
        player2_count = 0
        
        # Compter les pions
        for row in range(len(self.board)):
            for col in range(len(self.board[0])):
                player = self.board[row][col] % 10
                if player == 1:
                    player1_count += 1
                elif player == 2:
                    player2_count += 1
        
        # Victoire par élimination
        if player1_count == 0:
            return 2
        if player2_count == 0:
            return 1
        
        # Victoire par coins (pour plateau 10x10)
        if len(self.board) >= 10 and len(self.board[0]) >= 10:
            # Player 1 gagne s'il occupe les deux coins du bas
            if self.board[9][0] % 10 == 1 and self.board[9][9] % 10 == 1:
                return 1
            # Player 2 gagne s'il occupe les deux coins du haut
            if self.board[0][0] % 10 == 2 and self.board[0][9] % 10 == 2:
                return 2
        
        return None
    
    def _check_isolation_victory(self):
        """Vérification de victoire pour Isolation"""
        # Compter les mouvements total
        total_moves = 0
        for row in range(len(self.board)):
            for col in range(len(self.board[0])):
                if self.board[row][col] % 10 != 0:
                    total_moves += 1
        
        max_moves = len(self.board) * len(self.board[0])
        
        # Jeu terminé si le plateau est plein
        if total_moves >= max_moves:
            return self.current_player  # Dernier joueur à jouer gagne
        
        # Vérifier si le joueur actuel peut encore jouer
        if not self._can_play_isolation(self.current_player):
            # Joueur actuel ne peut pas jouer, l'adversaire gagne
            return 2 if self.current_player == 1 else 1
        
        return None
    
    def _can_play_isolation(self, current_player):
        """Vérifie si le joueur peut encore jouer en Isolation"""
        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                case = self.board[i][j]
                # Ignorer les coins et cases déjà occupées
                if case in (0, 50, 60) or case % 10 != 0:
                    continue
                
                # Vérifier si la case n'est pas "en prise" (sous attaque)
                if not self._is_square_under_attack(i, j):
                    return True
        return False
    
    def _is_square_under_attack(self, x, y):
        """Vérifie si une case est sous attaque"""
        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                case = self.board[i][j]
                if case % 10 != 0:  # Il y a un pion ici
                    try:
                        # Utiliser les règles de mouvement pour vérifier l'attaque
                        if hasattr(self.game_instance, 'moves_rules'):
                            if self.game_instance.moves_rules.verify_move(case, i, j, x, y):
                                return True
                    except:
                        continue
        return False
    
    def on_player_change(self, new_player):
        self.current_player = new_player
        if new_player == self.local_player:
            self.set_status("Your turn", (100, 255, 100))
        else:
            self.set_status("Opponent's turn", (255, 255, 100))
    
    def on_game_end(self, winner):
        
        self.game_finished = True
        if winner == "Disconnection":
            self.set_status("Opponent disconnected - Press Escape to quit", (255, 100, 100))
            if self.local_player == 1:
                WinScreen("Player 1 (You - Opponent disconnected)")
            else:
                WinScreen("Player 2 (You - Opponent disconnected)")
        elif winner == self.local_player:
            self.set_status("You win! Press Escape to quit", (100, 255, 100))
            WinScreen(f"Player {self.local_player} (You)")
        else:
            self.set_status("You lose! Press Escape to quit", (255, 100, 100))
            WinScreen(f"Player {winner} (Opponent)")

    def set_status(self, message, color):
        self.status_message = message
        self.status_color = color

    def update(self):
        if hasattr(self.game_instance, 'update'):
            self.game_instance.update()
    
    def draw(self):
        screen = self.get_screen()

        # Si le jeu est terminé, afficher l'écran de victoire
        if self.game_finished and hasattr(self, 'win_screen'):
            self.win_screen.draw(screen)
            return

        # Sinon, afficher normalement le jeu
        if hasattr(self.game_instance, 'draw'):
            self._draw_using_game_instance(screen)
        else:
            self._draw_basic(screen)

        # Infos réseau
        self._draw_network_info(screen)
    
    def _draw_using_game_instance(self, screen):
        # Temporarily modify game instance state
        original_screen = self.game_instance.get_screen()
        original_selected = getattr(self.game_instance, 'selected_pawn', None)
        original_current = getattr(self.game_instance, 'current_player', None)
        
        # Set values
        self.game_instance._BaseUI__screen = screen
        if hasattr(self.game_instance, 'selected_pawn'):
            self.game_instance.selected_pawn = self.selected_pawn
        if hasattr(self.game_instance, 'current_player'):
            self.game_instance.current_player = self.current_player
        
        # Draw the game but replace the back button
        self.game_instance.draw()
        
        # Override the back button with network-styled version
        self._draw_network_back_button(screen)
        
        # Restore original values
        self.game_instance._BaseUI__screen = original_screen
        if hasattr(self.game_instance, 'selected_pawn'):
            self.game_instance.selected_pawn = original_selected
        if hasattr(self.game_instance, 'current_player'):
            self.game_instance.current_player = original_current
    
    def _draw_network_back_button(self, screen):
        # Draw stylish back button like in other interfaces
        back_rect = pygame.Rect(20, 20, 120, 40)
        
        # Draw button background
        pygame.draw.rect(screen, (70, 70, 70), back_rect)
        pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
        
        # Draw button text
        button_font = pygame.font.SysFont(None, 36)
        back_text = button_font.render("Back", True, (255, 255, 255))
        text_rect = back_text.get_rect(center=back_rect.center)
        screen.blit(back_text, text_rect)
        
        # Update the back button rect for click detection
        if hasattr(self.game_instance, 'back_button_rect'):
            self.game_instance.back_button_rect = back_rect
    
    def _draw_basic(self, screen):
        screen = self.get_screen()
        screen.fill((30, 30, 30))
        
        board_ui = Board_draw_tools()
        
        # Draw the board
        for row in range(len(self.board)):
            for col in range(len(self.board[0])):
                rect = pygame.Rect(
                    col * 60 + 100,
                    row * 60 + 100,
                    60, 60
                )
                
                value = self.board[row][col]
                color = board_ui.get_color_from_board(value // 10)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)
                
                # Draw pawns with same style as normal games
                if value % 10 > 0:
                    center = rect.center
                    radius = 20
                    if value % 10 == 1:
                        pygame.draw.circle(screen, (255, 255, 255), center, radius)
                        pygame.draw.circle(screen, (0, 0, 0), center, radius, 2)
                    elif value % 10 == 2:
                        pygame.draw.circle(screen, (0, 0, 0), center, radius)
                        pygame.draw.circle(screen, (255, 255, 255), center, radius, 2)
        
        # Draw stylish back button
        self._draw_network_back_button(screen)
    
    def _draw_network_info(self, screen):
        # Create a stylish info panel
        panel_width = 350
        panel_height = 120
        panel_x = self.get_width() - panel_width - 20
        panel_y = 20
        
        # Draw semi-transparent background panel
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((40, 40, 40))
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Draw panel border
        pygame.draw.rect(screen, (100, 100, 100), (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Network Game title
        title_font = pygame.font.SysFont(None, 32)
        title_surface = title_font.render("Network Game", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 10, panel_y + 10))
        
        # Player information with colored circle
        info_font = pygame.font.SysFont(None, 28)
        player_text = f"You are Player {self.local_player}"
        player_surface = info_font.render(player_text, True, (255, 255, 255))
        screen.blit(player_surface, (panel_x + 10, panel_y + 45))
        
        # Draw player color indicator circle
        circle_x = panel_x + panel_width - 30
        circle_y = panel_y + 55
        if self.local_player == 1:
            pygame.draw.circle(screen, (255, 255, 255), (circle_x, circle_y), 12)
            pygame.draw.circle(screen, (0, 0, 0), (circle_x, circle_y), 12, 2)
        else:
            pygame.draw.circle(screen, (0, 0, 0), (circle_x, circle_y), 12)
            pygame.draw.circle(screen, (255, 255, 255), (circle_x, circle_y), 12, 2)
        
        # Status message
        if self.status_message:
            status_font = pygame.font.SysFont(None, 24)
            status_surface = status_font.render(self.status_message, True, self.status_color)
            screen.blit(status_surface, (panel_x + 10, panel_y + 80))
    
    def get_game_statistics(self):
        if self.session.board:
            return self.session.get_game_info()
        return None
    
    def get_valid_moves(self):
        return self.session.get_valid_moves()
    
    def can_make_move(self):
        return (self.current_player == self.local_player and 
                self.session.game_started and 
                not self.game_finished)