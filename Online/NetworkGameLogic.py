from collections import deque

class NetworkGameLogic:
    
    
    def validate_move(self, board, moves_rules, game_type, current_player, from_pos, to_pos):
        
        if not moves_rules or not board:
            return False
        
        to_row, to_col = to_pos
        
        # Check destination limits
        if not (0 <= to_row < len(board) and 0 <= to_col < len(board[0])):
            return False
        
        if game_type == 3:  # Isolation
            return self._validate_isolation_move(board, moves_rules, current_player, from_pos, to_pos)
        elif game_type == 1:  # Katarenga
            return self._validate_katarenga_move(board, moves_rules, current_player, from_pos, to_pos)
        elif game_type == 2:  # Congress
            return self._validate_congress_move(board, moves_rules, current_player, from_pos, to_pos)
        
        return False
    
    def _validate_isolation_move(self, board, moves_rules, current_player, from_pos, to_pos):
       
        to_row, to_col = to_pos
        
        # For Isolation
        if from_pos is not None:
            return False
        
        # Check if square is free
        case = board[to_row][to_col]
        if case % 10 != 0:
            return False
        
        # Skip corners and invalid squares
        if case in (0, 50, 60):
            return False
        
        # Check square is not "en prise" = under attack
        if self._is_square_under_attack(board, moves_rules, to_row, to_col):
            return False
        
        return True
    
    def _validate_katarenga_move(self, board, moves_rules, current_player, from_pos, to_pos):
        
        if from_pos is None:
            return False
        
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Check source position is in limits
        if not (0 <= from_row < len(board) and 0 <= from_col < len(board[0])):
            return False
        
        # Check player owns the piece at source position
        case_color = board[from_row][from_col]
        if case_color % 10 != current_player:
            return False
        
       
        # Player 1 can move from row 8 (cols 1-8) to victory corners (9,0) or (9,9)
        if (current_player == 1 and from_row == 8 and 1 <= from_col <= 8 
            and (to_row, to_col) in [(9, 0), (9, 9)]):
            return True
        
        # Player 2 can move from row 1 (cols 1-8) to victory corners (0,0) or (0,9)  
        if (current_player == 2 and from_row == 1 and 1 <= from_col <= 8
            and (to_row, to_col) in [(0, 0), (0, 9)]):
            return True
        
        # Use existing movement rules for normal moves
        return moves_rules.verify_move(case_color, from_row, from_col, to_row, to_col)
    
    def _validate_congress_move(self, board, moves_rules, current_player, from_pos, to_pos):
        
        if from_pos is None:
            return False
        
        from_row, from_col = from_pos
        
        # Check source position is in limits
        if not (0 <= from_row < len(board) and 0 <= from_col < len(board[0])):
            return False
        
        # Check player owns the piece at source position
        case_color = board[from_row][from_col]
        if case_color % 10 != current_player:
            return False
        
        # Use existing movement rules
        return moves_rules.verify_move(case_color, from_row, from_col, to_pos[0], to_pos[1])
    
    def check_victory(self, board, game_type, current_player):
        
        if game_type == 1:  # Katarenga
            return self._check_katarenga_victory(board)
        elif game_type == 2:  # Congress
            return self._check_congress_victory(board)
        elif game_type == 3:  # Isolation
            return self._check_isolation_victory(board, current_player)
        
        return None
    
    def _check_katarenga_victory(self, board):
        
        player1_count = 0
        player2_count = 0
        
        # Count pawns for each player
        for row in range(len(board)):
            for col in range(len(board[0])):
                player = board[row][col] % 10
                if player == 1:
                    player1_count += 1
                elif player == 2:
                    player2_count += 1
        
        # Victory by elimination
        if player1_count == 0:
            return 2
        if player2_count == 0:
            return 1
        
        # Victory by corner occupation 
        if len(board) >= 10 and len(board[0]) >= 10:
            # Player 2 wins if occupies both bottom corners
            if board[9][0] % 10 == 1 and board[9][9] % 10 == 1:
                return 1
            
            # Player 1 wins if occupies both top corners  
            if board[0][0] % 10 == 2 and board[0][9] % 10 == 2:
                return 2
        
        return None
    
    def _check_congress_victory(self, board):
       
        grid_dim = len(board)
        
        for player in [1, 2]:
            # Find all positions of current player
            positions = [(i, j) for i in range(grid_dim) for j in range(grid_dim)
                        if board[i][j] % 10 == player]
            
            if not positions:
                continue
            
            # Check if all pawns are connected using BFS
            visited = set([positions[0]])
            queue = deque([positions[0]])
            
            while queue:
                x, y = queue.popleft()
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < grid_dim and 0 <= ny < grid_dim and
                        (nx, ny) not in visited and board[nx][ny] % 10 == player):
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            
            # If all pawns are connected, player wins
            if len(visited) == len(positions):
                return player
        
        return None
    
    def _check_isolation_victory(self, board, current_player):
       
        # Count total moves made
        total_moves = 0
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] % 10 != 0:
                    total_moves += 1
        
        max_moves = len(board) * len(board[0])
        
        # Game ends if board is full
        if total_moves >= max_moves:
            return current_player  # Last player to move wins
        
        # Check if current player can still play
        if not self.can_play_isolation(board, current_player):
            # Current player cannot play, opponent wins
            return 2 if current_player == 1 else 1
        
        return None
    
    def can_play_isolation(self, board, current_player):
        
        for i in range(len(board)):
            for j in range(len(board[0])):
                case = board[i][j]
                # Skip corners and already occupied squares
                if case in (0, 50, 60) or case % 10 != 0:
                    continue
                
                # Check if square is not "en prise" (under attack)
                if not self.is_square_under_attack(board, None, i, j):
                    return True
        return False
    
    def is_square_under_attack(self, board, moves_rules, x, y):
       
        # Create temporary moves_rules if not provided
        if moves_rules is None:
            from Game_ui.move_rules import Moves_rules
            moves_rules = Moves_rules(board)
        
        for i in range(len(board)):
            for j in range(len(board[0])):
                case = board[i][j]
                if case % 10 != 0:  # There's a piece here
                    try:
                        if moves_rules.verify_move(case, i, j, x, y):
                            return True
                    except:
                        # Handle any errors in move verification
                        continue
        return False
    
    def get_valid_moves(self, board, moves_rules, game_type, current_player):
        
        valid_moves = []
        
        if game_type == 3:  # Isolation
            # Check all empty squares
            for row in range(len(board)):
                for col in range(len(board[0])):
                    if self.validate_move(board, moves_rules, game_type, current_player, None, (row, col)):
                        valid_moves.append((None, (row, col)))
        
        else:  # Katarenga and Congress
            # Check all player's pieces
            for from_row in range(len(board)):
                for from_col in range(len(board[0])):
                    if board[from_row][from_col] % 10 == current_player:
                        # Check all possible destinations
                        for to_row in range(len(board)):
                            for to_col in range(len(board[0])):
                                if self.validate_move(board, moves_rules, game_type, current_player, 
                                                    (from_row, from_col), (to_row, to_col)):
                                    valid_moves.append(((from_row, from_col), (to_row, to_col)))
        
        return valid_moves
    
    def is_game_over(self, board, game_type, current_player):
        
        # Check for victory
        winner = self.check_victory(board, game_type, current_player)
        if winner:
            return True, winner
        
        # Check if current player has valid moves
        valid_moves = self.get_valid_moves(board, None, game_type, current_player)
        if not valid_moves:
            # No valid moves, opponent wins
            opponent = 2 if current_player == 1 else 1
            return True, opponent
        
        return False, None
    
    def get_game_state_info(self, board, game_type, current_player):
       
        info = {
            'current_player': current_player,
            'game_type': game_type,
            'board_size': (len(board), len(board[0])),
            'total_pieces': sum(1 for row in board for cell in row if cell % 10 != 0),
            'player1_pieces': sum(1 for row in board for cell in row if cell % 10 == 1),
            'player2_pieces': sum(1 for row in board for cell in row if cell % 10 == 2),
        }
        
        # Game  information
        if game_type == 1:  # Katarenga
            info['corner_status'] = self._get_katarenga_corner_status(board)
        elif game_type == 2:  # Congress
            info['connectivity'] = self._get_congress_connectivity(board)
        elif game_type == 3:  # Isolation
            info['board_fill_percentage'] = (info['total_pieces'] / (info['board_size'][0] * info['board_size'][1])) * 100
            info['valid_moves_count'] = len(self.get_valid_moves(board, None, game_type, current_player))
        
        return info
    
    def _get_katarenga_corner_status(self, board):
        
        if len(board) < 10 or len(board[0]) < 10:
            return {}
        
        return {
            'top_left': board[0][0] % 10,
            'top_right': board[0][9] % 10,
            'bottom_left': board[9][0] % 10,
            'bottom_right': board[9][9] % 10
        }
    
    def _get_congress_connectivity(self, board):
        
        connectivity = {}
        
        for player in [1, 2]:
            positions = [(i, j) for i in range(len(board)) for j in range(len(board[0]))
                        if board[i][j] % 10 == player]
            
            if positions:
                # Count connected components
                visited = set()
                components = 0
                
                for pos in positions:
                    if pos not in visited:
                        components += 1
                        
                        queue = deque([pos])
                        visited.add(pos)
                        
                        while queue:
                            x, y = queue.popleft()
                            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                                nx, ny = x + dx, y + dy
                                if ((nx, ny) in positions and (nx, ny) not in visited):
                                    visited.add((nx, ny))
                                    queue.append((nx, ny))
                
                connectivity[f'player_{player}'] = {
                    'total_pieces': len(positions),
                    'connected_components': components,
                    'is_fully_connected': components == 1
                }
            else:
                connectivity[f'player_{player}'] = {
                    'total_pieces': 0,
                    'connected_components': 0,
                    'is_fully_connected': False
                }
        
        return connectivity