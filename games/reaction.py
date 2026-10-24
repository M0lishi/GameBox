import os
import random
import sys

import pygame

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import FPS, HEIGHT, TEXT, WIDTH, draw_text

WAIT_COLOR = (190, 55, 65)
READY_COLOR = (45, 160, 95)
RESULT_COLOR = (45, 100, 160)


def run(screen, clock):
    pygame.display.set_caption("Тест на реакцию")
    width, height = screen.get_size()
    state = "waiting"
    deadline = pygame.time.get_ticks() + random.randint(1500, 4000)
    ready_at = best = result = None
    message = None

    while True:
        now = pygame.time.get_ticks()
        if state == "waiting" and now >= deadline:
            state, ready_at, message = "ready", now, None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return best
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                now = pygame.time.get_ticks()
                if state == "waiting":
                    message = "Слишком рано! Попробуйте ещё раз"
                    deadline = now + random.randint(1500, 4000)
                elif state == "ready":
                    result = now - ready_at
                    best = result if best is None else min(best, result)
                    state = "result"
                else:
                    state = "waiting"
                    deadline = now + random.randint(1500, 4000)
                    message = None

        if state == "waiting":
            screen.fill(WAIT_COLOR)
            title = "Ждите…"
            hint = message or "Нажмите ЛКМ, когда экран станет зелёным"
        elif state == "ready":
            screen.fill(READY_COLOR)
            title, hint = "ЖМИ!", "Нажмите левую кнопку мыши!"
        else:
            screen.fill(RESULT_COLOR)
            title, hint = f"Ваша реакция: {result} мс", "Нажмите ЛКМ для следующего раунда"

        draw_text(screen, title, 48, TEXT, center=(width // 2, height // 2 - 45))
        draw_text(screen, hint, 22, TEXT, center=(width // 2, height // 2 + 25))
        if best is not None:
            draw_text(screen, f"Лучший результат: {best} мс", 20, TEXT,
                      center=(width // 2, height // 2 + 85))
        draw_text(screen, "Esc — вернуться в меню", 18, TEXT,
                  center=(width // 2, height - 30))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    run(pygame.display.set_mode((WIDTH, HEIGHT)), pygame.time.Clock())
    pygame.quit()