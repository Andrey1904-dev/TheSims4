import pytest

from after_dark.systems.reputation.reputation import Reputation, ReputationEvent


def test_public_event_applies_full_effect():
    rep = Reputation()
    applied = rep.apply_event(ReputationEvent("interview", {"public": 10}, publicity=1.0))
    assert applied == {"public": 10}
    assert rep.public == 10


def test_private_event_is_scaled_down():
    rep = Reputation()
    applied = rep.apply_event(ReputationEvent("private_dinner", {"public": -10}, publicity=0.0))
    assert applied == {"public": 0}
    assert rep.public == 0


def test_values_are_clamped_to_range():
    rep = Reputation(public=95)
    rep.apply_event(ReputationEvent("viral", {"public": 50}))
    assert rep.public == 100


def test_unknown_axis_is_rejected():
    with pytest.raises(ValueError):
        ReputationEvent("bad", {"morality": -5})


def test_publicity_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        ReputationEvent("bad", {"public": -5}, publicity=1.5)


def test_no_events_means_no_change():
    rep = Reputation(public=20, circle=-5)
    snapshot = rep.to_dict()
    assert rep.to_dict() == snapshot


def test_decay_moves_toward_zero_without_overshoot():
    rep = Reputation(public=2, circle=-1, professional=0)
    rep.decay_toward_neutral(amount=5)
    assert (rep.public, rep.circle, rep.professional) == (0, 0, 0)


def test_fame_grows_only_with_public_negative_events():
    rep = Reputation()
    rep.apply_event(ReputationEvent("praise", {"public": 5}, publicity=1.0))
    assert rep.fame == 0
    rep.apply_event(ReputationEvent("scandal", {"public": -5}, publicity=1.0))
    assert rep.fame == 1


def test_roundtrip_and_corrupt_values_are_clamped():
    rep = Reputation.from_dict({"public": 500, "circle": "-900", "history": ["a"]})
    assert rep.public == 100
    assert rep.circle == -100
    assert rep.history == ["a"]
