from dataclasses import dataclass, field
import math
import random


@dataclass
class DistributionConfig:
    type: str
    center_seconds: float | None = None
    spread_seconds: float | None = None


@dataclass
class BurstConfig:
    max_size: int
    max_duration_seconds: float


@dataclass
class NoiseConfig:
    percent: float


@dataclass
class ScenarioConfig:
    name: str
    version: int
    type: str
    duration_seconds: float
    runner_count: int
    distribution: DistributionConfig
    burst: BurstConfig
    noise: NoiseConfig
    report_each_tag_once: bool = True
    random_seed: int | None = None
    time_scale: float = 1.0

    def validate(self) -> None:
        if self.version != 1:
            raise ValueError("unsupported scenario version")
        if self.duration_seconds <= 0:
            raise ValueError("scenario duration must be greater than 0")
        if self.runner_count < 1:
            raise ValueError("runner_count must be at least 1")
        if self.distribution.type not in {"truncated-normal", "log-normal"}:
            raise ValueError("distribution type must be truncated-normal or log-normal")
        if self.burst.max_size < 1:
            raise ValueError("burst max_size must be at least 1")
        if self.burst.max_duration_seconds < 0:
            raise ValueError("burst max_duration_seconds must be >= 0")
        if not 0 <= self.noise.percent <= 100:
            raise ValueError("noise percent must be between 0 and 100")
        if self.time_scale <= 0:
            raise ValueError("time_scale must be greater than 0")
        if self.distribution.type == "truncated-normal":
            if self.distribution.center_seconds is None or self.distribution.spread_seconds is None:
                raise ValueError("truncated-normal requires center_seconds and spread_seconds")
            if self.distribution.spread_seconds <= 0:
                raise ValueError("spread_seconds must be greater than 0")

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioConfig":
        distribution = data.get("distribution", {})
        burst = data.get("burst", {})
        noise = data.get("noise", {})
        scenario = cls(
            name=str(data["name"]),
            version=int(data.get("version", 1)),
            type=str(data.get("type", "custom")),
            duration_seconds=float(data["duration_seconds"]),
            runner_count=int(data["runner_count"]),
            distribution=DistributionConfig(
                type=str(distribution["type"]),
                center_seconds=(float(distribution["center_seconds"]) if distribution.get("center_seconds") is not None else None),
                spread_seconds=(float(distribution["spread_seconds"]) if distribution.get("spread_seconds") is not None else None),
            ),
            burst=BurstConfig(
                max_size=int(burst["max_size"]),
                max_duration_seconds=float(burst.get("max_duration_seconds", 0.8)),
            ),
            noise=NoiseConfig(percent=float(noise.get("percent", 0))),
            report_each_tag_once=bool(data.get("report_each_tag_once", True)),
            random_seed=(int(data["random_seed"]) if data.get("random_seed") is not None else None),
            time_scale=float(data.get("time_scale", 1.0)),
        )
        scenario.validate()
        return scenario

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.type,
            "duration_seconds": self.duration_seconds,
            "runner_count": self.runner_count,
            "distribution": {
                "type": self.distribution.type,
                "center_seconds": self.distribution.center_seconds,
                "spread_seconds": self.distribution.spread_seconds,
            },
            "burst": {
                "max_size": self.burst.max_size,
                "max_duration_seconds": self.burst.max_duration_seconds,
            },
            "noise": {"percent": self.noise.percent},
            "report_each_tag_once": self.report_each_tag_once,
            "random_seed": self.random_seed,
            "time_scale": self.time_scale,
        }


@dataclass
class ScenarioScheduler:
    scenario: ScenarioConfig
    rng: random.Random = field(init=False)
    arrivals: list[float] = field(init=False)

    def __post_init__(self) -> None:
        self.scenario.validate()
        self.rng = random.Random(self.scenario.random_seed)
        self.arrivals = self._build_arrivals()

    def _build_arrivals(self) -> list[float]:
        count = self.scenario.runner_count
        duration = self.scenario.duration_seconds
        distribution = self.scenario.distribution
        if distribution.type == "truncated-normal":
            center = distribution.center_seconds or 0
            spread = distribution.spread_seconds or 1
            values = []
            while len(values) < count:
                value = self.rng.gauss(center, spread)
                if 0 <= value <= duration:
                    values.append(value)
        else:
            # A median around 60% of the scenario duration gives a long finish tail.
            mu = math.log(max(duration * 0.35, 1))
            sigma = 1.0
            values = [min(duration, self.rng.lognormvariate(mu, sigma)) for _ in range(count)]
        values.sort()
        return values

    def next_burst(self, index: int) -> tuple[int, float]:
        if index >= len(self.arrivals):
            raise StopIteration
        start = self.arrivals[index]
        end = start + self.scenario.burst.max_duration_seconds
        count = 1
        while index + count < len(self.arrivals) and count < self.scenario.burst.max_size:
            if self.arrivals[index + count] > end:
                break
            count += 1
        return count, start
