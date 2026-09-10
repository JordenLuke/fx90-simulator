import json

import pytest

from fx90_simulator.simulator.scenarios import ScenarioLoader
from fx90_simulator.simulator.test_config import TestConfig


@pytest.mark.unit
def test_scenario_loader_lists_json_files(tmp_path):
    (tmp_path / "start-line.json").write_text(
        json.dumps(
            {
                "name": "Start Line Test",
                "description": "Compact start",
                "settings": {"simulation_mode": "start-line", "runner_count": 10},
            }
        ),
        encoding="utf-8",
    )

    scenarios = ScenarioLoader(tmp_path).list()

    assert len(scenarios) == 1
    assert scenarios[0].id == "start-line"
    assert scenarios[0].settings["runner_count"] == 10


@pytest.mark.unit
def test_scenario_loader_rejects_missing_settings(tmp_path):
    (tmp_path / "bad.json").write_text(
        json.dumps({"name": "Bad", "description": "Missing settings"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="settings"):
        ScenarioLoader(tmp_path).list()


@pytest.mark.unit
def test_finish_line_configuration_is_valid():
    config = TestConfig(simulation_mode="finish-line", duration_hours=16)
    config.validate()
