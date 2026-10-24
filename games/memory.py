"""Память для GameBox: найдите все пары карточек за минимум ходов.

Подключается к главному меню через run(screen, clock):
по Esc возвращает управление в меню и отдаёт лучший результат за сессию
(наименьшее число ходов в завершённой партии) или None, если ни одной партии
не доведено до конца. ЧЕМ МЕНЬШЕ ХОДОВ, ТЕМ ЛУЧШЕ - добавьте "memory"
в LOWER_IS_BETTER (scores.py) и в UNITS (main.py).

Управление: клик мышью по карточке, ПРОБЕЛ - новая партия, Esc - в меню.
Картинки рисуются фигурами pygame, поэтому внешние файлы не нужны.
"""
import math
import random
import sys

import pygame

FPS = 60
COLS, ROWS = 4, 4          # 4x4 = 8 пар
CARD, GAP = 100, 14        # размер карточки и промежуток между ними
FLIP_BACK_MS = 800         # сколько показывать неугаданную пару
FONT_NAMES = "arial,segoeui,dejavusans,liberationsans,freesans"

BG = (24, 26, 35)
TEXT = (235, 237, 245)
MUTED = (140, 146, 165)
PANEL = (40, 44, 60)
PANEL_HOVER = (62, 70, 100)
ACCENT = (96, 165, 250)
FACE = (235, 237, 245)
MATCHED_BG = (36, 66, 50)
GOOD = (80, 200, 120)

# 8 разных картинок: (фигура, цвет)
SHAPES = [
    ("circle", (230, 80, 80)),
    ("square", (70, 130, 240)),
    ("triangle", (60, 180, 100)),
    ("diamond", (240, 200, 40)),
    ("cross", (245, 140, 50)),
    ("star", (170, 90, 220)),
    ("ring", (40, 190, 200)),
    ("hexagon", (240, 100, 170)),
]


