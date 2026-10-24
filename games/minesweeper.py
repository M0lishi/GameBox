"""Сапёр для GameBox.

Управление:
    левая кнопка мыши  - открыть клетку;
    правая кнопка мыши - поставить или снять флаг;
    R                  - начать новую игру;
    Esc                - вернуться в главное меню.

Первый ход всегда безопасен: мины размещаются только после первого клика и
не могут появиться в выбранной клетке или в соседних с ней клетках.
"""
import random
import sys
from collections import deque

import pygame

FPS = 60
ROWS = 9
COLS = 9
MINES = 10

BG = (24, 26, 35)
PANEL = (40, 44, 60)
PANEL_HOVER = (62, 70, 100)
GRID = (82, 88, 110)
TEXT = (235, 237, 245)
MUTED = (140, 146, 165)
ACCENT = (96, 165, 250)
GOOD = (80, 200, 120)
BAD = (230, 80, 80)
FLAG = (255, 196, 80)
FONT_NAMES = "arial,segoeui,dejavusans,liberationsans,freesans"

NUMBER_COLORS = {
    1: (90, 160, 255),
    2: (80, 200, 120),
    3: (240, 90, 90),
    4: (150, 115, 245),
    5: (190, 80, 80),
    6: (70, 200, 200),
    7: (225, 225, 225),
    8: (150, 150, 165),
}


