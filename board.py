import random
import numpy as np

# --- Board ---
BOARD_SIZE = 9
TILE_SIZE = 60
BOARD_OFFSET_X = 80
BOARD_OFFSET_Y = 50
SCOREBOARD_WIDTH = 200
WIDTH = BOARD_OFFSET_X * 2 + BOARD_SIZE * TILE_SIZE + SCOREBOARD_WIDTH
HEIGHT = BOARD_OFFSET_Y * 2 + BOARD_SIZE * TILE_SIZE + 70
FPS = 60

# --- Colors ---
WOOD_COLOR = (205, 133, 63)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
HOVER_COLOR = (160, 82, 45)
ERROR_OVERLAY_COLOR = (0, 0, 0, 128)

# --- Pieces ---
class Piece:

    def __init__(self, row, col, color, owner):
        # row,col -> np.int16
        self.position = np.array([row, col], dtype=np.int16)
        self.color = color
        self.owner = owner
        self.x = -100
        self.y = -100
        self.reset_position()

    @property
    def row(self):
        return self.position[0]

    @row.setter
    def row(self, value):

        if value is None:
            self.position[0] = -1
        else:
            self.position[0] = value

    @property
    def col(self):
        return self.position[1]

    @col.setter
    def col(self, value):
        if value is None:
            self.position[1] = -1
        else:
            self.position[1] = value

    def draw(self, window):
        import pygame
        radius = TILE_SIZE // 2 - 5
        pygame.draw.circle(window, self.color, (int(self.x), int(self.y)), radius)

    def reset_position(self):

        r, c = self.row, self.col
        if r >= 0 and c >= 0:
            self.x = BOARD_OFFSET_X + c * TILE_SIZE + TILE_SIZE // 2
            self.y = BOARD_OFFSET_Y + r * TILE_SIZE + TILE_SIZE // 2
        else:
            self.x = -100
            self.y = -100
