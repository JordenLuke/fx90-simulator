import random
from pathlib import Path

import pytest

from fx90_simulator.simulator.scenario import ScenarioConfig, ScenarioScheduler
from fx90_simulator.simulator.scenario_loader import ScenarioLoader
from fx90_simulator.simulator.tag_generator import TagGenerator


SCENARIOS = Path(__file__).parents[1] / "src" / "fx90_simulator" / "scenarios"


@pytest.mark.unit
def test_builtin_scenarios_load() -> None:
    scenarios = ScenarioLoader(SCENARIOS).list()

    assert [scenario.name for scenario in scenarios] == ["Finish Line", "Short Burst", "Start Line"]
    assert all(scenario.runner_count > 0 for scenario in scenarios)


@pytest.mark.unit
def test_start_line_schedule_is_deterministic_and_bounded() -> None:
    scenario = ScenarioLoader(SCENARIOS).get("Start Line")
    first = ScenarioScheduler(scenario).arrivals
    second = ScenarioScheduler(scenario).arrivals

    assert first == second
    assert len(first) == 500
    assert first == sorted(first)
    assert min(first) >= 0
    assert max(first) <= scenario.duration_seconds


@pytest.mark.unit
def test_burst_never_exceeds_configured_maximum() -> None:
    scenario = ScenarioLoader(SCENARIOS).get("Start Line")
    scheduler = ScenarioScheduler(scenario)

    index = 0
    total = 0
    while index < len(scheduler.arrivals):
        count, start = scheduler.next_burst(index)
        assert 0 < count <= scenario.burst.max_size
        assert start == scheduler.arrivals[index]
        total += count
        index += count

    assert total == scenario.runner_count


@pytest.mark.unit
def test_scenario_validation_rejects_invalid_bib_range() -> None:
    scenario = ScenarioConfig.from_dict({
        "name": "Invalid",
        "version": 1,
        "type": "custom",
        "duration_seconds": 10,
        "runner_count": 2,
        "bib_start": 1,
        "bib_end": 1,
        "distribution": {
            "type": "truncated-normal",
            "center_seconds": 5,
            "spread_seconds": 1,
        },
        "burst": {"max_size": 1, "max_duration_seconds": 0.1},
        "noise": {"percent": 0},
    })

    with pytest.raises(ValueError, match="runner_count exceeds"):
        scenario.validate()


@pytest.mark.unit
def test_tag_generator_seed_controls_random_order_and_noise() -> None:
    first = TagGenerator(1, 500, 500, "random", rng=random.Random(12345))
    second = TagGenerator(1, 500, 500, "random", rng=random.Random(12345))

    assert first.race_tags() == second.race_tags()
    assert first.noise_tags == second.noise_tags


@pytest.mark.unit
def test_scenario_noise_is_additive_and_does_not_consume_runner_tags() -> None:
    scenario = ScenarioLoader(SCENARIOS).get("Start Line")
    rng = random.Random(scenario.random_seed)
    generator = TagGenerator(1, 500, 500, "random", rng=rng)
    remaining = generator.race_tags()
    runner_tags = []
    noise_tags = []

    for _ in range(scenario.runner_count):
        if rng.random() < scenario.noise.percent / 100:
            noise_tags.append(generator.next_noise_tag())
        runner_tags.append(generator.next_runner_tag(remaining, True))

    assert len(runner_tags) == 500
    assert len(set(runner_tags)) == 500
    assert not remaining
    assert len(noise_tags) > 0
    assert set(noise_tags).isdisjoint(runner_tags)
