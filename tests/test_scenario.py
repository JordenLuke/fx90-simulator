import asyncio
import random
from pathlib import Path

import pytest

from fx90_simulator.simulator.reader import Reader
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
def test_burst_duration_matches_scheduled_arrivals() -> None:
    scenario = ScenarioLoader(SCENARIOS).get("Start Line")
    scheduler = ScenarioScheduler(scenario)

    index = 0
    while index < len(scheduler.arrivals):
        count, start = scheduler.next_burst(index)
        burst_arrivals = scheduler.arrivals[index:index + count]
        assert burst_arrivals[-1] - start <= scenario.burst.max_duration_seconds
        index += count


@pytest.mark.unit
def test_start_line_has_front_loaded_distribution() -> None:
    scenario = ScenarioLoader(SCENARIOS).get("Start Line")
    arrivals = ScenarioScheduler(scenario).arrivals

    first_15_minutes = sum(value <= 900 for value in arrivals)
    first_30_minutes = sum(value <= 1800 for value in arrivals)

    assert first_15_minutes >= 300
    assert first_30_minutes >= 450


@pytest.mark.unit
def test_finish_line_has_long_tail() -> None:
    scenario = ScenarioLoader(SCENARIOS).get("Finish Line")
    arrivals = ScenarioScheduler(scenario).arrivals

    first_2_hours = sum(value <= 7200 for value in arrivals)
    final_2_hours = sum(value >= scenario.duration_seconds - 7200 for value in arrivals)

    assert first_2_hours < scenario.runner_count * 0.7
    assert final_2_hours > 0
    assert max(arrivals) > scenario.duration_seconds * 0.8


@pytest.mark.unit
def test_scenario_validation_rejects_invalid_bib_range() -> None:
    with pytest.raises(ValueError, match="runner_count exceeds"):
        ScenarioConfig.from_dict({
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
            "random_seed": 1,
        })


@pytest.mark.unit
def test_scenario_validation_rejects_unseeded_or_infeasible_distribution() -> None:
    base = {
        "name": "Invalid",
        "version": 1,
        "type": "custom",
        "duration_seconds": 10,
        "runner_count": 1,
        "bib_start": 1,
        "bib_end": 1,
        "distribution": {"type": "truncated-normal", "center_seconds": 5, "spread_seconds": 1},
        "burst": {"max_size": 1, "max_duration_seconds": 0.1},
        "noise": {"percent": 0},
    }
    with pytest.raises(ValueError, match="random_seed"):
        ScenarioConfig.from_dict(base)
    base["random_seed"] = 1
    base["distribution"] = {"type": "truncated-normal", "center_seconds": 1e12, "spread_seconds": 1}
    with pytest.raises(ValueError, match="negligible probability"):
        ScenarioConfig.from_dict(base)


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


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reader_scenario_uses_scenario_bibs_and_additive_noise() -> None:
    reader = Reader()
    reader.set_scenario(ScenarioConfig.from_dict({
        "name": "Reader Test",
        "version": 1,
        "type": "custom",
        "duration_seconds": 0.01,
        "runner_count": 3,
        "bib_start": 700,
        "bib_end": 702,
        "distribution": {"type": "truncated-normal", "center_seconds": 0.001, "spread_seconds": 0.0001},
        "burst": {"max_size": 3, "max_duration_seconds": 0.1},
        "noise": {"percent": 100},
        "random_seed": 7,
    }))
    reader.test_config.tag_order = "sequential"
    await reader.start_scenario()
    for _ in range(100):
        if not reader.radio_active:
            break
        await asyncio.sleep(0.001)
    await reader.stop()

    assert reader._good_tags_sent == 3
    assert reader._noise_tags_sent == 3
