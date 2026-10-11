"""История отношений персонажа.

Каждая связь, зарегистрированная системой, остаётся в истории навсегда
(даже после завершения). Активная связь с одним партнёром в одном виде
может быть только одна.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from after_dark.core.constants import SCORE_MAX, SCORE_MIN


class RelationKind(str, Enum):
    CASUAL = "casual"        # непродолжительная связь
    DATING = "dating"        # свидания / романтические отношения
    EXCLUSIVE = "exclusive"  # договорённость о моногамии


class EndReason(str, Enum):
    MUTUAL = "mutual"        # расстались по взаимному согласию
    BREAKUP = "breakup"      # один из партнёров ушёл сам
    BETRAYAL = "betrayal"    # измена при договорённости о моногамии
    DEATH = "death"          # партнёр умер / исчез из игры
    UNKNOWN = "unknown"      # причина не зарегистрирована


def clamp(value: float, low: int = SCORE_MIN, high: int = SCORE_MAX) -> int:
    return int(max(low, min(high, round(value))))


@dataclass
class Relationship:
    partner_id: int
    kind: RelationKind
    started_day: int
    ended_day: int | None = None
    end_reason: EndReason | None = None
    trust: int = 50          # доверие
    attachment: int = 0      # эмоциональная привязанность

    @property
    def is_active(self) -> bool:
        return self.ended_day is None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["end_reason"] = self.end_reason.value if self.end_reason else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        end_reason = data.get("end_reason")
        return cls(
            partner_id=int(data["partner_id"]),
            kind=RelationKind(data["kind"]),
            started_day=int(data["started_day"]),
            ended_day=None if data.get("ended_day") is None else int(data["ended_day"]),
            end_reason=EndReason(end_reason) if end_reason else None,
            trust=clamp(data.get("trust", 50)),
            attachment=clamp(data.get("attachment", 0)),
        )


@dataclass
class PartnerHistory:
    """История связей одного персонажа."""

    entries: list[Relationship] = field(default_factory=list)

    def active(self) -> list[Relationship]:
        return [r for r in self.entries if r.is_active]

    def find_active(self, partner_id: int, kind: RelationKind | None = None) -> Relationship | None:
        for rel in self.entries:
            if rel.is_active and rel.partner_id == partner_id and (kind is None or rel.kind is kind):
                return rel
        return None

    def start(self, partner_id: int, kind: RelationKind, day: int) -> Relationship:
        """Зарегистрировать новую связь. Дубликат активной связи запрещён."""
        if self.find_active(partner_id, kind) is not None:
            raise ValueError("Такая связь уже активна.")
        rel = Relationship(partner_id=partner_id, kind=RelationKind(kind), started_day=day)
        self.entries.append(rel)
        return rel

    def end(self, partner_id: int, day: int, reason: EndReason,
            kind: RelationKind | None = None) -> Relationship | None:
        """Завершить активную связь. Возвращает None, если активной связи нет."""
        rel = self.find_active(partner_id, kind)
        if rel is None:
            return None
        rel.ended_day = day
        rel.end_reason = EndReason(reason)
        return rel

    def to_list(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.entries]

    @classmethod
    def from_list(cls, items: list[dict[str, Any]]) -> "PartnerHistory":
        return cls(entries=[Relationship.from_dict(item) for item in items])
