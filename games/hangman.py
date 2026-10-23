"""Виселица для GameBox.

Подключается к главному меню через run(screen, clock):
по Esc возвращает управление в меню и отдаёт число угаданных слов за сессию
(или None, если не угадано ни одного).

Слова берутся из assets/words.txt (одно слово на строку). Если файла нет,
используется встроенный короткий список.
Управление: буквы с клавиатуры (русская раскладка) или клик мышью по букве,
ПРОБЕЛ - следующее слово, Esc - в меню.
"""
import os
import random
import sys

import pygame

FPS = 60
MAX_MISTAKES = 6
ALPHABET = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
FONT_NAMES = "arial,segoeui,dejavusans,liberationsans,freesans"

WORDS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "words.txt"
)
DEFAULT_WORDS = [
    "ПРОГРАММА", "АЛГОРИТМ", "КОМПИЛЯТОР", "РЕПОЗИТОРИЙ", "КОММИТ",
    "ВЕТКА", "СЛИЯНИЕ", "КОНФЛИКТ", "КЛАВИАТУРА", "СТУДЕНТ",
]

BG = (24, 26, 35)
TEXT = (235, 237, 245)
MUTED = (140, 146, 165)
PANEL = (40, 44, 60)
PANEL_HOVER = (62, 70, 100)
GOOD = (80, 200, 120)
BAD = (230, 80, 80)
ACCENT = (96, 165, 250)
YELLOW = (255, 220, 80)


def load_words():
    """Читает слова из файла; при проблемах возвращает встроенный список."""
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            words = [line.strip().upper().replace("Ё", "Е") for line in f]
    except OSError:
        words = []
    words = [w for w in words if len(w) >= 3 and all(c in ALPHABET for c in w)]
    return words or DEFAULT_WORDS


