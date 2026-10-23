"""Таблица рекордов: общая для всех игр, хранится в scores.json."""
import json
import os

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")

# Игры, где результат тем лучше, чем он МЕНЬШЕ (попытки, время реакции)
LOWER_IS_BETTER = {"guess_number", "reaction"}


def _load():
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data):
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # не удалось сохранить - игра не должна из-за этого падать


def add(game, score):
    """Добавить результат игры (game - имя модуля, например 'snake')."""
    data = _load()
    data.setdefault(game, []).append(score)
    _save(data)


def best(game):
    """Лучший результат игры или None, если ещё не играли."""
    results = _load().get(game, [])
    if not results:
        return None
    return min(results) if game in LOWER_IS_BETTER else max(results)
