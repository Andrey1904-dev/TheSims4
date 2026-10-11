"""Согласие участников.

Правила:
* оба участника должны быть совершеннолетними;
* любое взаимодействие начинается с предложения, которое нужно явно принять;
* отказ не даёт штрафов сам по себе;
* согласие можно отозвать в любой момент, в том числе после принятия.

Модуль не запускает никаких интимных действий: он только решает,
разрешено ли предложение, и хранит состояние согласия.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from after_dark.core.constants import MIN_ADULT_AGE


class ConsentError(ValueError):
    """Предложение нарушает правила согласия."""


class OfferKind(str, Enum):
    DATE = "date"                    # предложение свидания
    CASUAL = "casual"                # непродолжительная связь без обязательств
    EXCLUSIVE = "exclusive"          # переход к моногамным отношениям


class OfferState(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


@dataclass
class ConsentOffer:
    offer_id: int
    initiator_id: int
    target_id: int
    kind: OfferKind
    state: OfferState = OfferState.PENDING
    history: list[str] = field(default_factory=list)

    @property
    def is_open(self) -> bool:
        return self.state is OfferState.PENDING

    def accept(self) -> None:
        self._transition(OfferState.ACCEPTED, "accepted")

    def decline(self) -> None:
        """Отказ — нормальный исход, без последствий для репутации."""
        self._transition(OfferState.DECLINED, "declined")

    def withdraw(self) -> None:
        """Инициатор отзывает предложение до ответа."""
        self._transition(OfferState.WITHDRAWN, "withdrawn")

    def _transition(self, new_state: OfferState, label: str) -> None:
        if not self.is_open:
            raise ConsentError(f"Предложение {self.offer_id} уже закрыто ({self.state.value}).")
        self.state = new_state
        self.history.append(label)


def check_adults(*ages: int) -> None:
    """Все участники должны быть совершеннолетними."""
    for age in ages:
        if not isinstance(age, int) or age < MIN_ADULT_AGE:
            raise ConsentError("Все участники должны быть совершеннолетними.")


def make_offer(offer_id: int, initiator_id: int, initiator_age: int,
               target_id: int, target_age: int, kind: OfferKind) -> ConsentOffer:
    if initiator_id == target_id:
        raise ConsentError("Нельзя сделать предложение самому себе.")
    check_adults(initiator_age, target_age)
    return ConsentOffer(offer_id=offer_id, initiator_id=initiator_id,
                        target_id=target_id, kind=OfferKind(kind))
