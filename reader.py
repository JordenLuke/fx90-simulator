from dataclasses import dataclass
from datetime import datetime, timezone
import json

from config import settings


@dataclass
class Reader:
    state: str = "STOPPED"

    def status(self) -> dict:
        return {
            "state": self.state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def start(self) -> dict:
        self.state = "RUNNING"
        return self.status()

    def stop(self) -> dict:
        self.state = "STOPPED"
        return self.status()

    def load_tags(self) -> list[dict]:
        with open(settings.tags_file, "r", encoding="utf-8") as file:
            return json.load(file)


reader = Reader()
