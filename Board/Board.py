import json
import os
#in the following list:
    #the number 1 = blue
    #the number 2 = green
    #the number 3 = yellow
    #the number 4 = red 
    
    
    #then the second number represent the player 
    #0 if there is no player on the case
    #1 for player 1
    #2 for player 2
    
    #exemple:
    # red case with a pawn of player 1 = 41
    # red case with a pawn of player 2 = 42
    # yellow case with a pawn of player 1 = 31
    # red case with no player = 40
    
    
    #finally
    #the number 5 = a corner
    
    #exemple:
    #a corner with no pawn = 50
    #a corner with a pawn of player 1 = 51

class Board:
    
    def __init__(self):
        self._square_list = {
            "default 1": [
                [40, 10, 10, 40],
                [10, 10, 40, 30],
                [30, 10, 40, 10],
                [40, 40, 10, 40]
            ],
            "default 2": [
                [20, 20, 30, 30],
                [10, 40, 40, 10],
                [10, 30, 20, 20],
                [40, 10, 10, 40]
            ],
            "default 3": [
                [10, 10, 10, 10],
                [20, 20, 20, 20],
                [30, 30, 30, 30],
                [40, 40, 40, 40]
            ],
            "default 4": [
                [40, 30, 20, 10],
                [10, 20, 30, 40],
                [40, 30, 20, 10],
                [10, 20, 30, 40]
            ]            
        }

        self.final_board = None
        self._default_board = [[0]*8 for _ in range(8)]  # 8x8 empty board
        self._default_square = [[0]*4 for _ in range(4)]  # 4x4 empty square
        self._corners = [0]*4  # corners list

    def save_to_file(self, filename: str):
        # Save squares to JSON file, merge if file exists
        data = {}
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                print(f"File '{filename}' exists but is invalid JSON, overwriting.")

        if "square" not in data:
            data["square"] = {}

        data["square"].update(self._square_list)

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to '{filename}' without overwriting other keys.")

    def save_to_file_manager(self, filename: str):
        # Save only squares, overwrite file
        with open(filename, 'w') as f:
            json.dump({"square": self._square_list}, f, indent=4)
        print(f"Data saved to '{filename}'.")

    def check_or_create_file(self, filename: str):
        # Create file if missing, check if empty
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write('')
            print(f"File '{filename}' created.")
            return False
        if os.path.getsize(filename) == 0:
            print(f"File '{filename}' is empty.")
            return False
        print(f"File '{filename}' exists and contains data.")
        return True

    def load_from_file(self, filename: str):
        # Load squares and boards from file
        if not self.check_or_create_file(filename):
            return

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self._square_list = {k:v for k,v in data.get("square", {}).items()}
            self._board_list = {k:v for k,v in data.get("board", {}).items()}
            print(f"Data loaded from '{filename}'.")
        except json.JSONDecodeError:
            print(f"Failed to read '{filename}': invalid JSON.")

    def create_final_board(self, matrix_8x8):
        # Set final board from 8x8 matrix copy
        if len(matrix_8x8) != 8 or any(len(row) != 8 for row in matrix_8x8):
            raise ValueError("Board must be 8x8 matrix.")
        self.final_board = [row[:] for row in matrix_8x8]
        return [row[:] for row in matrix_8x8]

    def add_border_and_corners(self, board):
        # Add zero border and corners to board
        cols = len(board[0])
        new_board = [[0] + row + [0] for row in board]
        zero_row = [0]*(cols+2)
        new_board.insert(0, zero_row[:])
        new_board.append(zero_row[:])

        # Set corners (values 50 and 60 to mark corners)
        new_board[0][0] = 50
        new_board[0][-1] = 50
        new_board[-1][0] = 60
        new_board[-1][-1] = 60

        return new_board

    def get_default_board(self):
        return self._default_board

    def get_default_square(self):
        return self._default_square

    def set_square_list(self, key: str, value: list):
        # Set a square pattern by key
        if isinstance(key, str) and isinstance(value, list):
            self._square_list[key] = value
        else:
            print("Error: key must be str and value must be list.")

    def get_square_list(self):
        return self._square_list

    def rotate_right(self, board):
        # Rotate board 90° clockwise
        return [list(reversed(col)) for col in zip(*board)]

    def rotate_left(self, board):
        # Rotate board 90° counter-clockwise
        return [list(col) for col in zip(*board)][::-1]

    def flip_horizontal(self, board):
        # Flip board horizontally
        return [row[::-1] for row in board]