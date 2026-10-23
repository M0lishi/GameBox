"""Общие настройки интерфейса и класс Button для всех игр GameBox."""
import pygame

WIDTH, HEIGHT = 800, 600
FPS = 60

# Палитра (используйте её во всех играх, чтобы всё выглядело единообразно)
BG = (24, 26, 35)
PANEL = (40, 44, 60)
PANEL_HOVER = (62, 70, 100)
ACCENT = (96, 165, 250)
TEXT = (235, 237, 245)
MUTED = (140, 146, 165)

_FONT_NAMES = "arial,segoeui,dejavusans,liberationsans,freesans"
_font_cache = {}


def get_font(size):
    """Шрифт с поддержкой кириллицы (системный, с запасными вариантами)."""
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont(_FONT_NAMES, size)
    return _font_cache[size]


def draw_text(screen, text, size, color, center=None, topleft=None):
    """Нарисовать текст по центру или от верхнего левого угла."""
    surf = get_font(size).render(text, True, color)
    rect = surf.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    screen.blit(surf, rect)
    return rect


class Button:
    def __init__(self, rect, text, font_size=24):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font_size = font_size

    def draw(self, screen):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(
            screen, PANEL_HOVER if hovered else PANEL, self.rect, border_radius=12
        )
        if hovered:
            pygame.draw.rect(screen, ACCENT, self.rect, width=2, border_radius=12)

        # Если текст не влезает в кнопку, уменьшаем шрифт
        size = self.font_size
        while size > 12 and get_font(size).size(self.text)[0] > self.rect.width - 20:
            size -= 1
        draw_text(screen, self.text, size, TEXT, center=self.rect.center)

    def clicked(self, event):
        """True, если по кнопке кликнули левой кнопкой мыши."""
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )
