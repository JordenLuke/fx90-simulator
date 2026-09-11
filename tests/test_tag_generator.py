import re

import pytest

from fx90_simulator.simulator.tag_generator import TagGenerator


@pytest.mark.unit
def test_decimal_tag_format() -> None:
    generator = TagGenerator(1, 10, 10, "sequential")
    assert generator.race_tags()[0] == "000000000000000000000001"
    assert generator.race_tags()[-1] == "000000000000000000000010"


@pytest.mark.unit
def test_500_runner_tags_use_decimal_last_four_characters() -> None:
    generator = TagGenerator(1, 500, 500, "sequential")
    tags = generator.race_tags()

    assert len(tags) == 500
    assert len(set(tags)) == 500
    assert all(len(tag) == 24 for tag in tags)
    assert all(re.fullmatch(r"[0-9A-F]{20}[0-9]{4}", tag) for tag in tags)
    assert tags[0][-4:] == "0001"
    assert tags[-1][-4:] == "0500"


@pytest.mark.unit
def test_sequential_runner_tags_are_unique() -> None:
    generator = TagGenerator(100, 109, 10, "sequential")
    tags = generator.race_tags()
    assert len(tags) == 10
    assert len(set(tags)) == 10


@pytest.mark.unit
def test_random_order_contains_same_runners() -> None:
    generator = TagGenerator(1, 20, 20, "random")
    assert set(generator.race_tags()) == set(TagGenerator(1, 20, 20, "sequential").race_tags())


@pytest.mark.unit
def test_runner_count_must_fit_range() -> None:
    with pytest.raises(ValueError):
        TagGenerator(1, 10, 11, "random")


@pytest.mark.unit
def test_bib_range_must_fit_four_decimal_digits() -> None:
    with pytest.raises(ValueError):
        TagGenerator(1, 10000, 1, "sequential")


@pytest.mark.unit
def test_report_each_tag_once_never_emits_duplicate_runner_tags() -> None:
    generator = TagGenerator(1, 10, 10, "random")
    remaining = generator.race_tags()

    emitted = [
        generator.next_tag(remaining, noise_percent=0, report_each_tag_once=True)[0]
        for _ in range(10)
    ]

    assert len(emitted) == 10
    assert len(set(emitted)) == 10
    assert not remaining


@pytest.mark.unit
def test_report_each_tag_once_still_allows_noise() -> None:
    generator = TagGenerator(1, 3, 3, "sequential", noise_tags=["noise-tag"])
    remaining = generator.race_tags()

    tag, is_noise = generator.next_tag(remaining, noise_percent=100, report_each_tag_once=True)

    assert tag == "noise-tag"
    assert is_noise is True
    assert len(remaining) == 3


@pytest.mark.unit
def test_generated_noise_is_valid_hex_and_disjoint_from_runner_tags() -> None:
    generator = TagGenerator(1, 500, 500, "sequential", noise_pool_size=100)
    runner_tags = set(generator.race_tags())

    assert len(generator.noise_tags) == 100
    assert len(set(generator.noise_tags)) == 100
    assert set(generator.noise_tags).isdisjoint(runner_tags)
    assert all(re.fullmatch(r"[0-9A-F]{24}", tag) for tag in generator.noise_tags)
