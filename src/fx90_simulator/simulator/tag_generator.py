import random

from .. import config


class TagGenerator:
    """Generates FXR90-compatible RFID tags from decimal bib numbers."""

    def __init__(self) -> None:
        self.bibs = list(range(config.BIB_START, config.BIB_END + 1))
        if config.RUNNER_COUNT > len(self.bibs):
            raise ValueError(
                "FX90_RUNNER_COUNT cannot exceed the configured bib range "
                "(FX90_BIB_START through FX90_BIB_END)"
            )

        self.noise_tags = [
            self._tag_for_bib(config.BIB_END + number)
            for number in range(1, config.NOISE_POOL_SIZE + 1)
        ]

    @staticmethod
    def _tag_for_bib(bib: int) -> str:
        """Build the decimal idHex format consumed by Ultra Tracker."""
        return f"{'0' * 20}{bib}"

    def race_tags(self) -> list[str]:
        tags = self.bibs[: config.RUNNER_COUNT]
        if config.TAG_ORDER == "random":
            random.shuffle(tags)
        return [self._tag_for_bib(bib) for bib in tags]

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
        tags = self.race_tags()
        if not tags:
            raise RuntimeError("FX90_RUNNER_COUNT must be at least 1")
        return random.choice(tags), False
