"""Змейка для GameBox.

Подключается к главному меню через run(screen, clock):
игра рисует на переданном окне, по Esc возвращает управление в меню
и отдаёт лучший результат за сессию (или None, если очков не набрано).
"""
import random
import sys

import pygame

try:
    import scores  # общая таблица рекордов (лежит в корне проекта)
except ImportError:  # запуск файла отдельно, без главного меню
    scores = None

FPS = 60          # частота отрисовки и опроса клавиатуры
START_SPEED = 10  # ходов змейки в секунду
MAX_SPEED = 25
FONT_NAMES = "arial,segoeui,dejavusans,liberationsans,freesans"


class Color:
    """Контейнер для цветов, используемых в игре"""
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 200, 0)
    DARK_GREEN = (0, 150, 0)
    BLUE = (0, 0, 200)
    GRAY = (128, 128, 128)
    GRID = (35, 35, 35)
    YELLOW = (255, 255, 0)


class Position:
    """Представляет позицию на игровом поле"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Position) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Position({self.x}, {self.y})"


class Direction:
    """Перечисление направлений движения змейки"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class Food:
    """Класс, представляющий еду на игровом поле"""
    def __init__(self, grid_width: int, grid_height: int, block_size: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.block_size = block_size
        self.position = None

    def randomize(self, occupied=()) -> bool:
        """Ставит еду в случайную СВОБОДНУЮ клетку.

        Возвращает False, если свободных клеток не осталось (змейка заполнила поле).
        """
        busy = {(p.x, p.y) for p in occupied}
        free = [
            (x, y)
            for x in range(self.grid_width)
            for y in range(self.grid_height)
            if (x, y) not in busy
        ]
        if not free:
            self.position = None
            return False
        self.position = Position(*random.choice(free))
        return True

    def draw(self, surface):
        """Отрисовка еды"""
        if self.position is None:
            return
        rect = pygame.Rect(
            self.position.x * self.block_size,
            self.position.y * self.block_size,
            self.block_size,
            self.block_size
        )
        pygame.draw.rect(surface, Color.RED, rect)
        pygame.draw.rect(surface, Color.WHITE, rect, 2)


class Snake:
    """Класс змейки"""
    def __init__(self, grid_width: int, grid_height: int, block_size: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.block_size = block_size
        self.reset()

    def reset(self):
        """Сбрасывает змейку в начальное состояние"""
        start_x = self.grid_width // 2
        start_y = self.grid_height // 2
        self.body = [
            Position(start_x, start_y),
            Position(start_x - 1, start_y),
            Position(start_x - 2, start_y)
        ]
        self.direction = Direction.RIGHT
        self.direction_queue = []  # нажатия, ожидающие следующего хода
        self.grow_pending = False

    def set_direction(self, new_direction: tuple):
        """Ставит поворот в очередь.

        Очередь нужна, чтобы два быстрых нажатия за один ход (например, вверх и сразу влево)
        не развернули змейку на 180 градусов внутрь самой себя.
        """
        last = self.direction_queue[-1] if self.direction_queue else self.direction
        opposite = (-last[0], -last[1])
        if new_direction != opposite and new_direction != last and len(self.direction_queue) < 2:
            self.direction_queue.append(new_direction)

    def move(self):
        """Перемещает змейку в текущем направлении"""
        if self.direction_queue:
            self.direction = self.direction_queue.pop(0)

        head = self.body[0]
        new_head = Position(
            head.x + self.direction[0],
            head.y + self.direction[1]
        )
        self.body.insert(0, new_head)

        if self.grow_pending:
            self.grow_pending = False
        else:
            self.body.pop()

    def grow(self):
        """Увеличивает длину змейки"""
        self.grow_pending = True

    def check_collision(self) -> bool:
        """Проверяет столкновение со стенами или с собой"""
        head = self.body[0]

        # Столкновение со стенами
        if head.x < 0 or head.x >= self.grid_width or head.y < 0 or head.y >= self.grid_height:
            return True

        # Столкновение с собой
        if head in self.body[1:]:
            return True

        return False

    def check_food(self, food_position: Position) -> bool:
        """Проверяет, съела ли змейка еду"""
        return self.body[0] == food_position

    def draw(self, surface):
        """Отрисовка змейки"""
        for i, segment in enumerate(self.body):
            rect = pygame.Rect(
                segment.x * self.block_size,
                segment.y * self.block_size,
                self.block_size,
                self.block_size
            )
            color = Color.GREEN if i == 0 else Color.DARK_GREEN
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, Color.WHITE, rect, 1)


class Game:
    """Основной класс игры"""
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.block_size = 20
        # Поле подстраивается под размер окна меню (800x600 -> 40x30 клеток)
        self.screen_width, self.screen_height = screen.get_size()
        self.grid_width = self.screen_width // self.block_size
        self.grid_height = self.screen_height // self.block_size

        self.font_large = pygame.font.SysFont(FONT_NAMES, 48, bold=True)
        self.font_medium = pygame.font.SysFont(FONT_NAMES, 32)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 20)

        self.snake = Snake(self.grid_width, self.grid_height, self.block_size)
        self.food = Food(self.grid_width, self.grid_height, self.block_size)
        self.food.randomize(self.snake.body)

        self.score = 0
        self.session_best = 0
        self.high_score = self._load_record()
        self.game_over = False
        self.won = False
        self.paused = False
        self.speed = START_SPEED
        self.last_move = pygame.time.get_ticks()

    @staticmethod
    def _load_record() -> int:
        """Рекорд из общей таблицы (если запущено из меню)."""
        if scores is None:
            return 0
        try:
            return scores.best("snake") or 0
        except Exception:
            return 0

    def handle_events(self):
        """Обработка пользовательского ввода. False - выйти в меню."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.restart()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    self.last_move = pygame.time.get_ticks()
                elif not self.paused:
                    key_map = {
                        pygame.K_UP: Direction.UP,
                        pygame.K_DOWN: Direction.DOWN,
                        pygame.K_LEFT: Direction.LEFT,
                        pygame.K_RIGHT: Direction.RIGHT,
                        pygame.K_w: Direction.UP,
                        pygame.K_s: Direction.DOWN,
                        pygame.K_a: Direction.LEFT,
                        pygame.K_d: Direction.RIGHT,
                    }
                    if event.key in key_map:
                        self.snake.set_direction(key_map[event.key])

        return True

    def finish(self):
        """Конец игры: проигрыш или победа."""
        self.game_over = True
        self.session_best = max(self.session_best, self.score)
        self.high_score = max(self.high_score, self.score)

    def update(self):
        """Один ход игры"""
        self.snake.move()

        if self.snake.check_collision():
            self.finish()
            return

        if self.snake.check_food(self.food.position):
            self.snake.grow()
            self.score += 10
            # Увеличиваем скорость каждые 50 очков
            self.speed = min(START_SPEED + (self.score // 50) * 2, MAX_SPEED)
            if not self.food.randomize(self.snake.body):
                self.won = True  # поле заполнено целиком
                self.finish()

    def draw(self):
        """Отрисовка всех элементов игры"""
        self.screen.fill(Color.BLACK)

        # Рисуем сетку
        field_w = self.grid_width * self.block_size
        field_h = self.grid_height * self.block_size
        for x in range(0, field_w + 1, self.block_size):
            pygame.draw.line(self.screen, Color.GRID, (x, 0), (x, field_h))
        for y in range(0, field_h + 1, self.block_size):
            pygame.draw.line(self.screen, Color.GRID, (0, y), (field_w, y))

        self.food.draw(self.screen)
        self.snake.draw(self.screen)

        # Отображаем счет
        score_text = self.font_small.render(f"Счет: {self.score}", True, Color.WHITE)
        self.screen.blit(score_text, (10, 10))

        high_score_text = self.font_small.render(f"Рекорд: {self.high_score}", True, Color.WHITE)
        high_rect = high_score_text.get_rect(topright=(self.screen_width - 10, 10))
        self.screen.blit(high_score_text, high_rect)

        if self.game_over:
            if self.won:
                self.draw_overlay("ПОБЕДА!", Color.YELLOW)
            else:
                self.draw_overlay("ИГРА ОКОНЧЕНА", Color.RED)
        elif self.paused:
            self.draw_overlay("ПАУЗА", Color.WHITE, hint="P - продолжить, ESC - в меню", show_score=False)

        pygame.display.flip()

    def draw_overlay(self, title, color, hint="ПРОБЕЛ - заново, ESC - в меню", show_score=True):
        """Затемнение с заголовком (конец игры или пауза)"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill(Color.BLACK)
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.screen_width // 2, self.screen_height // 2

        title_text = self.font_large.render(title, True, color)
        self.screen.blit(title_text, title_text.get_rect(center=(cx, cy - 50)))

        if show_score:
            score_text = self.font_medium.render(f"Счет: {self.score}", True, Color.WHITE)
            self.screen.blit(score_text, score_text.get_rect(center=(cx, cy + 10)))

        hint_text = self.font_medium.render(hint, True, Color.YELLOW)
        self.screen.blit(hint_text, hint_text.get_rect(center=(cx, cy + 60)))

    def restart(self):
        """Перезапуск игры"""
        self.snake.reset()
        self.food.randomize(self.snake.body)
        self.score = 0
        self.game_over = False
        self.won = False
        self.speed = START_SPEED
        self.last_move = pygame.time.get_ticks()

    def run(self):
        """Игровой цикл. Возвращает лучший результат за сессию или None."""
        self.last_move = pygame.time.get_ticks()
        while True:
            if not self.handle_events():
                break

            # Ходы идут по таймеру, а отрисовка и ввод - с постоянной частотой FPS,
            # поэтому управление не "залипает" на медленной скорости.
            now = pygame.time.get_ticks()
            if not (self.game_over or self.paused) and now - self.last_move >= 1000 // self.speed:
                self.last_move = now
                self.update()

            self.draw()
            self.clock.tick(FPS)

        return self.session_best or None


def run(screen, clock):
    """Точка входа для главного меню GameBox."""
    pygame.display.set_caption("Змейка")
    return Game(screen, clock).run()


if __name__ == "__main__":
    pygame.init()
    window = pygame.display.set_mode((800, 600))
    run(window, pygame.time.Clock())
    pygame.quit()
