import pygame
from board import BLACK, WHITE, HOVER_COLOR

class Button:
    def __init__(self, x, y, width, height, text, font, bg_color, text_color, action=None, image=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.action = action
        self.image = image

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            color = self.bg_color
            if self.is_hovered():
                color = HOVER_COLOR
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 2)
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered() and self.action:
                self.action()
