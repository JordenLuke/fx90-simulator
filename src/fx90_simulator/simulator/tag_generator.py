import random


class TagGenerator:
    """Generates FXR90-compatible RFID tags from decimal bib numbers."""

    def __init__(self, bib_start: int, bib_end: int, runner_count: int, tag_order: str,
                 noise_tags: list[str] | None = None, noise_pool_size: int = 50) -> None:
        self.bibs = list(range(bib_start, bib_end + 1))
        if runner_count > len(self.bibs):
            raise ValueError("runner_count cannot exceed the configured bib range")
        self.runner_count = runner_count
        self.tag_order = tag_order
        self.noise_tags = list(noise_tags) if noise_tags else [
            self._tag_for_bib(bib_end + number)
            for number in range(1, noise_pool_size + 1)
        ]

    @staticmethod
    def _tag_for_bib(bib: int) -> str:
        return f"{'0' * 20}{bib}"

    def race_tags(self) -> list[str]:
        tags = self.bibs[: self.runner_count]
        if self.tag_order == "random":
            random.shuffle(tags)
        return [self._tag_for_bib(bib) for bib in tags]

    def next_tag(self, remaining: list[str], noise_percent: float, report_each_tag_once: bool) -> tuple[str, bool]:
        is_noise = random.random() < noise_percent / 100
        if is_noise:
            if not self.noise_tags:
                raise RuntimeError("noise tag pool must contain at least one tag when noise is enabled")
            return random.choice(self.noise_tags), True
        if report_each_tag_once:
            if not remaining:
                raise RuntimeError("no runner tags remain")
            return remaining.pop(), False
        tags = self.race_tags()
        return random.choice(tags), False
