"""Общее состояние мода: собирает состояния всех систем по персонажам."""

from __future__ import annotations

from dataclasses import dataclass, field

from after_dark.systems.relationships.history import PartnerHistory
from after_dark.systems.reputation.reputation import Reputation
from after_dark.systems.sexuality.flirt import FlirtLimiter


@dataclass
class SimRecord:
    """Всё, что мод знает об одном персонаже. Ключ — ID персонажа в игре."""

    sim_id: int
    age: int
    history: PartnerHistory = field(default_factory=PartnerHistory)
    reputation: Reputation = field(default_factory=Reputation)
    flirt: FlirtLimiter = field(default_factory=FlirtLimiter)
    has_trait_new_experiences: bool = False


@dataclass
class ModState:
    sims: dict[int, SimRecord] = field(default_factory=dict)
    day_index: int = 0

    def ensure_sim(self, sim_id: int, age: int) -> SimRecord:
        record = self.sims.get(sim_id)
        if record is None:
            record = SimRecord(sim_id=sim_id, age=age)
            self.sims[sim_id] = record
        record.age = age
        return record
