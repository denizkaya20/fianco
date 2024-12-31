import random

# --- Board / Oyun Alanı Sabitleri ---
BOARD_SIZE = 9
TILE_SIZE = 60
BOARD_OFFSET_X = 80
BOARD_OFFSET_Y = 50
SCOREBOARD_WIDTH = 200
WIDTH = BOARD_OFFSET_X * 2 + BOARD_SIZE * TILE_SIZE + SCOREBOARD_WIDTH
HEIGHT = BOARD_OFFSET_Y * 2 + BOARD_SIZE * TILE_SIZE + 70
FPS = 60

# --- Renkler ---
WOOD_COLOR = (205, 133, 63)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
HOVER_COLOR = (160, 82, 45)
ERROR_OVERLAY_COLOR = (0, 0, 0, 128)

# --- Parçalar (Taşlar) ---
class Piece:
    def __init__(self, row, col, color, owner):
        self.row = row
        self.col = col
        self.color = color
        self.owner = owner
        self.reset_position()

    def draw(self, window):
        radius = TILE_SIZE // 2 - 5
        import pygame  # pygame import'u burada lokal kullanıyoruz
        pygame.draw.circle(window, self.color, (int(self.x), int(self.y)), radius)

    def reset_position(self):
        if self.row is not None and self.col is not None:
            self.x = BOARD_OFFSET_X + self.col * TILE_SIZE + TILE_SIZE // 2
            self.y = BOARD_OFFSET_Y + self.row * TILE_SIZE + TILE_SIZE // 2
        else:
            # Taş yakalandığında, tahtadan "uzak" bir konuma atıyoruz.
            self.x = -100
            self.y = -100
