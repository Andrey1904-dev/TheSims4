"""Последствия завершения отношений.

Разделяем добровольное расставание и предательство: расставание по согласию
не наказывает никого, измена при договорённости о моногамии снижает доверие
у обиженного партнёра. Открытость сама по себе ни на что не влияет.
"""

from __future__ import annotations

from dataclasses import dataclass

from after_dark.systems.relationships.history import EndReason, Relationship, clamp


@dataclass(frozen=True)
class EndEffect:
    """Изменение показателей у оставшегося партнёра (для отношений с ним)."""
    trust_delta: int = 0
    attachment_delta: int = 0


END_EFFECTS: dict[EndReason, EndEffect] = {
    EndReason.MUTUAL: EndEffect(trust_delta=0, attachment_delta=-5),
    EndReason.BREAKUP: EndEffect(trust_delta=-5, attachment_delta=-10),
    EndReason.BETRAYAL: EndEffect(trust_delta=-30, attachment_delta=-20),
    EndReason.DEATH: EndEffect(trust_delta=0, attachment_delta=0),
    EndReason.UNKNOWN: EndEffect(trust_delta=0, attachment_delta=-2),
}


def apply_end_effect(rel: Relationship, reason: EndReason) -> Relationship:
    """Применить эффект завершения к связи, которая уже помечена как завершённая."""
    effect = END_EFFECTS[EndReason(reason)]
    rel.trust = clamp(rel.trust + effect.trust_delta)
    rel.attachment = clamp(rel.attachment + effect.attachment_delta)
    return rel


def is_betrayal(kind_exclusive: bool, partner_had_other_active_link: bool) -> bool:
    """Измена — только когда есть договорённость о моногамии и параллельная связь.

    Параллельные связи при свободных отношениях измену не образуют.
    """
    return kind_exclusive and partner_had_other_active_link
