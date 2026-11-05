import os
import unittest
from unittest.mock import Mock, mock_open, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from games import hangman


class LoadWordsTests(unittest.TestCase):
    def test_reads_utf8_file_and_normalizes_words(self):
        reader = mock_open(read_data="  кошка  \nёжик\nДоМ\n")
        with patch("builtins.open", reader):
            words = hangman.load_words()
        self.assertEqual(words, ["КОШКА", "ЕЖИК", "ДОМ"])
        reader.assert_called_once_with(hangman.WORDS_FILE, "r", encoding="utf-8")

    def test_filters_short_empty_and_non_russian_entries(self):
        data = "\nя\nмы\ncat\nкот2\nдва слова\nкот-пёс\nкот!\nкот\n"
        with patch("builtins.open", mock_open(read_data=data)):
            self.assertEqual(hangman.load_words(), ["КОТ"])

    def test_empty_file_uses_default_words(self):
        with patch("builtins.open", mock_open(read_data="")):
            self.assertEqual(hangman.load_words(), hangman.DEFAULT_WORDS)

    def test_file_without_valid_words_uses_default_words(self):
        with patch("builtins.open", mock_open(read_data="123\nabc\nя\n")):
            self.assertEqual(hangman.load_words(), hangman.DEFAULT_WORDS)

    def test_missing_file_uses_default_words(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            self.assertEqual(hangman.load_words(), hangman.DEFAULT_WORDS)

    def test_unreadable_file_uses_default_words(self):
        with patch("builtins.open", side_effect=PermissionError):
            self.assertEqual(hangman.load_words(), hangman.DEFAULT_WORDS)


class HangmanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.addClassCleanup(pygame.quit)
        cls.screen = pygame.display.set_mode((800, 600))

    def setUp(self):
        words_patch = patch("games.hangman.load_words", return_value=["ДОМ", "КОШКА"])
        shuffle_patch = patch("games.hangman.random.shuffle")
        words_patch.start()
        self.addCleanup(words_patch.stop)
        shuffle_patch.start()
        self.addCleanup(shuffle_patch.stop)
        self.clock = Mock()
        self.game = hangman.Hangman(self.screen, self.clock)
        pygame.event.clear()

    def send_events(self, *events):
        with patch("games.hangman.pygame.event.get", return_value=list(events)):
            return self.game.handle_events()

    def press_key(self, key, text=""):
        return self.send_events(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=text))

    def win_round(self):
        for letter in dict.fromkeys(self.game.word):
            self.game.guess(letter)

    def lose_round(self):
        for letter in "БВГДЕЖ":
            self.game.guess(letter)

    def snapshot(self):
        return (self.game.word, self.game.guessed.copy(), self.game.mistakes,
                self.game.state, self.game.wins)

    def test_initial_round_has_no_guesses_mistakes_or_wins(self):
        self.assertEqual(self.snapshot(), ("КОШКА", set(), 0, "play", 0))

    def test_correct_letter_is_registered_without_mistake(self):
        self.game.guess("К")
        self.assertEqual(self.game.guessed, {"К"})
        self.assertEqual(self.game.mistakes, 0)
        self.assertEqual(self.game.state, "play")

    def test_wrong_letter_adds_one_mistake(self):
        self.game.guess("Б")
        self.assertEqual(self.game.guessed, {"Б"})
        self.assertEqual(self.game.mistakes, 1)
        self.assertEqual(self.game.state, "play")

    def test_repeated_correct_and_wrong_letters_do_not_change_state(self):
        for letter in ("К", "Б"):
            with self.subTest(letter=letter):
                self.game.guess(letter)
                before = self.snapshot()
                self.game.guess(letter)
                self.assertEqual(self.snapshot(), before)

    def test_all_distinct_letters_win_word_with_repeated_letter(self):
        for letter in "КОШ":
            self.game.guess(letter)
        self.assertEqual(self.game.state, "play")
        self.game.guess("А")
        self.assertEqual(self.game.state, "won")
        self.assertEqual(self.game.wins, 1)
        self.assertEqual(self.game.mistakes, 0)

    def test_sixth_wrong_letter_loses_round(self):
        self.assertEqual(hangman.MAX_MISTAKES, 6)
        for count, letter in enumerate("БВГДЕЖ", start=1):
            self.game.guess(letter)
            self.assertEqual(self.game.mistakes, count)
            self.assertEqual(self.game.state, "lost" if count == 6 else "play")
        self.assertEqual(self.game.wins, 0)

    def test_guesses_after_victory_do_not_change_result(self):
        self.win_round()
        before = self.snapshot()
        self.game.guess("Б")
        self.game.guess("А")
        self.assertEqual(self.snapshot(), before)

    def test_guesses_after_defeat_do_not_change_result(self):
        self.lose_round()
        before = self.snapshot()
        self.game.guess("К")
        self.game.guess("З")
        self.assertEqual(self.snapshot(), before)

    def test_new_word_resets_round_and_preserves_wins(self):
        self.game.guess("Б")
        self.win_round()
        self.game.new_word()
        self.assertEqual(self.snapshot(), ("ДОМ", set(), 0, "play", 1))

    def test_new_word_after_defeat_resets_mistakes_and_guesses(self):
        self.lose_round()
        self.game.new_word()
        self.assertEqual(self.snapshot(), ("ДОМ", set(), 0, "play", 0))

    def test_words_do_not_repeat_until_deck_is_exhausted(self):
        first = self.game.word
        self.game.new_word()
        self.assertEqual({first, self.game.word}, {"КОШКА", "ДОМ"})
        self.assertEqual(self.game.deck, [])
        self.assertEqual(self.game.words, ["ДОМ", "КОШКА"])
        self.game.new_word()
        self.assertEqual(self.game.word, "КОШКА")
        self.assertEqual(self.game.deck, ["ДОМ"])

    def test_wins_accumulate_across_rounds(self):
        self.win_round()
        self.game.new_word()
        self.win_round()
        self.assertEqual(self.game.wins, 2)

    def test_lowercase_russian_keyboard_input_is_accepted(self):
        self.assertTrue(self.press_key(pygame.K_r, "к"))
        self.assertEqual(self.game.guessed, {"К"})
        self.assertEqual(self.game.mistakes, 0)

    def test_keyboard_yo_is_normalized_to_ye(self):
        self.press_key(pygame.K_BACKQUOTE, "ё")
        self.assertEqual(self.game.guessed, {"Е"})
        self.assertEqual(self.game.mistakes, 1)

    def test_non_russian_text_input_is_ignored(self):
        before = self.snapshot()
        for key, text in ((pygame.K_a, "a"), (pygame.K_1, "1"),
                          (pygame.K_PERIOD, ".")):
            with self.subTest(text=text):
                self.press_key(key, text)
                self.assertEqual(self.snapshot(), before)

    def test_key_without_text_is_ignored(self):
        before = self.snapshot()
        self.press_key(pygame.K_LSHIFT)
        self.assertEqual(self.snapshot(), before)

    def test_left_click_selects_letter(self):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.game.letter_rects["К"].center)
        self.assertTrue(self.send_events(event))
        self.assertEqual(self.game.guessed, {"К"})
        self.assertEqual(self.game.mistakes, 0)

    def test_click_outside_keyboard_and_right_click_are_ignored(self):
        before = self.snapshot()
        self.send_events(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0)),
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3,
                               pos=self.game.letter_rects["К"].center),
        )
        self.assertEqual(self.snapshot(), before)

    def test_space_during_round_does_not_skip_word(self):
        self.game.guess("К")
        before = self.snapshot()
        self.press_key(pygame.K_SPACE, " ")
        self.assertEqual(self.snapshot(), before)

    def test_space_after_victory_starts_next_word(self):
        self.win_round()
        self.press_key(pygame.K_SPACE, " ")
        self.assertEqual(self.snapshot(), ("ДОМ", set(), 0, "play", 1))

    def test_space_after_defeat_starts_next_word(self):
        self.lose_round()
        self.press_key(pygame.K_SPACE, " ")
        self.assertEqual(self.snapshot(), ("ДОМ", set(), 0, "play", 0))

    def test_escape_returns_control_without_changing_round(self):
        before = self.snapshot()
        self.assertFalse(self.press_key(pygame.K_ESCAPE))
        self.assertEqual(self.snapshot(), before)

    def test_window_close_quits_pygame_and_exits(self):
        with patch("games.hangman.pygame.quit") as quit_pygame:
            with self.assertRaises(SystemExit):
                self.send_events(pygame.event.Event(pygame.QUIT))
        quit_pygame.assert_called_once_with()

    def test_run_returns_none_without_wins(self):
        escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="")
        with patch("games.hangman.pygame.event.get", return_value=[escape]):
            self.assertIsNone(self.game.run())

    def test_run_returns_accumulated_wins(self):
        self.win_round()
        self.game.new_word()
        self.win_round()
        escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="")
        with patch("games.hangman.pygame.event.get", return_value=[escape]):
            self.assertEqual(self.game.run(), 2)

    def test_run_draws_frame_then_exits_on_escape(self):
        escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="")
        with patch("games.hangman.pygame.event.get", side_effect=[[], [escape]]):
            with patch.object(self.game, "draw", wraps=self.game.draw) as draw:
                self.assertIsNone(self.game.run())
        draw.assert_called_once_with()
        self.clock.tick.assert_called_once_with(hangman.FPS)

    def test_draw_handles_play_victory_and_defeat(self):
        self.game.draw()
        self.win_round()
        self.game.draw()
        self.game.new_word()
        for letter in "АБВГЕЖ":
            self.game.guess(letter)
        self.assertEqual(self.game.state, "lost")
        self.game.draw()

    def test_module_entry_point_returns_session_result(self):
        with patch("games.hangman.Hangman", return_value=self.game) as constructor:
            with patch.object(self.game, "run", return_value=2):
                self.assertEqual(hangman.run(self.screen, self.clock), 2)
        constructor.assert_called_once_with(self.screen, self.clock)
        self.assertEqual(pygame.display.get_caption()[0], "Виселица")


if __name__ == "__main__":
    unittest.main()