def draw_shape(surface, name, color, rect):
    """Рисует фигуру по центру прямоугольника."""
    cx, cy = rect.center
    r = CARD * 0.30

    if name == "circle":
        pygame.draw.circle(surface, color, (cx, cy), int(r))
    elif name == "ring":
        pygame.draw.circle(surface, color, (cx, cy), int(r), 9)
    elif name == "square":
        side = int(r * 1.6)
        pygame.draw.rect(surface, color, pygame.Rect(cx - side // 2, cy - side // 2, side, side))
    elif name == "triangle":
        pts = [(cx, cy - r), (cx + r * 1.05, cy + r * 0.8), (cx - r * 1.05, cy + r * 0.8)]
        pygame.draw.polygon(surface, color, pts)
    elif name == "diamond":
        pts = [(cx, cy - r * 1.1), (cx + r * 0.85, cy), (cx, cy + r * 1.1), (cx - r * 0.85, cy)]
        pygame.draw.polygon(surface, color, pts)
    elif name == "cross":
        t = int(r * 0.6)
        pygame.draw.rect(surface, color, pygame.Rect(cx - t // 2, cy - int(r), t, int(2 * r)))
        pygame.draw.rect(surface, color, pygame.Rect(cx - int(r), cy - t // 2, int(2 * r), t))
    elif name == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r * 1.15 if i % 2 == 0 else r * 0.5
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        pygame.draw.polygon(surface, color, pts)
    elif name == "hexagon":
        pts = [
            (cx + r * 1.05 * math.cos(i * math.pi / 3), cy + r * 1.05 * math.sin(i * math.pi / 3))
            for i in range(6)
        ]
        pygame.draw.polygon(surface, color, pts)


class Memory:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()

        self.font_title = pygame.font.SysFont(FONT_NAMES, 40, bold=True)
        self.font_big = pygame.font.SysFont(FONT_NAMES, 48, bold=True)
        self.font_text = pygame.font.SysFont(FONT_NAMES, 24)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 18)
        self.font_card = pygame.font.SysFont(FONT_NAMES, 48, bold=True)

        grid_w = COLS * CARD + (COLS - 1) * GAP
        start_x = (self.width - grid_w) // 2
        start_y = 105
        self.rects = [
            pygame.Rect(start_x + (i % COLS) * (CARD + GAP), start_y + (i // COLS) * (CARD + GAP), CARD, CARD)
            for i in range(COLS * ROWS)
        ]

        self.session_best = None  # лучший (наименьший) результат в ходах
        self.new_game()

    def new_game(self):
        values = list(range(COLS * ROWS // 2)) * 2
        random.shuffle(values)
        self.values = values
        self.state = ["hidden"] * len(values)  # hidden / open / matched
        self.first = None      # индекс первой открытой карточки
        self.pending = None    # (i, j, время) - неугаданная пара, ждущая переворота
        self.moves = 0
        self.matches = 0
        self.won = False
        self.start_ticks = pygame.time.get_ticks()
        self.end_ticks = None

    # ---------- логика ----------
    def resolve_pending(self):
        """Перевернуть неугаданную пару обратно."""
        if self.pending:
            i, j, _ = self.pending
            self.state[i] = self.state[j] = "hidden"
            self.pending = None

    def click_card(self, index):
        if self.won:
            return
        # если пара ещё показана, клик сразу закрывает её и открывает новую карточку
        self.resolve_pending()
        if self.state[index] != "hidden":
            return

        self.state[index] = "open"
        if self.first is None:
            self.first = index
            return

        # открыта вторая карточка - это один ход
        self.moves += 1
        first, self.first = self.first, None
        if self.values[first] == self.values[index]:
            self.state[first] = self.state[index] = "matched"
            self.matches += 1
            if self.matches == len(self.values) // 2:
                self.finish()
        else:
            self.pending = (first, index, pygame.time.get_ticks())

    def finish(self):
        self.won = True
        self.end_ticks = pygame.time.get_ticks()
        if self.session_best is None or self.moves < self.session_best:
            self.session_best = self.moves

    def update(self):
        if self.pending and pygame.time.get_ticks() - self.pending[2] >= FLIP_BACK_MS:
            self.resolve_pending()

    # ---------- ввод ----------
    def handle_events(self):
        """Обработка ввода. False - выйти в меню."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.new_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(event.pos):
                        self.click_card(i)
                        break
        return True

    # ---------- отрисовка ----------
    def elapsed_seconds(self):
        end = self.end_ticks if self.end_ticks is not None else pygame.time.get_ticks()
        return (end - self.start_ticks) // 1000

    def draw_card(self, i):
        rect = self.rects[i]
        state = self.state[i]
        if state == "hidden":
            hovered = rect.collidepoint(pygame.mouse.get_pos()) and not self.won
            pygame.draw.rect(self.screen, PANEL_HOVER if hovered else PANEL, rect, border_radius=12)
            pygame.draw.rect(self.screen, ACCENT, rect, width=2, border_radius=12)
            q = self.font_card.render("?", True, MUTED)
            self.screen.blit(q, q.get_rect(center=rect.center))
        else:
            bg = FACE if state == "open" else MATCHED_BG
            pygame.draw.rect(self.screen, bg, rect, border_radius=12)
            if state == "matched":
                pygame.draw.rect(self.screen, GOOD, rect, width=2, border_radius=12)
            name, color = SHAPES[self.values[i]]
            draw_shape(self.screen, name, color, rect)

    def draw(self):
        self.screen.fill(BG)

        title = self.font_title.render("Память", True, TEXT)
        self.screen.blit(title, (30, 22))

        secs = self.elapsed_seconds()
        info = self.font_text.render(
            f"Ходов: {self.moves}    Пары: {self.matches}/{len(self.values) // 2}    "
            f"Время: {secs // 60}:{secs % 60:02d}",
            True, MUTED,
        )
        self.screen.blit(info, info.get_rect(topright=(self.width - 30, 30)))

        for i in range(len(self.values)):
            self.draw_card(i)

        hint = self.font_small.render("Клик - открыть карточку, ПРОБЕЛ - заново, Esc - в меню", True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 22)))

        if self.won:
            self.draw_win()

        pygame.display.flip()

    def draw_win(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(190)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.width // 2, self.height // 2
        t = self.font_big.render("ПОБЕДА!", True, GOOD)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 50)))
        s = self.font_text.render(f"Ходов: {self.moves}    Время: {self.elapsed_seconds()} с", True, TEXT)
        self.screen.blit(s, s.get_rect(center=(cx, cy + 10)))
        h = self.font_text.render("ПРОБЕЛ - заново, Esc - в меню", True, (255, 220, 80))
        self.screen.blit(h, h.get_rect(center=(cx, cy + 55)))

    def run(self):
        """Игровой цикл. Возвращает лучший результат (наименьшее число ходов) или None."""
        while True:
            if not self.handle_events():
                break
            self.update()
            self.draw()
            self.clock.tick(FPS)
        return self.session_best


def run(screen, clock):
    """Точка входа для главного меню GameBox."""
    pygame.display.set_caption("Память")
    return Memory(screen, clock).run()


if __name__ == "__main__":
    pygame.init()
    window = pygame.display.set_mode((800, 600))
    run(window, pygame.time.Clock())
    pygame.quit()
