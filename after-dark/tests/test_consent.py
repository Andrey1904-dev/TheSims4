import pytest

from after_dark.systems.sexuality.consent import (
    ConsentError,
    OfferKind,
    OfferState,
    make_offer,
)


def test_adults_can_make_offer():
    offer = make_offer(1, initiator_id=10, initiator_age=25, target_id=11, target_age=30,
                       kind=OfferKind.DATE)
    assert offer.state is OfferState.PENDING
    assert offer.is_open


@pytest.mark.parametrize("ages", [(17, 25), (25, 17), (16, 16)])
def test_minors_are_rejected(ages):
    with pytest.raises(ConsentError):
        make_offer(1, 10, ages[0], 11, ages[1], OfferKind.CASUAL)


def test_cannot_offer_to_self():
    with pytest.raises(ConsentError):
        make_offer(1, 10, 25, 10, 25, OfferKind.DATE)


def test_decline_is_final_and_recorded():
    offer = make_offer(1, 10, 25, 11, 25, OfferKind.CASUAL)
    offer.decline()
    assert offer.state is OfferState.DECLINED
    assert offer.history == ["declined"]
    with pytest.raises(ConsentError):
        offer.accept()


def test_accept_then_withdraw_is_not_allowed_after_close():
    offer = make_offer(1, 10, 25, 11, 25, OfferKind.EXCLUSIVE)
    offer.accept()
    with pytest.raises(ConsentError):
        offer.withdraw()


def test_withdraw_before_answer():
    offer = make_offer(1, 10, 25, 11, 25, OfferKind.DATE)
    offer.withdraw()
    assert offer.state is OfferState.WITHDRAWN


def test_unknown_offer_kind_is_rejected():
    with pytest.raises(ValueError):
        make_offer(1, 10, 25, 11, 25, "something_else")