class Hangman:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()

        self.font_title = pygame.font.SysFont(FONT_NAMES, 40, bold=True)
        self.font_word = pygame.font.SysFont(FONT_NAMES, 44, bold=True)
        self.font_letter = pygame.font.SysFont(FONT_NAMES, 26, bold=True)
        self.font_text = pygame.font.SysFont(FONT_NAMES, 24)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 18)

        self.words = load_words()
        self.deck = []
        self.wins = 0
        self.letter_rects = self._build_keyboard()
        self.new_word()

    def _build_keyboard(self):
        """Прямоугольники букв: 8 в ряд, 4 ряда, справа внизу."""
        cell, per_row = 48, 8
        start_x = self.width - per_row * cell - 40
        start_y = 345
        rects = {}
        for i, letter in enumerate(ALPHABET):
            row, col = divmod(i, per_row)
            rects[letter] = pygame.Rect(start_x + col * cell, start_y + row * cell, cell - 6, cell - 6)
        return rects

    def new_word(self):
        """Следующее слово; слова не повторяются, пока не кончится вся колода."""
        if not self.deck:
            self.deck = self.words[:]
            random.shuffle(self.deck)
        self.word = self.deck.pop()
        self.guessed = set()
        self.mistakes = 0
        self.state = "play"  # play / won / lost

    def guess(self, letter):
        """Попытка угадать букву."""
        if self.state != "play" or letter in self.guessed:
            return
        self.guessed.add(letter)
        if letter not in self.word:
            self.mistakes += 1
            if self.mistakes >= MAX_MISTAKES:
                self.state = "lost"
        elif all(c in self.guessed for c in self.word):
            self.state = "won"
            self.wins += 1

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
                if event.key == pygame.K_SPACE and self.state != "play":
                    self.new_word()
                else:
                    letter = event.unicode.upper().replace("Ё", "Е")
                    if letter in ALPHABET:
                        self.guess(letter)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for letter, rect in self.letter_rects.items():
                    if rect.collidepoint(event.pos):
                        self.guess(letter)
                        break
        return True

    # ---------- отрисовка ----------
    def draw_gallows(self):
        ox, oy = 60, 110
        line = (200, 200, 215)
        w = 5
        # виселица (рисуется всегда)
        pygame.draw.line(self.screen, line, (ox, oy + 330), (ox + 240, oy + 330), w)
        pygame.draw.line(self.screen, line, (ox + 60, oy + 330), (ox + 60, oy), w)
        pygame.draw.line(self.screen, line, (ox + 60, oy), (ox + 200, oy), w)
        pygame.draw.line(self.screen, line, (ox + 200, oy), (ox + 200, oy + 40), w)

        color = BAD if self.state == "lost" else TEXT
        m = self.mistakes
        if m >= 1:  # голова
            pygame.draw.circle(self.screen, color, (ox + 200, oy + 70), 30, w)
        if m >= 2:  # туловище
            pygame.draw.line(self.screen, color, (ox + 200, oy + 100), (ox + 200, oy + 200), w)
        if m >= 3:  # левая рука
            pygame.draw.line(self.screen, color, (ox + 200, oy + 120), (ox + 160, oy + 170), w)
        if m >= 4:  # правая рука
            pygame.draw.line(self.screen, color, (ox + 200, oy + 120), (ox + 240, oy + 170), w)
        if m >= 5:  # левая нога
            pygame.draw.line(self.screen, color, (ox + 200, oy + 200), (ox + 165, oy + 270), w)
        if m >= 6:  # правая нога
            pygame.draw.line(self.screen, color, (ox + 200, oy + 200), (ox + 235, oy + 270), w)

    def draw_word(self):
        """Слово с подчёркиваниями на месте неотгаданных букв."""
        area_left, area_right = 340, self.width - 30
        slot = min(48, (area_right - area_left) // len(self.word))
        total = slot * len(self.word)
        x = (area_left + area_right) // 2 - total // 2
        y = 215
        for ch in self.word:
            known = ch in self.guessed
            if known or self.state == "lost":
                color = TEXT if known else BAD
                surf = self.font_word.render(ch, True, color)
                self.screen.blit(surf, surf.get_rect(center=(x + slot // 2, y - 6)))
            pygame.draw.line(self.screen, MUTED, (x + 4, y + 22), (x + slot - 4, y + 22), 3)
            x += slot

    def draw_keyboard(self):
        mouse = pygame.mouse.get_pos()
        for letter, rect in self.letter_rects.items():
            if letter in self.guessed:
                bg = (35, 70, 50) if letter in self.word else (80, 40, 45)
                fg = GOOD if letter in self.word else BAD
            else:
                bg = PANEL_HOVER if rect.collidepoint(mouse) and self.state == "play" else PANEL
                fg = TEXT
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)
            surf = self.font_letter.render(letter, True, fg)
            self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw(self):
        self.screen.fill(BG)

        title = self.font_title.render("Виселица", True, TEXT)
        self.screen.blit(title, (30, 22))
        info = self.font_text.render(
            f"Ошибок: {self.mistakes}/{MAX_MISTAKES}    Угадано слов: {self.wins}", True, MUTED
        )
        self.screen.blit(info, info.get_rect(topright=(self.width - 30, 30)))

        self.draw_gallows()
        self.draw_word()

        if self.state == "won":
            msg = self.font_text.render("Верно! ПРОБЕЛ - следующее слово", True, GOOD)
            self.screen.blit(msg, msg.get_rect(center=(550, 290)))
        elif self.state == "lost":
            msg = self.font_text.render("Не угадали. ПРОБЕЛ - следующее слово", True, BAD)
            self.screen.blit(msg, msg.get_rect(center=(550, 290)))

        self.draw_keyboard()

        hint = self.font_small.render("Буквы с клавиатуры или мышью, Esc - в меню", True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 22)))

        pygame.display.flip()

    def run(self):
        """Игровой цикл. Возвращает число угаданных слов или None."""
        while True:
            if not self.handle_events():
                break
            self.draw()
            self.clock.tick(FPS)
        return self.wins or None


def run(screen, clock):
    """Точка входа для главного меню GameBox."""
    pygame.display.set_caption("Виселица")
    return Hangman(screen, clock).run()


if __name__ == "__main__":
    pygame.init()
    window = pygame.display.set_mode((800, 600))
    run(window, pygame.time.Clock())
    pygame.quit()
