"""Сохранение и загрузка состояния мода.

Принципы:
* формат — обычный JSON-совместимый словарь с номером схемы;
* загрузка никогда не выбрасывает исключений: повреждённая часть заменяется
  значениями по умолчанию, а проблема записывается в предупреждения. Так
  повреждённые данные мода не делают недоступным сохранение игры;
* для неизвестной более новой схемы состояние не загружается, а возвращается
  пустое, чтобы не перезаписать чужие данные неправильно.
"""

from __future__ import annotations

from typing import Any

from after_dark import __version__
from after_dark.core.constants import SAVE_SCHEMA_VERSION
from after_dark.core.state import ModState, SimRecord
from after_dark.systems.relationships.history import PartnerHistory
from after_dark.systems.reputation.reputation import Reputation
from after_dark.systems.sexuality.flirt import FlirtLimiter


def dump_state(state: ModState) -> dict[str, Any]:
    return {
        "schema_version": SAVE_SCHEMA_VERSION,
        "mod_version": __version__,
        "day_index": state.day_index,
        "sims": {
            str(sim_id): {
                "age": record.age,
                "history": record.history.to_list(),
                "reputation": record.reputation.to_dict(),
                "flirt": record.flirt.to_dict(),
                "has_trait_new_experiences": record.has_trait_new_experiences,
            }
            for sim_id, record in state.sims.items()
        },
    }


def load_state(data: Any, warnings: list[str], flirt_cooldown_seconds: int,
               flirt_max_per_day: int) -> ModState:
    """Загрузить состояние. Параметры флирта берутся из настроек игрока, а не из файла."""
    state = ModState()
    if not isinstance(data, dict):
        if data is not None:
            warnings.append("Состояние мода повреждено (не объект); начато с пустого состояния.")
        return state

    schema = data.get("schema_version")
    if not isinstance(schema, int) or schema > SAVE_SCHEMA_VERSION:
        warnings.append(f"Неизвестная версия схемы {schema!r}; состояние не загружено.")
        return state

    state.day_index = _safe_int(data.get("day_index"), 0)
    sims = data.get("sims", {})
    if not isinstance(sims, dict):
        warnings.append("Раздел sims повреждён; персонажи не загружены.")
        return state

    for raw_id, raw in sims.items():
        try:
            sim_id = int(raw_id)
            if not isinstance(raw, dict):
                raise ValueError("запись не является объектом")
            record = SimRecord(
                sim_id=sim_id,
                age=_safe_int(raw.get("age"), 0),
                history=PartnerHistory.from_list(raw.get("history", [])),
                reputation=Reputation.from_dict(raw.get("reputation", {})),
                flirt=FlirtLimiter.from_dict(raw.get("flirt", {}), flirt_cooldown_seconds, flirt_max_per_day),
                has_trait_new_experiences=bool(raw.get("has_trait_new_experiences", False)),
            )
        except (ValueError, KeyError, TypeError) as exc:
            warnings.append(f"Персонаж {raw_id}: данные повреждены ({exc}); запись пропущена.")
            continue
        state.sims[sim_id] = record
    return state


def _safe_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
