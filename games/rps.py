import os
import random
import sys

import pygame

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import ACCENT, BG, FPS, HEIGHT, MUTED, TEXT, WIDTH, Button, draw_text

CHOICES = ("Камень", "Ножницы", "Бумага")
KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}


def run(screen, clock):
    pygame.display.set_caption("Камень, ножницы, бумага")
    width, height = screen.get_size()
    button_width, button_height, gap = 200, 80, 20
    start_x = (width - 3 * button_width - 2 * gap) // 2
    buttons = [
        Button((start_x + i * (button_width + gap), height // 2 - 15,
                button_width, button_height), choice, font_size=28)
        for i, choice in enumerate(CHOICES)
    ]
    wins = draws = losses = rounds = 0
    player = computer = result = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return wins if rounds else None

            choice = None
            if event.type == pygame.KEYDOWN:
                choice = KEYS.get(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                choice = next((i for i, button in enumerate(buttons)
                               if button.rect.collidepoint(event.pos)), None)

            if choice is not None:
                player = choice
                computer = random.randrange(3)
                result = ("draw" if player == computer else
                          "win" if (player - computer) % 3 == 2 else "loss")
                rounds += 1
                if result == "win":
                    wins += 1
                elif result == "draw":
                    draws += 1
                else:
                    losses += 1

        screen.fill(BG)
        draw_text(screen, "Камень, ножницы, бумага", 42, TEXT,
                  center=(width // 2, 75))
        draw_text(screen, "Выберите ход", 24, MUTED, center=(width // 2, 145))
        for button in buttons:
            button.draw(screen)

        if result is not None:
            draw_text(screen, f"Вы: {CHOICES[player]}    Компьютер: {CHOICES[computer]}",
                      26, TEXT, center=(width // 2, 390))
            label, color = {
                "win": ("Вы выиграли!", ACCENT),
                "draw": ("Ничья", MUTED),
                "loss": ("Вы проиграли", (245, 110, 110)),
            }[result]
            draw_text(screen, label, 32, color, center=(width // 2, 435))

        draw_text(screen, f"Победы: {wins}   Ничьи: {draws}   Поражения: {losses}",
                  22, TEXT, center=(width // 2, 510))
        draw_text(screen, "Клавиши 1–3 — выбор, Esc — меню", 18, MUTED,
                  center=(width // 2, height - 30))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    run(pygame.display.set_mode((WIDTH, HEIGHT)), pygame.time.Clock())
    pygame.quit()