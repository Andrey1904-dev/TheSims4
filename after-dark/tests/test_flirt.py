import random

from after_dark.systems.sexuality.flirt import (
    HOUR,
    FlirtLimiter,
    flirt_success_chance,
    roll_flirt,
)


def test_cooldown_blocks_repeat_flirt_with_same_partner():
    limiter = FlirtLimiter(cooldown_seconds=4 * HOUR, max_per_day=10)
    assert limiter.can_flirt(1, now=0, day_index=0)
    limiter.register(1, now=0, day_index=0)
    assert not limiter.can_flirt(1, now=HOUR, day_index=0)
    assert limiter.can_flirt(1, now=4 * HOUR, day_index=0)


def test_cooldown_is_per_partner():
    limiter = FlirtLimiter(cooldown_seconds=4 * HOUR, max_per_day=10)
    limiter.register(1, now=0, day_index=0)
    assert limiter.can_flirt(2, now=1, day_index=0)


def test_daily_limit_stops_flirting_until_next_day():
    limiter = FlirtLimiter(cooldown_seconds=0, max_per_day=2)
    limiter.register(1, now=0, day_index=0)
    limiter.register(2, now=1, day_index=0)
    assert not limiter.can_flirt(3, now=2, day_index=0)
    assert limiter.can_flirt(3, now=100, day_index=1)


def test_limiter_roundtrip():
    limiter = FlirtLimiter(cooldown_seconds=HOUR, max_per_day=5)
    limiter.register(9, now=50.0, day_index=3)
    restored = FlirtLimiter.from_dict(limiter.to_dict(), HOUR, 5)
    assert restored.last_flirt_at == {9: 50.0}
    assert restored.day_index == 3
    assert restored.count_today == 1


def test_success_chance_is_bounded_and_trait_bonus_is_small():
    low = flirt_success_chance(0, 0, trait_bonus=0)
    high = flirt_success_chance(100, 100, trait_bonus=0)
    boosted = flirt_success_chance(100, 100, trait_bonus=999)
    assert 0.0 <= low <= high <= 0.95
    assert boosted - high <= 0.10 + 1e-9
    assert boosted <= 0.95


def test_roll_is_deterministic_with_seed():
    first = [roll_flirt(random.Random(42), 0.5) for _ in range(3)]
    second = [roll_flirt(random.Random(42), 0.5) for _ in range(3)]
    assert first == second
