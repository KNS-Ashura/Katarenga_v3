from UI_tools.win_screen import WinScreen
import json
import copy
from Game_ui.move_rules import Moves_rules
from Online.NetworkGameLogic import NetworkGameLogic

try:
    NETWORK_LOGIC_AVAILABLE = True
except ImportError:
    #print("NetworkGameLogic not found, using basic validation only")
    NETWORK_LOGIC_AVAILABLE = False

class GameSession:
    
    def __init__(self, game_type, network_manager):
        self.game_type = game_type  # 1=Katarenga, 2=Congress, 3=Isolation
        self.network = network_manager
        self.board = None
        self.current_player = 1
        self.is_host = network_manager.is_host
        self.game_started = False
        self.game_finished = False
        
        # Movement rules
        self.moves_rules = None
        
        # Game logic handler
        if NETWORK_LOGIC_AVAILABLE:
            self.game_logic = NetworkGameLogic()
        else:
            self.game_logic = None
        
        # Callbacks for game events
        self.on_board_update = None
        self.on_player_change = None
        self.on_game_end = None
        
        self.network.set_callbacks(
            message_callback=self._handle_network_message,
            disconnect_callback=self._handle_disconnect
        )
    
    def set_game_callbacks(self, board_update=None, player_change=None, game_end=None):
        self.on_board_update = board_update
        self.on_player_change = player_change
        self.on_game_end = game_end
    
    def set_board(self, board_data):
        self.board = copy.deepcopy(board_data)
        # Initialize movement rules with new board
        self.moves_rules = Moves_rules(self.board)
        
        if self.is_host:
            # Send board data to client
            message = {
                'type': 'BOARD_DATA',
                'board': self.board,
                'game_type': self.game_type
            }
            self.network.send_message(json.dumps(message))
    
    def start_game(self):
        if not self.board:
            return False
        
        self.game_started = True
        self.current_player = 1  # Host always starts
        
        if self.is_host:
            message = {
                'type': 'GAME_START',
                'current_player': self.current_player
            }
            self.network.send_message(json.dumps(message))
        
        if self.on_player_change:
            self.on_player_change(self.current_player)
        
        #print(f"Game started - Type: {self.game_type}")
        return True
    
    def make_move(self, from_pos, to_pos):
        if not self.game_started or self.game_finished:
            #print("[DEBUG] Move rejected: game not started or already finished.")
            return False

        local_player = 1 if self.is_host else 2
        if self.current_player != local_player:
            #print("[DEBUG] Not your turn.")
            return False

        #print(f"[DEBUG] Attempting move: {from_pos} -> {to_pos} by Player {self.current_player}")

        if self.game_logic and self.game_logic.validate_move(
            self.board, self.moves_rules, self.game_type,
            self.current_player, from_pos, to_pos
        ):
            self._apply_move(from_pos, to_pos)

            message = {
                'type': 'MOVE',
                'from': from_pos,
                'to': to_pos,
                'player': self.current_player
            }
            #print(f"[DEBUG] Sending MOVE to opponent: {message}")
            self.network.send_message(json.dumps(message))

            winner = self.game_logic.check_victory(self.board, self.game_type, self.current_player)
            if winner:
                #print(f"[DEBUG] Victory detected for Player {winner}")
                self._end_game(winner)
            else:
                self._switch_player()

            return True

        elif not self.game_logic and self._basic_validate_move(from_pos, to_pos):
            self._apply_move(from_pos, to_pos)

            message = {
                'type': 'MOVE',
                'from': from_pos,
                'to': to_pos,
                'player': self.current_player
            }
            self.network.send_message(json.dumps(message))
            self._switch_player()
            return True

        #print("[DEBUG] Invalid move.")
        return False
    
    def _handle_network_message(self, message):
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            #print(f"[DEBUG] Received message: {msg_type} | Data: {data}")

            if msg_type == 'BOARD_DATA':
                self.board = data['board']
                self.game_type = data['game_type']
                self.moves_rules = Moves_rules(self.board)
                if self.on_board_update:
                    self.on_board_update(self.board)

            elif msg_type == 'GAME_START':
                self.game_started = True
                self.current_player = data['current_player']
                if self.on_player_change:
                    self.on_player_change(self.current_player)

            elif msg_type == 'MOVE':
                from_pos = tuple(data['from']) if data['from'] else None
                to_pos = tuple(data['to'])
                player = data['player']
                #print(f"[DEBUG] Applying opponent move: {from_pos} -> {to_pos}")

                self._apply_move(from_pos, to_pos)

                winner = None
                if self.game_logic:
                    winner = self.game_logic.check_victory(
                        self.board, self.game_type, self.current_player
                    )
                if winner:
                    #print(f"[DEBUG] Opponent triggered victory: Player {winner}")
                    # Appeler _end_game pour que WinScreen soit affiché aussi côté client
                    self._end_game(winner)
                else:
                    self._switch_player()

            elif msg_type == 'GAME_END':
                winner = data['winner']
                #print(f"[DEBUG] GAME_END received from opponent - Winner: Player {winner}")
                self._end_game_received(winner)

        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _handle_disconnect(self):
        if not self.game_finished:
            self._end_game("Disconnection")
    
    def _apply_move(self, from_pos, to_pos):
        if not self.board:
            return
        
        to_row, to_col = to_pos
        
        if self.game_type == 3:  # Isolation
            # For Isolation, just place the piece
            dest_color = self.board[to_row][to_col] // 10
            self.board[to_row][to_col] = dest_color * 10 + self.current_player
        
        else:  # Katarenga and Congress
            if from_pos is None:
                print("Error : from is None")
                return
            
            from_row, from_col = from_pos
            
            # Verify source has correct player piece
            piece = self.board[from_row][from_col]
            if piece % 10 != self.current_player:
                return
            
            # Clear source square
            source_color = piece // 10
            self.board[from_row][from_col] = source_color * 10
            
            # Place piece at destination
            dest_color = self.board[to_row][to_col] // 10
            self.board[to_row][to_col] = dest_color * 10 + self.current_player
        
        # Update move rules with new board state
        if self.moves_rules:
            self.moves_rules._Moves_rules__board = self.board
        
        if self.on_board_update:
            self.on_board_update(self.board)
    
    def _switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        if self.on_player_change:
            self.on_player_change(self.current_player)
    
    def _end_game(self, winner):
        #print(f"[DEBUG] _end_game called - Winner: Player {winner}")
        self.game_finished = True

        message = {
            'type': 'GAME_END',
            'winner': winner
        }
        #print("[DEBUG] Sending GAME_END message to opponent")
        self.network.send_message(json.dumps(message))

        if self.on_game_end:
            #print("[DEBUG] Calling on_game_end callback")
            self.on_game_end(winner)
        else:
            #print("[DEBUG] No on_game_end callback defined")
            pass
        # Affiche la WinScreen quel que soit le joueur
        self.close_all_and_show_win_screen(f"Player {winner}")
    
    def _end_game_received(self, winner):
        #print(f"[DEBUG] _end_game_received called - Winner: Player {winner}")
        self.game_finished = True

        if self.on_game_end:
            #print("[DEBUG] Calling on_game_end callback from _end_game_received")
            self.on_game_end(winner)
        else:
            #print("[DEBUG] No on_game_end callback defined in _end_game_received")
            pass
        # Affiche WinScreen côté client à la réception de GAME_END
        self.close_all_and_show_win_screen(f"Player {winner}")
    
    def close_all_and_show_win_screen(self, winner):
        #print(f"[DEBUG] Closing all and showing WinScreen for {winner}")
        WinScreen(winner)
    
    def send_chat_message(self, text):
        message = {
            'type': 'CHAT',
            'message': f"{'Host' if self.is_host else 'Client'}: {text}"
        }
        self.network.send_message(json.dumps(message))
    
    def get_status(self):
        return {
            'game_type': self.game_type,
            'game_started': self.game_started,
            'game_finished': self.game_finished,
            'current_player': self.current_player,
            'is_host': self.is_host,
            'local_player': 1 if self.is_host else 2
        }
    
    def get_game_info(self): #Get game state information
        if self.board and self.game_logic:
            return self.game_logic.get_game_state_info(
                self.board, self.game_type, self.current_player
            )
        return None
    
    def get_valid_moves(self):
        if self.board and self.game_logic:
            return self.game_logic.get_valid_moves(
                self.board, self.moves_rules, self.game_type, self.current_player
            )
        return []
    
    def _basic_validate_move(self, from_pos, to_pos): # get move validation if NetworkGameLogic not available
        if not self.moves_rules or not self.board:
            return False
        
        to_row, to_col = to_pos
        if not (0 <= to_row < len(self.board) and 0 <= to_col < len(self.board[0])):
            return False
        
        if self.game_type == 3:  # Isolation
            return from_pos is None and self.board[to_row][to_col] % 10 == 0
        
        else:  # Katarenga and Congress
            if from_pos is None:
                return False
            from_row, from_col = from_pos
            if not (0 <= from_row < len(self.board) and 0 <= from_col < len(self.board[0])):
                return False
            case_color = self.board[from_row][from_col]