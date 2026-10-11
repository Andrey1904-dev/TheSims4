"""Мост к игре The Sims 4.

ВАЖНО: в версии 0.1.0 игровые хуки НЕ проверены в игре. Этот модуль:
* безопасно импортируется вне игры (импорт модулей игры обёрнут в try);
* содержит только определение окружения и список точек интеграции,
  которые будут реализованы и проверены на этапе 1 (см. docs/ROADMAP.md).

Точки интеграции (нереализованы):
1. Загрузка мода и регистрация команд отладки.
2. Чтение и запись блока сохранения SAVE_KEY через механизм сохранений игры.
3. Выдача черты характера при создании персонажа (по выбору игрока).
4. Зарегистрированные взаимодействия флирта из tuning/interactions/.
"""

from __future__ import annotations

from after_dark.core.constants import SAVE_KEY

try:  # pragma: no cover - выполняется только внутри игры
    import sims4  # type: ignore[import-not-found]  # noqa: F401
    IN_GAME = True
except ImportError:
    IN_GAME = False


def describe_environment() -> dict[str, object]:
    """Сведения для логов и экрана «Совместимость» (без персональных данных)."""
    return {"in_game": IN_GAME, "save_key": SAVE_KEY}
