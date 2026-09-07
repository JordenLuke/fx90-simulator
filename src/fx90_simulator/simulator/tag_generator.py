import random

from .. import config


class TagGenerator:
    """Loads legitimate runner tags and supplies configurable noise tags."""

    def __init__(self) -> None:
        self.tags = self._load_tags()
        self.noise_tags = [
            f"E200341201{number:08X}"
            for number in range(1, config.NOISE_POOL_SIZE + 1)
        ]

    def _load_tags(self) -> list[str]:
        if config.TAGS_FILE.exists():
            import json

            data = json.loads(config.TAGS_FILE.read_text(encoding="utf-8"))
            tags = data.get("tags", []) if isinstance(data, dict) else data
        else:
            tags = []

        tags = [str(tag) for tag in tags]
        if len(tags) < config.RUNNER_COUNT:
            tags = [f"{number:024X}" for number in range(1, config.RUNNER_COUNT + 1)]
        return tags[: config.RUNNER_COUNT]

    def race_tags(self) -> list[str]:
        tags = list(self.tags)
        random.shuffle(tags)
        return tags

    def next_tag(self, remaining: list[str]) -> tuple[str, bool]:
        is_noise = random.random() < config.NOISE_PERCENT / 100
        if is_noise:
            if not self.noise_tags:
                raise RuntimeError("FX90_NOISE_POOL_SIZE must be at least 1")
            return random.choice(self.noise_tags), True
        if config.REPORT_EACH_TAG_ONCE:
            if not remaining:
                raise RuntimeError("FX90_RUNNER_COUNT must be at least 1")
            return remaining.pop(), False
        if not self.tags:
            raise RuntimeError("FX90_RUNNER_COUNT must be at least 1")
        return random.choice(self.tags), False
