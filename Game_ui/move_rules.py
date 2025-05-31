# Class that defines movement rules depending on the color of the board case.
# Each movement method checks if a move is allowed based on chess-like rules
# adapted to colored tiles: blue (king), green (knight), yellow (bishop), red (rook).
class Moves_rules:
    def __init__(self, board):
        self.__board = board  # Board is expected to be a 2D list

    # Yellow tile: diagonal movement (bishop-like)
    def yellow_case_move(self, x_start, y_start, x_end, y_end):
        if self.__board[x_end][y_end] == 0:
            return False

        dx, dy = x_end - x_start, y_end - y_start
        if abs(dx) != abs(dy):  # Must be diagonal
            return False

        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1

        # Check for obstacles or yellow tiles along the way
        for i in range(1, abs(dx)):
            x, y = x_start + i * sx, y_start + i * sy
            if self.__board[x][y] % 10 != 0:  # Obstacle
                return False
            if self.__board[x][y] // 10 == 3:  # Yellow tile
                return False

        end_piece = self.__board[x_end][y_end] % 10
        current_player = self.__board[x_start][y_start] % 10

        return end_piece == 0 or end_piece != current_player

    # Blue tile: 1-square in any direction (king-like)
    def blue_case_move(self, x_start, y_start, x_end, y_end):
        if self.__board[x_end][y_end] == 0:
            return False

        dx, dy = abs(x_end - x_start), abs(y_end - y_start)
        if dx > 1 or dy > 1:  # Only adjacent squares
            return False

        end_piece = self.__board[x_end][y_end] % 10
        current_player = self.__board[x_start][y_start] % 10

        return end_piece == 0 or end_piece != current_player

    # Green tile: L-shaped movement (knight-like)
    def green_case_move(self, x_start, y_start, x_end, y_end):
        if self.__board[x_end][y_end] == 0:
            return False

        dx, dy = abs(x_end - x_start), abs(y_end - y_start)
        if not ((dx == 2 and dy == 1) or (dx == 1 and dy == 2)):
            return False

        end_piece = self.__board[x_end][y_end] % 10
        current_player = self.__board[x_start][y_start] % 10

        return end_piece == 0 or end_piece != current_player

    # Red tile: straight movement (rook-like)
    def red_case_move(self, x_start, y_start, x_end, y_end):
        if self.__board[x_end][y_end] == 0:
            return False

        if x_start != x_end and y_start != y_end:  # Must be horizontal or vertical
            return False

        dx = 0 if x_start == x_end else (1 if x_end > x_start else -1)
        dy = 0 if y_start == y_end else (1 if y_end > y_start else -1)

        x, y = x_start + dx, y_start + dy
        while (x, y) != (x_end, y_end):
            if self.__board[x][y] % 10 != 0:  # Obstacle
                return False
            if self.__board[x][y] // 10 == 4:  # Red tile
                return False
            x, y = x + dx, y + dy

        end_piece = self.__board[x_end][y_end] % 10
        current_player = self.__board[x_start][y_start] % 10

        return end_piece == 0 or end_piece != current_player

    # Selects the appropriate rule based on the tile color
    def verify_move(self, case_color, x_start, y_start, x_end, y_end):
        couleur = case_color // 10

        if couleur == 1:
            return self.blue_case_move(x_start, y_start, x_end, y_end)
        elif couleur == 2:
            return self.green_case_move(x_start, y_start, x_end, y_end)
        elif couleur == 3:
            return self.yellow_case_move(x_start, y_start, x_end, y_end)
        elif couleur == 4:
            return self.red_case_move(x_start, y_start, x_end, y_end)
        else:
            return False