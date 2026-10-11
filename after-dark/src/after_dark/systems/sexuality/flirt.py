"""Флирт и знакомства.

Функции принимают уже вычисленные значения и источник случайности
(random.Random), поэтому поведение детерминировано в тестах.
Кулдауны и дневной лимит не дают запускать флирт бесконечно.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from after_dark.core.constants import SCORE_MAX, SCORE_MIN

HOUR = 60 * 60


@dataclass
class FlirtLimiter:
    """Кулдаун на партнёра и дневной лимит. Время — в секундах игры."""

    cooldown_seconds: int = 4 * HOUR
    max_per_day: int = 6
    last_flirt_at: dict[int, float] = field(default_factory=dict)
    day_index: int = -1
    count_today: int = 0

    def can_flirt(self, partner_id: int, now: float, day_index: int) -> bool:
        if day_index != self.day_index:
            # Новый игровой день: счётчик сбрасывается, но кулдауны остаются.
            return True
        if self.count_today >= self.max_per_day:
            return False
        last = self.last_flirt_at.get(partner_id)
        return last is None or now - last >= self.cooldown_seconds

    def register(self, partner_id: int, now: float, day_index: int) -> None:
        if day_index != self.day_index:
            self.day_index = day_index
            self.count_today = 0
        self.count_today += 1
        self.last_flirt_at[partner_id] = now

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_flirt_at": {str(k): v for k, v in self.last_flirt_at.items()},
            "day_index": self.day_index,
            "count_today": self.count_today,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], cooldown_seconds: int, max_per_day: int) -> "FlirtLimiter":
        limiter = cls(cooldown_seconds=cooldown_seconds, max_per_day=max_per_day)
        limiter.last_flirt_at = {int(k): float(v) for k, v in data.get("last_flirt_at", {}).items()}
        limiter.day_index = int(data.get("day_index", -1))
        limiter.count_today = int(data.get("count_today", 0))
        return limiter


def flirt_success_chance(attraction: int, confidence: int, trait_bonus: int = 0) -> float:
    """Шанс успеха флирта в диапазоне 0..1.

    attraction и confidence — показатели 0..100. Бонус от черты добавляет
    не более 10 процентных пунктов: черта помогает, но не гарантирует результат.
    """
    attraction = max(SCORE_MIN, min(SCORE_MAX, attraction))
    confidence = max(SCORE_MIN, min(SCORE_MAX, confidence))
    base = 0.2 + 0.4 * (attraction / SCORE_MAX) + 0.2 * (confidence / SCORE_MAX)
    bonus = max(0, min(10, trait_bonus)) / 100
    return max(0.0, min(0.95, base + bonus))


def roll_flirt(rng: random.Random, chance: float) -> bool:
    return rng.random() < chance
