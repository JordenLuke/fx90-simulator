from dataclasses import asdict, dataclass, fields

from .. import config


@dataclass
class TestConfig:
    """Runtime controls for stress and failure injection tests."""

    runner_count: int = config.RUNNER_COUNT
    bib_start: int = config.BIB_START
    bib_end: int = config.BIB_END
    tag_order: str = config.TAG_ORDER
    noise_percent: float = config.NOISE_PERCENT
    noise_tags: list[str] | None = None
    max_burst_size: int = config.MAX_BURST_SIZE
    max_burst_seconds: float = config.MAX_BURST_SECONDS
    between_bursts_min: float = config.BETWEEN_BURSTS_MIN
    between_bursts_max: float = config.BETWEEN_BURSTS_MAX
    report_each_tag_once: bool = config.REPORT_EACH_TAG_ONCE
    disconnect_after_tags: int = 0
    disconnect_after_seconds: float = 0.0
    tag_delay_ms: float = 0.0

    def validate(self) -> None:
        if self.bib_start < 1 or self.bib_end < self.bib_start:
            raise ValueError("bib range is invalid")
        available_bibs = self.bib_end - self.bib_start + 1
        if self.runner_count < 1 or self.runner_count > available_bibs:
            raise ValueError(
                f"runner_count ({self.runner_count}) exceeds the available bibs "
                f"({available_bibs}) in range {self.bib_start}-{self.bib_end}"
            )
        if self.tag_order not in {"random", "sequential"}:
            raise ValueError('tag_order must be "random" or "sequential"')
        if not 0 <= self.noise_percent <= 100:
            raise ValueError("noise_percent must be between 0 and 100")
        if self.noise_tags is not None:
            if not isinstance(self.noise_tags, list):
                raise ValueError("noise_tags must be a JSON array of strings")
            if any(not isinstance(tag, str) or not tag.strip() for tag in self.noise_tags):
                raise ValueError("noise_tags must contain only non-empty strings")
        if self.max_burst_size < 1:
            raise ValueError("max_burst_size must be at least 1")
        if self.max_burst_seconds < 0:
            raise ValueError("max_burst_seconds must be >= 0")
        if self.between_bursts_min < 0 or self.between_bursts_max < self.between_bursts_min:
            raise ValueError("between_bursts interval is invalid")
        if self.disconnect_after_tags < 0:
            raise ValueError("disconnect_after_tags must be >= 0")
        if self.disconnect_after_seconds < 0:
            raise ValueError("disconnect_after_seconds must be >= 0")
        if self.tag_delay_ms < 0:
            raise ValueError("tag_delay_ms must be >= 0")

    def update(self, values: dict) -> None:
        allowed = {field.name for field in fields(self)}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"unknown test settings: {', '.join(sorted(unknown))}")

        candidate = TestConfig(**asdict(self))
        for key, value in values.items():
            setattr(candidate, key, value)
        candidate.validate()

        for key, value in values.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        return asdict(self)
