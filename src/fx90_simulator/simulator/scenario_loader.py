import json
from pathlib import Path

from .scenario import ScenarioConfig


SCENARIOS_PATH = Path(__file__).resolve().parents[1] / "scenarios"


class ScenarioLoader:
    """Loads versioned built-in scenario definitions from JSON files."""

    def __init__(self, path: Path = SCENARIOS_PATH) -> None:
        self.path = path

    def list(self) -> list[ScenarioConfig]:
        scenarios = []
        for scenario_path in sorted(self.path.glob("*.json")):
            scenarios.append(self.load(scenario_path))
        return scenarios

    def load(self, path: Path) -> ScenarioConfig:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"unable to load scenario {path.name}: {exc}") from exc
        try:
            return ScenarioConfig.from_dict(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid scenario {path.name}: {exc}") from exc

    def get(self, name: str) -> ScenarioConfig:
        for scenario in self.list():
            if scenario.name.lower() == name.lower():
                return scenario
        raise KeyError(f"scenario not found: {name}")
