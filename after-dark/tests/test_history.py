import pytest

from after_dark.systems.relationships.history import (
    EndReason,
    PartnerHistory,
    RelationKind,
    Relationship,
)
from after_dark.systems.relationships.rules import apply_end_effect, is_betrayal


def test_start_and_end_keeps_record_in_history():
    history = PartnerHistory()
    history.start(partner_id=7, kind=RelationKind.CASUAL, day=3)
    rel = history.end(7, day=5, reason=EndReason.MUTUAL)
    assert rel is not None
    assert not rel.is_active
    assert len(history.entries) == 1
    assert history.active() == []


def test_duplicate_active_relationship_is_rejected():
    history = PartnerHistory()
    history.start(7, RelationKind.DATING, day=1)
    with pytest.raises(ValueError):
        history.start(7, RelationKind.DATING, day=2)


def test_same_partner_can_have_different_kinds():
    history = PartnerHistory()
    history.start(7, RelationKind.CASUAL, day=1)
    history.start(7, RelationKind.DATING, day=2)
    assert len(history.active()) == 2


def test_ending_nonexistent_relationship_returns_none():
    history = PartnerHistory()
    assert history.end(99, day=1, reason=EndReason.BREAKUP) is None


def test_parallel_relationships_with_several_partners():
    history = PartnerHistory()
    for partner in (1, 2, 3):
        history.start(partner, RelationKind.CASUAL, day=partner)
    history.end(2, day=10, reason=EndReason.MUTUAL)
    assert {r.partner_id for r in history.active()} == {1, 3}


def test_serialization_roundtrip():
    history = PartnerHistory()
    history.start(5, RelationKind.EXCLUSIVE, day=4)
    history.end(5, day=9, reason=EndReason.BETRAYAL)
    restored = PartnerHistory.from_list(history.to_list())
    assert restored == history


def test_betrayal_only_with_exclusive_agreement():
    assert is_betrayal(kind_exclusive=True, partner_had_other_active_link=True)
    assert not is_betrayal(kind_exclusive=False, partner_had_other_active_link=True)
    assert not is_betrayal(kind_exclusive=True, partner_had_other_active_link=False)


def test_mutual_end_has_no_trust_penalty():
    rel = Relationship(partner_id=1, kind=RelationKind.DATING, started_day=0, trust=60, attachment=40)
    apply_end_effect(rel, EndReason.MUTUAL)
    assert rel.trust == 60
    assert rel.attachment < 40


def test_betrayal_lowers_trust_and_is_clamped():
    rel = Relationship(partner_id=1, kind=RelationKind.EXCLUSIVE, started_day=0, trust=10, attachment=5)
    apply_end_effect(rel, EndReason.BETRAYAL)
    assert rel.trust == 0
    assert rel.attachment == 0
