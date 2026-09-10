import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    description: str
    settings: dict[str, Any]


class ScenarioLoader:
    """Loads simulation scenarios from JSON files in the scenarios directory."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def list(self) -> list[Scenario]:
        scenarios: list[Scenario] = []
        if not self.directory.exists():
            return scenarios

        for path in sorted(self.directory.glob("*.json")):
            try:
                scenarios.append(self._load_path(path))
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"invalid scenario file {path.name}: {exc}") from exc
        return scenarios

    def get(self, scenario_id: str) -> Scenario:
        path = self.directory / f"{scenario_id}.json"
        if path.suffix != ".json" or path.name != f"{scenario_id}.json":
            raise ValueError("invalid scenario id")
        if not path.is_file():
            raise KeyError(scenario_id)
        return self._load_path(path)

    def _load_path(self, path: Path) -> Scenario:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("scenario must be a JSON object")

        scenario_id = path.stem
        name = data.get("name")
        description = data.get("description", "")
        settings = data.get("settings")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(description, str):
            raise ValueError("description must be a string")
        if not isinstance(settings, dict):
            raise ValueError("settings must be a JSON object")

        return Scenario(
            id=scenario_id,
            name=name,
            description=description,
            settings=settings,
        )
