class Board_draw_tools:

    def get_color_from_board(self, code):
        if code == 1:
            return (100, 160, 230)  
        elif code == 0:
            return (50, 50, 50)
        elif code == 2:
            return (125, 190, 155)  
        elif code == 3:
            return (240, 200, 80)
        elif code == 4:
            return (235, 115, 115)  
        elif code == 5:
            return (128, 0, 128)
        elif code == 6:
            return (110, 110, 110)
             
        
    def get_colors(self):
        return {
            1: (100, 160, 230),  
            2: (125, 190, 155),  
            3: (240, 200, 80),
            4: (235, 115, 115),  
            5: (128, 0, 128),
            0: (30, 30, 30)
        }
        
