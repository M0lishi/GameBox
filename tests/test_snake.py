"""Тесты игры «Змейка» (games/snake.py), unittest."""


import os
import sys
import unittest
from unittest import mock

# Окно не нужно: pygame работает без экрана и звука (важно для CI и серверов)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Чтобы импортировать games.snake, как бы ни запускали тесты
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from games import snake  # noqa: E402
from games.snake import Direction, Food, Game, Position, Snake  # noqa: E402


def key_event(key, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode)


class PositionTests(unittest.TestCase):
    def test_equal_positions(self):
        self.assertEqual(Position(2, 3), Position(2, 3))

    def test_different_positions(self):
        self.assertNotEqual(Position(2, 3), Position(3, 2))

    def test_not_equal_to_tuple(self):
        self.assertNotEqual(Position(2, 3), (2, 3))

    def test_hashable_for_sets(self):
        self.assertEqual(len({Position(1, 1), Position(1, 1), Position(2, 1)}), 2)


class SnakeTests(unittest.TestCase):
    def setUp(self):
        self.snake = Snake(10, 10, 20)

    def test_initial_state(self):
        body = self.snake.body
        self.assertEqual(len(body), 3)
        self.assertEqual(body[0], Position(5, 5))
        self.assertEqual(self.snake.direction, Direction.RIGHT)
        self.assertEqual(self.snake.direction_queue, [])
        self.assertFalse(self.snake.grow_pending)

    def test_move_shifts_body_forward(self):
        self.snake.move()
        self.assertEqual(
            self.snake.body, [Position(6, 5), Position(5, 5), Position(4, 5)]
        )

    def test_grow_adds_one_segment_once(self):
        self.snake.grow()
        self.snake.move()
        self.assertEqual(len(self.snake.body), 4)
        self.snake.move()
        self.assertEqual(len(self.snake.body), 4)

    def test_opposite_direction_is_ignored(self):
        self.snake.set_direction(Direction.LEFT)  # змейка идёт вправо
        self.snake.move()
        self.assertEqual(self.snake.body[0], Position(6, 5))

    def test_same_direction_is_not_queued(self):
        self.snake.set_direction(Direction.RIGHT)
        self.assertEqual(self.snake.direction_queue, [])

    def test_turn_applies_on_next_move(self):
        self.snake.set_direction(Direction.UP)
        self.snake.move()
        self.assertEqual(self.snake.body[0], Position(5, 4))
        self.assertEqual(self.snake.direction, Direction.UP)

    def test_fast_double_turn_does_not_kill_snake(self):
        # Раньше "вверх" и сразу "влево" при движении вправо разворачивали змейку в себя
        self.snake.set_direction(Direction.UP)
        self.snake.set_direction(Direction.LEFT)
        self.snake.move()
        self.snake.move()
        self.assertEqual(self.snake.body[0], Position(4, 4))
        self.assertFalse(self.snake.check_collision())

    def test_direction_queue_holds_at_most_two_turns(self):
        self.snake.set_direction(Direction.UP)
        self.snake.set_direction(Direction.LEFT)
        self.snake.set_direction(Direction.DOWN)
        self.assertEqual(self.snake.direction_queue, [Direction.UP, Direction.LEFT])

    def test_no_collision_inside_field(self):
        self.assertFalse(self.snake.check_collision())

    def test_wall_collisions(self):
        for x, y in [(-1, 0), (10, 0), (0, -1), (0, 10)]:
            with self.subTest(head=(x, y)):
                self.snake.body[0] = Position(x, y)
                self.assertTrue(self.snake.check_collision())

    def test_self_collision(self):
        self.snake.body = [
            Position(2, 2), Position(3, 2), Position(3, 3), Position(2, 3), Position(2, 2)
        ]
        self.assertTrue(self.snake.check_collision())

    def test_moving_into_tail_cell_is_allowed(self):
        # Хвост в этот же ход освобождает клетку, значит, это не столкновение
        self.snake.body = [Position(3, 3), Position(3, 2), Position(2, 2), Position(2, 3)]
        self.snake.direction = Direction.LEFT
        self.snake.move()
        self.assertEqual(self.snake.body[0], Position(2, 3))
        self.assertFalse(self.snake.check_collision())

    def test_check_food(self):
        head = self.snake.body[0]
        self.assertTrue(self.snake.check_food(Position(head.x, head.y)))
        self.assertFalse(self.snake.check_food(Position(head.x + 1, head.y)))

    def test_reset_restores_start_state(self):
        self.snake.set_direction(Direction.UP)
        self.snake.grow()
        self.snake.move()
        self.snake.reset()
        self.assertEqual(len(self.snake.body), 3)
        self.assertEqual(self.snake.direction, Direction.RIGHT)
        self.assertEqual(self.snake.direction_queue, [])
        self.assertFalse(self.snake.grow_pending)


