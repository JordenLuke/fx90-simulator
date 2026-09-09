import pytest

from fx90_simulator.simulator.tag_generator import TagGenerator


@pytest.mark.unit
def test_decimal_tag_format() -> None:
    generator = TagGenerator(1, 10, 10, "sequential")
    assert generator.race_tags()[0] == "000000000000000000001"
    assert generator.race_tags()[-1] == "0000000000000000000010"


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
