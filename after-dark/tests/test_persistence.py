import json

from after_dark.core.constants import SAVE_SCHEMA_VERSION
from after_dark.core.persistence import dump_state, load_state
from after_dark.core.state import ModState
from after_dark.systems.relationships.history import EndReason, RelationKind
from after_dark.systems.reputation.reputation import ReputationEvent

COOLDOWN = 4 * 3600
MAX_PER_DAY = 6


def _build_state() -> ModState:
    state = ModState(day_index=12)
    sim = state.ensure_sim(sim_id=1001, age=25)
    sim.has_trait_new_experiences = True
    sim.history.start(2002, RelationKind.CASUAL, day=3)
    sim.history.start(3003, RelationKind.DATING, day=4)
    sim.history.end(2002, day=6, reason=EndReason.MUTUAL)
    sim.reputation.apply_event(ReputationEvent("interview", {"public": 8, "professional": 3}))
    sim.flirt.register(3003, now=1000.0, day_index=12)
    return state


def test_full_roundtrip_survives_json():
    state = _build_state()
    data = json.loads(json.dumps(dump_state(state)))
    warnings: list[str] = []
    restored = load_state(data, warnings, COOLDOWN, MAX_PER_DAY)
    assert warnings == []
    assert restored.day_index == 12
    sim = restored.sims[1001]
    assert sim.age == 25
    assert sim.has_trait_new_experiences is True
    assert len(sim.history.entries) == 2
    assert sim.history.find_active(3003) is not None
    assert sim.reputation.public == 8
    assert sim.flirt.last_flirt_at == {3003: 1000.0}


def test_saved_data_has_schema_and_no_flirt_settings_leak():
    data = dump_state(_build_state())
    assert data["schema_version"] == SAVE_SCHEMA_VERSION
    assert "_flirt_settings" not in data


def test_empty_or_missing_data_gives_empty_state_without_error():
    warnings: list[str] = []
    assert load_state(None, warnings, COOLDOWN, MAX_PER_DAY).sims == {}
    assert load_state({}, warnings, COOLDOWN, MAX_PER_DAY).sims == {}


def test_newer_schema_is_not_loaded():
    warnings: list[str] = []
    state = load_state({"schema_version": SAVE_SCHEMA_VERSION + 1, "sims": {"1": {}}},
                       warnings, COOLDOWN, MAX_PER_DAY)
    assert state.sims == {}
    assert warnings


def test_one_corrupt_sim_does_not_break_others():
    data = dump_state(_build_state())
    data["sims"]["555"] = {"history": [{"partner_id": "x", "kind": "??", "started_day": 0}]}
    data["sims"]["556"] = "garbage"
    warnings: list[str] = []
    restored = load_state(data, warnings, COOLDOWN, MAX_PER_DAY)
    assert 1001 in restored.sims
    assert 555 not in restored.sims
    assert 556 not in restored.sims
    assert len(warnings) == 2


def test_flirt_settings_come_from_current_config_not_file():
    data = dump_state(_build_state())
    restored = load_state(data, [], flirt_cooldown_seconds=60, flirt_max_per_day=1)
    assert restored.sims[1001].flirt.cooldown_seconds == 60
    assert restored.sims[1001].flirt.max_per_day == 1
