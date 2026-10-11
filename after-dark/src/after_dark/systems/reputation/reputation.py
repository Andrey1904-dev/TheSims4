"""Репутационные показатели персонажа.

* Изменения происходят только через зарегистрированные события (apply_event).
* Нет «автоматического» штрафа за сексуальные предпочтения или число связей:
  функции этого модуля не принимают таких параметров.
* Публичность события масштабирует его эффект (закрытая встреча — почти без
  эффекта, скандал на публике — полный эффект).
* Без событий показатели никуда не дрейфуют: восстановление возможно только
  через явные игровые действия (decay_toward_neutral вызывается явно).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from after_dark.core.constants import REPUTATION_MAX, REPUTATION_MIN

AXES = ("public", "circle", "professional")


@dataclass(frozen=True)
class ReputationEvent:
    name: str
    deltas: dict[str, int]          # например {"public": -5, "circle": 3}
    publicity: float = 1.0          # 0.0 — приватно, 1.0 — публично

    def __post_init__(self) -> None:
        unknown = set(self.deltas) - set(AXES)
        if unknown:
            raise ValueError(f"Неизвестные оси репутации: {sorted(unknown)}")
        if not 0.0 <= self.publicity <= 1.0:
            raise ValueError("publicity должен быть в диапазоне 0..1")


@dataclass
class Reputation:
    public: int = 0
    circle: int = 0
    professional: int = 0
    fame: int = 0                   # известность, 0..100
    history: list[str] = field(default_factory=list)

    def value(self, axis: str) -> int:
        if axis not in AXES:
            raise KeyError(axis)
        return getattr(self, axis)

    def apply_event(self, event: ReputationEvent) -> dict[str, int]:
        """Применить событие. Возвращает фактические изменения по осям."""
        applied: dict[str, int] = {}
        for axis, delta in event.deltas.items():
            scaled = round(delta * event.publicity)
            new_value = max(REPUTATION_MIN, min(REPUTATION_MAX, self.value(axis) + scaled))
            applied[axis] = new_value - self.value(axis)
            setattr(self, axis, new_value)
        if event.publicity >= 0.5 and any(d < 0 for d in event.deltas.values()):
            self.fame = max(0, min(100, self.fame + 1))
        self.history.append(event.name)
        return applied

    def decay_toward_neutral(self, amount: int = 1) -> None:
        """Явное восстановление к нулю (вызывается игровым событием, не таймером)."""
        for axis in AXES:
            value = self.value(axis)
            if value > 0:
                setattr(self, axis, max(0, value - amount))
            elif value < 0:
                setattr(self, axis, min(0, value + amount))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Reputation":
        def ax(key: str) -> int:
            return max(REPUTATION_MIN, min(REPUTATION_MAX, int(data.get(key, 0))))

        history = [str(x) for x in data.get("history", [])][-50:]
        return cls(public=ax("public"), circle=ax("circle"), professional=ax("professional"),
                   fame=max(0, min(100, int(data.get("fame", 0)))), history=history)
