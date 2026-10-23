"""GameBox: главное меню сборника мини-игр.

Контракт для каждой игры (файл games/<имя>.py):

    def run(screen, clock):
        # свой игровой цикл; по Esc - выход в меню
        return score  # число очков/попыток/мс или None, если результата нет
"""
import importlib
import sys

import pygame

import scores
from ui import (BG, FPS, HEIGHT, MUTED, TEXT, WIDTH, Button, draw_text)

# (название на кнопке, имя модуля в папке games/)
GAMES = [
    ("Угадай число", "guess_number"),
    ("Виселица", "hangman"),
    ("Крестики-нолики", "tictactoe"),
    ("Память", "memory"),
    ("Реакция", "reaction"),
    ("Камень-ножницы-бумага", "rps"),
    ("Змейка", "snake"),
    ("Сапёр", "minesweeper"),
]

# Единицы измерения для таблицы рекордов
UNITS = {
    "guess_number": "попыток",
    "reaction": "мс",
}


def quit_app():
    pygame.quit()
    sys.exit()


def wait_for_escape(screen, clock, lines):
    """Простой экран с текстом; закрывается по Esc или клику."""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_app()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return
        screen.fill(BG)
        y = HEIGHT // 2 - 20 * len(lines)
        for text, size, color in lines:
            draw_text(screen, text, size, color, center=(WIDTH // 2, y))
            y += size + 18
        pygame.display.flip()
        clock.tick(FPS)


def launch_game(screen, clock, title, module_name):
    """Запустить игру; если файла ещё нет - показать заглушку."""
    full_name = f"games.{module_name}"
    try:
        module = importlib.import_module(full_name)
    except ModuleNotFoundError as e:
        if e.name not in (full_name, "games"):
            raise  # ошибка внутри самой игры (например, нет нужной библиотеки)
        module = None

    if module is None or not hasattr(module, "run"):
        wait_for_escape(screen, clock, [
            (title, 40, TEXT),
            ("Эта игра ещё в разработке", 24, MUTED),
            ("Esc или клик - вернуться в меню", 18, MUTED),
        ])
        return

    result = module.run(screen, clock)
    if result is not None:
        scores.add(module_name, result)
    pygame.display.set_caption("GameBox")


def show_records(screen, clock):
    lines = [("Рекорды", 40, TEXT)]
    for title, module_name in GAMES:
        value = scores.best(module_name)
        if value is None:
            shown = "-"
        else:
            shown = f"{value} {UNITS.get(module_name, '')}".strip()
        lines.append((f"{title}: {shown}", 22, TEXT))
    lines.append(("Esc или клик - вернуться в меню", 18, MUTED))
    wait_for_escape(screen, clock, lines)


def build_menu():
    """Создать кнопки: 8 игр + 'Рекорды' в сетке 3x3. Возвращает [(Button, действие)]."""
    cols, btn_w, btn_h, gap = 3, 220, 100, 30
    start_x = (WIDTH - (cols * btn_w + (cols - 1) * gap)) // 2
    start_y = 150

    items = [(title, ("game", name)) for title, name in GAMES]
    items.append(("Рекорды", ("records", None)))

    menu = []
    for i, (title, action) in enumerate(items):
        row, col = divmod(i, cols)
        rect = (start_x + col * (btn_w + gap), start_y + row * (btn_h + gap), btn_w, btn_h)
        menu.append((Button(rect, title), action))
    return menu


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("GameBox")
    clock = pygame.time.Clock()
    menu = build_menu()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_app()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                quit_app()
            for button, (kind, module_name) in menu:
                if button.clicked(event):
                    if kind == "records":
                        show_records(screen, clock)
                    else:
                        launch_game(screen, clock, button.text, module_name)
                    pygame.event.clear()
                    break

        screen.fill(BG)
        draw_text(screen, "GameBox", 56, TEXT, center=(WIDTH // 2, 70))
        draw_text(screen, "Выберите игру", 22, MUTED, center=(WIDTH // 2, 118))
        for button, _ in menu:
            button.draw(screen)
        draw_text(screen, "Esc в игре - возврат в меню", 18, MUTED,
                  center=(WIDTH // 2, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
