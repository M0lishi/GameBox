"""Крестики-нолики для GameBox.

Игра для двух игроков за одним компьютером. ЛКМ ставит знак в выбранную
клетку, R начинает новый раунд, Esc возвращает в главное меню.
"""
import sys

import pygame

FPS = 60
BOARD_SIZE = 3

BG = (24, 26, 35)
PANEL = (40, 44, 60)
PANEL_HOVER = (62, 70, 100)
GRID = (105, 113, 140)
TEXT = (235, 237, 245)
MUTED = (140, 146, 165)
X_COLOR = (96, 165, 250)
O_COLOR = (255, 196, 80)
GOOD = (80, 200, 120)
FONT_NAMES = "arial,segoeui,dejavusans,liberationsans,freesans"


class TicTacToe:
    """Состояние, правила и интерфейс игры."""

    WINNING_LINES = (
        ((0, 0), (0, 1), (0, 2)),
        ((1, 0), (1, 1), (1, 2)),
        ((2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 1), (1, 1), (2, 1)),
        ((0, 2), (1, 2), (2, 2)),
        ((0, 0), (1, 1), (2, 2)),
        ((0, 2), (1, 1), (2, 0)),
    )

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()

        self.cell_size = min(140, (self.height - 160) // BOARD_SIZE)
        self.board_pixels = self.cell_size * BOARD_SIZE
        self.board_left = (self.width - self.board_pixels) // 2
        self.board_top = 105

        self.font_title = pygame.font.SysFont(FONT_NAMES, 40, bold=True)
        self.font_text = pygame.font.SysFont(FONT_NAMES, 24)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 18)

        self.scores = {"X": 0, "O": 0}
        self.draws = 0
        self.starting_player = "X"
        self.reset()

    def reset(self):
        """Начать новый раунд, поочерёдно меняя первого игрока."""
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = self.starting_player
        self.winner = None
        self.winning_line = None
        self.game_over = False

    def start_next_round(self):
        """Начать раунд; право первого хода переходит другому игроку."""
        self.starting_player = "O" if self.starting_player == "X" else "X"
        self.reset()

    def find_winner(self):
        """Вернуть победителя и выигрышную линию либо (None, None)."""
        for line in self.WINNING_LINES:
            values = [self.board[row][col] for row, col in line]
            if values[0] is not None and values.count(values[0]) == BOARD_SIZE:
                return values[0], line
        return None, None

    def make_move(self, row, col):
        """Поставить знак текущего игрока, если ход допустим."""
        if self.game_over or self.board[row][col] is not None:
            return False

        self.board[row][col] = self.current_player
        winner, line = self.find_winner()
        if winner is not None:
            self.winner = winner
            self.winning_line = line
            self.scores[winner] += 1
            self.game_over = True
        elif all(cell is not None for board_row in self.board for cell in board_row):
            self.draws += 1
            self.game_over = True
        else:
            self.current_player = "O" if self.current_player == "X" else "X"
        return True

    def cell_at(self, pos):
        """Преобразовать координаты клика в клетку поля."""
        x, y = pos
        col = (x - self.board_left) // self.cell_size
        row = (y - self.board_top) // self.cell_size
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
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
                    self.start_next_round()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cell = self.cell_at(event.pos)
                if cell is not None:
                    self.make_move(*cell)
        return True

    def cell_rect(self, row, col):
        """Экранный прямоугольник клетки."""
        return pygame.Rect(
            self.board_left + col * self.cell_size,
            self.board_top + row * self.cell_size,
            self.cell_size,
            self.cell_size,
        )

    def draw_x(self, rect):
        margin = rect.width // 4
        pygame.draw.line(
            self.screen, X_COLOR,
            (rect.left + margin, rect.top + margin),
            (rect.right - margin, rect.bottom - margin), 10,
        )
        pygame.draw.line(
            self.screen, X_COLOR,
            (rect.right - margin, rect.top + margin),
            (rect.left + margin, rect.bottom - margin), 10,
        )

    def draw_o(self, rect):
        pygame.draw.circle(
            self.screen, O_COLOR, rect.center, rect.width // 4, 10
        )

    def draw_board(self):
        mouse = pygame.mouse.get_pos()
        winning_cells = set(self.winning_line or ())

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = self.cell_rect(row, col)
                if (row, col) in winning_cells:
                    color = (42, 78, 62)
                elif rect.collidepoint(mouse) and not self.game_over and self.board[row][col] is None:
                    color = PANEL_HOVER
                else:
                    color = PANEL
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRID, rect, 2)

                mark = self.board[row][col]
                if mark == "X":
                    self.draw_x(rect)
                elif mark == "O":
                    self.draw_o(rect)

        if self.winning_line:
            first_row, first_col = self.winning_line[0]
            last_row, last_col = self.winning_line[-1]
            pygame.draw.line(
                self.screen, GOOD,
                self.cell_rect(first_row, first_col).center,
                self.cell_rect(last_row, last_col).center,
                6,
            )

    def draw(self):
        self.screen.fill(BG)

        title = self.font_title.render("Крестики-нолики", True, TEXT)
        self.screen.blit(title, (30, 22))
        score = self.font_text.render(
            f"X: {self.scores['X']}    O: {self.scores['O']}    Ничьи: {self.draws}",
            True, MUTED,
        )
        self.screen.blit(score, score.get_rect(topright=(self.width - 30, 31)))

        self.draw_board()

        if self.winner:
            message = f"Победил игрок {self.winner}! R — новый раунд"
            color = GOOD
        elif self.game_over:
            message = "Ничья! R — новый раунд"
            color = MUTED
        else:
            message = f"Ход игрока {self.current_player}"
            color = X_COLOR if self.current_player == "X" else O_COLOR
        status = self.font_text.render(message, True, color)
        self.screen.blit(status, status.get_rect(center=(self.width // 2, self.height - 40)))

        hint = self.font_small.render("ЛКМ — ход, R — заново, Esc — в меню", True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 15)))
        pygame.display.flip()

    def run(self):
        """Игровой цикл; возвращает суммарное число побед за сессию."""
        while True:
            if not self.handle_events():
                break
            self.draw()
            self.clock.tick(FPS)
        wins = self.scores["X"] + self.scores["O"]
        return wins or None


def run(screen, clock):
    """Точка входа для главного меню GameBox."""
    pygame.display.set_caption("Крестики-нолики")
    return TicTacToe(screen, clock).run()


if __name__ == "__main__":
    pygame.init()
    window = pygame.display.set_mode((800, 600))
    run(window, pygame.time.Clock())
    pygame.quit()
