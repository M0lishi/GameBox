import os
import random
import sys

import pygame

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import ACCENT, BG, FPS, HEIGHT, MUTED, PANEL, TEXT, WIDTH, draw_text


def run(screen, clock):
    pygame.display.set_caption("Угадай число")
    width, height = screen.get_size()
    secret = random.randint(1, 100)
    entry = ""
    attempts = best = 0
    hint = "Введите число от 1 до 100 и нажмите Enter"
    won = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return best or None
                if won:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        secret = random.randint(1, 100)
                        entry, attempts, hint, won = "", 0, "Введите число от 1 до 100", False
                    continue
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if not entry:
                        hint = "Введите число"
                    else:
                        guess = int(entry)
                        if not 1 <= guess <= 100:
                            hint = "Число должно быть от 1 до 100"
                        else:
                            attempts += 1
                            if guess == secret:
                                hint = f"Верно! Попыток: {attempts}"
                                best = attempts if not best else min(best, attempts)
                                won = True
                            else:
                                hint = "Загаданное число " + ("больше" if guess < secret else "меньше")
                            entry = ""
                elif event.key == pygame.K_BACKSPACE:
                    entry = entry[:-1]
                elif event.unicode in "0123456789" and len(entry) < 3:
                    entry += event.unicode

        screen.fill(BG)
        draw_text(screen, "Угадай число", 46, TEXT, center=(width // 2, 90))
        draw_text(screen, "Я загадал число от 1 до 100", 24, MUTED,
                  center=(width // 2, 155))
        box = pygame.Rect(width // 2 - 110, 215, 220, 70)
        pygame.draw.rect(screen, PANEL, box, border_radius=10)
        pygame.draw.rect(screen, ACCENT, box, width=2, border_radius=10)
        draw_text(screen, entry or "?", 38, TEXT, center=box.center)
        draw_text(screen, hint, 23, TEXT, center=(width // 2, 335))
        draw_text(screen, f"Попыток: {attempts}", 22, MUTED,
                  center=(width // 2, 385))
        if best:
            draw_text(screen, f"Лучший результат: {best}", 20, MUTED,
                      center=(width // 2, 425))
        if won:
            draw_text(screen, "Enter — новая игра", 18, MUTED,
                      center=(width // 2, height // 2 + 250))
        draw_text(screen, "Enter — проверить, Backspace — удалить, Esc — меню",
                  17, MUTED, center=(width // 2, height - 30))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    run(pygame.display.set_mode((WIDTH, HEIGHT)), pygame.time.Clock())
    pygame.quit()