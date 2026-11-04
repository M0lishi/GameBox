"""Модульные тесты игровой логики «Сапёра»."""
import os
import unittest
from unittest.mock import patch

# Тестам не нужно настоящее окно: Pygame работает через виртуальный видеодрайвер.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from games.minesweeper import SAFE_CELL_POINTS, WIN_BONUS, Minesweeper


class MinesweeperTestCase(unittest.TestCase):
    """Проверки правил игры без запуска интерактивного игрового цикла."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((800, 600))
        cls.clock = pygame.time.Clock()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make_game(self, rows=5, cols=5, mine_count=3):
        return Minesweeper(self.screen, self.clock, rows, cols, mine_count)

    def configure_board(self, game, mines):
        """Установить известные мины и пересчитать числа вокруг них."""
        game.first_move = False
        game.mines = set(mines)
        game.numbers = [[0 for _ in range(game.cols)] for _ in range(game.rows)]
        for row in range(game.rows):
            for col in range(game.cols):
                if (row, col) not in game.mines:
                    game.numbers[row][col] = sum(
                        neighbor in game.mines
                        for neighbor in game.neighbors(row, col)
                    )

    def test_rejects_invalid_mine_count(self):
        with self.assertRaises(ValueError):
            self.make_game(rows=2, cols=2, mine_count=0)
        with self.assertRaises(ValueError):
            self.make_game(rows=2, cols=2, mine_count=4)

    def test_neighbors_respect_board_edges(self):
        game = self.make_game()

        self.assertEqual(set(game.neighbors(0, 0)), {(0, 1), (1, 0), (1, 1)})
        self.assertEqual(len(set(game.neighbors(2, 2))), 8)

    def test_first_move_and_its_neighbors_are_safe(self):
        game = self.make_game(rows=5, cols=5, mine_count=3)
        generated_mines = [(0, 0), (0, 4), (4, 0)]

        with patch("games.minesweeper.random.sample", return_value=generated_mines):
            game.reveal(2, 2)

        safe_area = {(2, 2), *game.neighbors(2, 2)}
        self.assertEqual(game.mines, set(generated_mines))
        self.assertTrue(safe_area.isdisjoint(game.mines))
        self.assertFalse(game.first_move)
        self.assertIn((2, 2), game.revealed)

    def test_numbers_show_adjacent_mine_count(self):
        game = self.make_game(rows=3, cols=3, mine_count=2)
        self.configure_board(game, {(0, 0), (2, 2)})

        self.assertEqual(game.numbers[0][1], 1)
        self.assertEqual(game.numbers[1][1], 2)
        self.assertEqual(game.numbers[2][1], 1)

    def test_empty_cell_reveals_connected_area(self):
        game = self.make_game(rows=4, cols=4, mine_count=1)
        self.configure_board(game, {(3, 3)})

        game.reveal(0, 0)

        self.assertEqual(len(game.revealed), 15)
        self.assertNotIn((3, 3), game.revealed)
        self.assertEqual(game.state, "won")

    def test_flag_can_be_toggled_and_blocks_reveal(self):
        game = self.make_game(rows=3, cols=3, mine_count=1)
        self.configure_board(game, {(2, 2)})

        game.toggle_flag(0, 0)
        game.reveal(0, 0)
        self.assertIn((0, 0), game.flags)
        self.assertNotIn((0, 0), game.revealed)

        game.toggle_flag(0, 0)
        self.assertNotIn((0, 0), game.flags)

    def test_number_of_flags_cannot_exceed_number_of_mines(self):
        game = self.make_game(rows=3, cols=3, mine_count=1)

        game.toggle_flag(0, 0)
        game.toggle_flag(0, 1)

        self.assertEqual(game.flags, {(0, 0)})

    def test_opening_mine_ends_game_without_extra_points(self):
        game = self.make_game(rows=2, cols=2, mine_count=1)
        self.configure_board(game, {(1, 1)})
        game.reveal(0, 0)
        score_before_mine = game.score

        game.reveal(1, 1)

        self.assertEqual(game.state, "lost")
        self.assertIn((1, 1), game.revealed)
        self.assertEqual(game.score, score_before_mine)
        self.assertEqual(game.session_best, score_before_mine)

    def test_victory_awards_points_and_places_flags(self):
        game = self.make_game(rows=2, cols=2, mine_count=1)
        self.configure_board(game, {(1, 1)})

        game.reveal(0, 0)
        game.reveal(0, 1)
        game.reveal(1, 0)

        expected_score = 3 * SAFE_CELL_POINTS + WIN_BONUS
        self.assertEqual(game.state, "won")
        self.assertEqual(game.score, expected_score)
        self.assertEqual(game.session_best, expected_score)
        self.assertEqual(game.wins, 1)
        self.assertEqual(game.flags, {(1, 1)})

    def test_reset_clears_board_and_keeps_session_record(self):
        game = self.make_game(rows=3, cols=3, mine_count=1)
        game.score = 70
        game.revealed = {(0, 0)}
        game.flags = {(2, 2)}
        game.state = "lost"

        game.reset()

        self.assertEqual(game.score, 0)
        self.assertEqual(game.session_best, 70)
        self.assertEqual(game.revealed, set())
        self.assertEqual(game.flags, set())
        self.assertEqual(game.state, "play")
        self.assertTrue(game.first_move)


if __name__ == "__main__":
    unittest.main()
