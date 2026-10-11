"""Настройки игрока: значения по умолчанию, загрузка и проверка.

Некорректные значения не ломают загрузку: заменяются значением по умолчанию
и попадают в список предупреждений, который пишется в лог.
"""

from __future__ import annotations

import copy
from typing import Any

from after_dark.core.constants import IMPLEMENTED_MODULES

FREQUENCY_LEVELS = ("off", "low", "normal", "high")

DEFAULT_SETTINGS: dict[str, Any] = {
    "adult_mechanics_enabled": True,
    "modules": {name: True for name in IMPLEMENTED_MODULES},
    "event_frequency": "normal",
    "flirt_cooldown_hours": 4,
    "max_flirts_per_day": 6,
    "logging_level": "INFO",
}

_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
_FLIRT_COOLDOWN_RANGE = (0, 24)
_MAX_FLIRTS_RANGE = (0, 50)


def load_settings(raw: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    """Вернуть (настройки, предупреждения). Не выбрасывает исключений."""
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    warnings: list[str] = []
    if not isinstance(raw, dict):
        if raw is not None:
            warnings.append("Настройки имеют неверный тип, используются значения по умолчанию.")
        return settings, warnings

    if isinstance(raw.get("adult_mechanics_enabled"), bool):
        settings["adult_mechanics_enabled"] = raw["adult_mechanics_enabled"]
    elif "adult_mechanics_enabled" in raw:
        warnings.append("adult_mechanics_enabled должен быть true/false.")

    raw_modules = raw.get("modules")
    if isinstance(raw_modules, dict):
        for name, value in raw_modules.items():
            if name not in IMPLEMENTED_MODULES:
                warnings.append(f"Неизвестный модуль в настройках: {name!r}.")
            elif isinstance(value, bool):
                settings["modules"][name] = value
            else:
                warnings.append(f"Модуль {name!r}: значение должно быть true/false.")
    elif raw_modules is not None:
        warnings.append("Раздел modules должен быть объектом.")

    freq = raw.get("event_frequency")
    if freq in FREQUENCY_LEVELS:
        settings["event_frequency"] = freq
    elif freq is not None:
        warnings.append(f"event_frequency должен быть одним из {FREQUENCY_LEVELS}.")

    _load_int(raw, settings, "flirt_cooldown_hours", _FLIRT_COOLDOWN_RANGE, warnings)
    _load_int(raw, settings, "max_flirts_per_day", _MAX_FLIRTS_RANGE, warnings)

    level = raw.get("logging_level")
    if level in _LOG_LEVELS:
        settings["logging_level"] = level
    elif level is not None:
        warnings.append(f"logging_level должен быть одним из {_LOG_LEVELS}.")

    return settings, warnings


def _load_int(raw: dict[str, Any], settings: dict[str, Any], key: str,
              bounds: tuple[int, int], warnings: list[str]) -> None:
    if key not in raw:
        return
    value = raw[key]
    low, high = bounds
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        warnings.append(f"{key} должен быть целым числом от {low} до {high}.")
        return
    settings[key] = value


def is_module_enabled(settings: dict[str, Any], module: str) -> bool:
    """Модуль работает, только если включены и он сам, и взрослые механики.

    Ядро (core) отключить нельзя: без него мод не может сохранять состояние.
    """
    if module == "core":
        return True
    if not settings.get("adult_mechanics_enabled", True):
        return False
    return bool(settings.get("modules", {}).get(module, False))