class Minesweeper:
    """Состояние, правила и отрисовка одной сессии игры."""

    def __init__(self, screen, clock, rows=ROWS, cols=COLS, mine_count=MINES):
        if mine_count < 1 or mine_count >= rows * cols:
            raise ValueError("Число мин должно быть от 1 до количества клеток минус один")

        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()
        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count

        self.cell_size = min(48, (self.height - 150) // rows, (self.width - 80) // cols)
        self.board_width = self.cols * self.cell_size
        self.board_height = self.rows * self.cell_size
        self.board_left = (self.width - self.board_width) // 2
        self.board_top = 105

        self.font_title = pygame.font.SysFont(FONT_NAMES, 40, bold=True)
        self.font_text = pygame.font.SysFont(FONT_NAMES, 23)
        self.font_cell = pygame.font.SysFont(FONT_NAMES, 25, bold=True)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 17)

        self.wins = 0
        self.reset()

    def reset(self):
        """Создать закрытое поле; мины появятся после первого хода."""
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.numbers = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.first_move = True
        self.state = "play"  # play / won / lost

    def neighbors(self, row, col):
        """Вернуть существующих соседей клетки, включая диагонали."""
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = row + dr, col + dc
                if (dr or dc) and 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def place_mines(self, safe_row, safe_col):
        """Случайно расставить мины вне безопасной области первого клика."""
        safe = {(safe_row, safe_col), *self.neighbors(safe_row, safe_col)}
        candidates = [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if (row, col) not in safe
        ]
        # На очень маленьком пользовательском поле безопасной оставляем хотя
        # бы саму первую клетку.
        if len(candidates) < self.mine_count:
            safe = {(safe_row, safe_col)}
            candidates = [
                (row, col)
                for row in range(self.rows)
                for col in range(self.cols)
                if (row, col) not in safe
            ]
        self.mines = set(random.sample(candidates, self.mine_count))

        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) not in self.mines:
                    self.numbers[row][col] = sum(
                        neighbor in self.mines for neighbor in self.neighbors(row, col)
                    )

    def reveal(self, row, col):
        """Открыть клетку и, если она пустая, связанную пустую область."""
        cell = (row, col)
        if self.state != "play" or cell in self.flags or cell in self.revealed:
            return

        if self.first_move:
            self.place_mines(row, col)
            self.first_move = False

        if cell in self.mines:
            self.revealed.update(self.mines)
            self.state = "lost"
            return

        queue = deque([cell])
        while queue:
            current = queue.popleft()
            if current in self.revealed or current in self.flags:
                continue
            self.revealed.add(current)
            cr, cc = current
            if self.numbers[cr][cc] == 0:
                for neighbor in self.neighbors(cr, cc):
                    if neighbor not in self.mines and neighbor not in self.revealed:
                        queue.append(neighbor)

        if len(self.revealed) == self.rows * self.cols - self.mine_count:
            self.state = "won"
            self.flags = set(self.mines)
            self.wins += 1

    def toggle_flag(self, row, col):
        """Поставить или снять флаг на закрытой клетке."""
        cell = (row, col)
        if self.state != "play" or cell in self.revealed:
            return
        if cell in self.flags:
            self.flags.remove(cell)
        elif len(self.flags) < self.mine_count:
            self.flags.add(cell)

    def cell_at(self, pos):
        """Преобразовать экранные координаты в клетку или вернуть None."""
        x, y = pos
        col = (x - self.board_left) // self.cell_size
        row = (y - self.board_top) // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None

    def handle_events(self):
        """Обработать ввод. False означает возврат в главное меню."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                cell = self.cell_at(event.pos)
                if cell is not None:
                    if event.button == 1:
                        self.reveal(*cell)
                    else:
                        self.toggle_flag(*cell)
        return True

    def draw_flag(self, rect):
        """Нарисовать флаг без зависимости от emoji-шрифтов."""
        pole_x = rect.x + rect.width * 2 // 5
        pygame.draw.line(
            self.screen, TEXT,
            (pole_x, rect.y + 9), (pole_x, rect.bottom - 9), 3,
        )
        pygame.draw.polygon(
            self.screen, FLAG,
            [(pole_x, rect.y + 9), (rect.right - 9, rect.y + 16), (pole_x, rect.y + 24)],
        )
        pygame.draw.line(
            self.screen, TEXT,
            (rect.x + 10, rect.bottom - 9), (rect.right - 10, rect.bottom - 9), 3,
        )

    def draw_board(self):
        mouse = pygame.mouse.get_pos()
        for row in range(self.rows):
            for col in range(self.cols):
                cell = (row, col)
                rect = pygame.Rect(
                    self.board_left + col * self.cell_size,
                    self.board_top + row * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                if cell in self.revealed:
                    color = BAD if cell in self.mines else (55, 59, 75)
                else:
                    color = PANEL_HOVER if rect.collidepoint(mouse) and self.state == "play" else PANEL
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRID, rect, 1)

                if cell in self.flags and cell not in self.revealed:
                    self.draw_flag(rect)
                elif cell in self.revealed and cell in self.mines:
                    pygame.draw.circle(self.screen, (20, 20, 25), rect.center, self.cell_size // 5)
                    pygame.draw.circle(self.screen, TEXT, rect.center, self.cell_size // 5, 2)
                elif cell in self.revealed:
                    number = self.numbers[row][col]
                    if number:
                        surf = self.font_cell.render(str(number), True, NUMBER_COLORS[number])
                        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw(self):
        self.screen.fill(BG)
        title = self.font_title.render("Сапёр", True, TEXT)
        self.screen.blit(title, (30, 22))

        remaining = self.mine_count - len(self.flags)
        info = self.font_text.render(
            f"Мин: {remaining}    Побед: {self.wins}", True, MUTED
        )
        self.screen.blit(info, info.get_rect(topright=(self.width - 30, 31)))

        self.draw_board()

        if self.state == "won":
            message, color = "Поле очищено! R — новая игра", GOOD
        elif self.state == "lost":
            message, color = "Вы подорвались. R — новая игра", BAD
        else:
            message, color = "ЛКМ — открыть, ПКМ — флаг", MUTED
        status = self.font_text.render(message, True, color)
        self.screen.blit(status, status.get_rect(center=(self.width // 2, self.height - 42)))

        hint = self.font_small.render("R — заново, Esc — в меню", True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 17)))
        pygame.display.flip()

    def run(self):
        """Игровой цикл; возвращает число побед за сессию."""
        while True:
            if not self.handle_events():
                break
            self.draw()
            self.clock.tick(FPS)
        return self.wins or None


def run(screen, clock):
    """Точка входа для главного меню GameBox."""
    pygame.display.set_caption("Сапёр")
    return Minesweeper(screen, clock).run()


if __name__ == "__main__":
    pygame.init()
    window = pygame.display.set_mode((800, 600))
    run(window, pygame.time.Clock())
    pygame.quit()