class FoodTests(unittest.TestCase):
    def test_food_never_appears_on_snake(self):
        food = Food(10, 10, 20)
        occupied = [Position(x, y) for x in range(10) for y in range(5)]  # половина поля
        for _ in range(200):
            self.assertTrue(food.randomize(occupied))
            self.assertNotIn(food.position, occupied)

    def test_food_goes_into_the_only_free_cell(self):
        food = Food(5, 5, 20)
        free = Position(3, 4)
        occupied = [Position(x, y) for x in range(5) for y in range(5) if (x, y) != (3, 4)]
        self.assertTrue(food.randomize(occupied))
        self.assertEqual(food.position, free)

    def test_full_board_returns_false(self):
        food = Food(3, 3, 20)
        occupied = [Position(x, y) for x in range(3) for y in range(3)]
        self.assertFalse(food.randomize(occupied))
        self.assertIsNone(food.position)

    def test_draw_without_position_does_not_crash(self):
        food = Food(3, 3, 20)
        food.position = None
        food.draw(pygame.Surface((60, 60)))


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((800, 600))
        cls.clock = pygame.time.Clock()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        pygame.event.clear()
        # Тесты не должны зависеть от реального scores.json
        patcher = mock.patch.object(snake, "scores", None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.game = Game(self.screen, self.clock)

    def put_food_ahead(self):
        head = self.game.snake.body[0]
        dx, dy = self.game.snake.direction
        self.game.food.position = Position(head.x + dx, head.y + dy)

    def test_grid_follows_window_size(self):
        self.assertEqual((self.game.grid_width, self.game.grid_height), (40, 30))

    def test_start_state(self):
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.paused)
        self.assertEqual(self.game.speed, snake.START_SPEED)
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_eating_food_gives_points_and_growth(self):
        self.put_food_ahead()
        self.game.update()
        self.assertEqual(self.game.score, 10)
        self.assertTrue(self.game.snake.grow_pending)
        self.assertNotIn(self.game.food.position, self.game.snake.body)

    def test_speed_grows_every_50_points(self):
        self.game.score = 40
        self.put_food_ahead()
        self.game.update()  # 50 очков
        self.assertEqual(self.game.speed, snake.START_SPEED + 2)

    def test_speed_is_capped(self):
        self.game.score = 5000
        self.put_food_ahead()
        self.game.update()
        self.assertEqual(self.game.speed, snake.MAX_SPEED)

    def test_hitting_wall_ends_game(self):
        self.game.food.position = Position(0, 0)  # далеко от пути змейки
        for _ in range(60):
            if self.game.game_over:
                break
            self.game.update()
        self.assertTrue(self.game.game_over)
        self.assertFalse(self.game.won)

    def test_filling_the_board_is_a_win(self):
        g = self.game
        cells = [Position(x, y) for x in range(g.grid_width) for y in range(g.grid_height)]
        head, target = Position(10, 10), Position(11, 10)
        g.snake.body = [head] + [c for c in cells if c not in (head, target)]
        g.snake.direction = Direction.RIGHT
        g.snake.grow_pending = True
        g.food.position = target
        g.update()
        self.assertTrue(g.won)
        self.assertTrue(g.game_over)

    def test_session_best_keeps_maximum(self):
        self.game.score = 30
        self.game.finish()
        self.assertEqual(self.game.session_best, 30)
        self.game.restart()
        self.game.score = 10
        self.game.finish()
        self.assertEqual(self.game.session_best, 30)

    def test_restart_resets_game(self):
        self.game.score = 50
        self.game.speed = 20
        self.game.game_over = True
        self.game.won = True
        self.game.restart()
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.speed, snake.START_SPEED)
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.won)
        self.assertEqual(len(self.game.snake.body), 3)

    def test_high_score_taken_from_scores_module(self):
        fake_scores = mock.MagicMock()
        fake_scores.best.return_value = 70
        with mock.patch.object(snake, "scores", fake_scores):
            game = Game(self.screen, self.clock)
        self.assertEqual(game.high_score, 70)
        fake_scores.best.assert_called_with("snake")

    def test_high_score_survives_scores_error(self):
        fake_scores = mock.MagicMock()
        fake_scores.best.side_effect = OSError("нет файла")
        with mock.patch.object(snake, "scores", fake_scores):
            game = Game(self.screen, self.clock)
        self.assertEqual(game.high_score, 0)

    def test_arrow_and_wasd_keys_queue_turns(self):
        pygame.event.post(key_event(pygame.K_UP))
        self.assertTrue(self.game.handle_events())
        self.assertEqual(self.game.snake.direction_queue, [Direction.UP])

        self.game.snake.direction_queue.clear()
        pygame.event.post(key_event(pygame.K_s))
        self.game.handle_events()
        self.assertEqual(self.game.snake.direction_queue, [Direction.DOWN])

    def test_pause_toggles_and_blocks_turns(self):
        pygame.event.post(key_event(pygame.K_p))
        self.game.handle_events()
        self.assertTrue(self.game.paused)

        pygame.event.post(key_event(pygame.K_UP))
        self.game.handle_events()
        self.assertEqual(self.game.snake.direction_queue, [])

        pygame.event.post(key_event(pygame.K_p))
        self.game.handle_events()
        self.assertFalse(self.game.paused)

    def test_space_restarts_only_after_game_over(self):
        self.game.score = 20
        pygame.event.post(key_event(pygame.K_SPACE))
        self.game.handle_events()
        self.assertEqual(self.game.score, 20)  # во время игры пробел ничего не делает

        self.game.game_over = True
        pygame.event.post(key_event(pygame.K_SPACE))
        self.game.handle_events()
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.score, 0)

    def test_escape_returns_to_menu(self):
        pygame.event.post(key_event(pygame.K_ESCAPE))
        self.assertFalse(self.game.handle_events())

    def test_run_returns_none_if_no_score(self):
        pygame.event.post(key_event(pygame.K_ESCAPE))
        self.assertIsNone(self.game.run())

    def test_run_returns_session_best(self):
        self.game.score = 30
        self.game.finish()
        pygame.event.post(key_event(pygame.K_ESCAPE))
        self.assertEqual(self.game.run(), 30)

    def test_module_run_entry_point(self):
        # Точка входа, которую вызывает главное меню
        pygame.event.post(key_event(pygame.K_ESCAPE))
        self.assertIsNone(snake.run(self.screen, self.clock))

    def test_draw_works_in_every_state(self):
        self.game.draw()
        self.game.paused = True
        self.game.draw()
        self.game.paused = False
        self.game.game_over = True
        self.game.draw()
        self.game.won = True
        self.game.draw()


if __name__ == "__main__":
    unittest.main()
