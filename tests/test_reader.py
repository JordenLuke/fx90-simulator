import asyncio

import pytest

from fx90_simulator.simulator.reader import Reader


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reader_emits_configured_number_of_runner_tags() -> None:
    reader = Reader()
    reader.update_test_config({
        "runner_count": 5,
        "bib_start": 1,
        "bib_end": 5,
        "noise_percent": 0,
        "max_burst_size": 5,
        "between_bursts_min": 0,
        "between_bursts_max": 0,
    })
    messages: list[str] = []

    async def sender(message: str) -> None:
        messages.append(message)

    async def closer() -> None:
        pass

    reader.register_sender(sender, closer)
    await reader.start()
    for _ in range(20):
        if reader.test_status()["good_tags_sent"] == 5:
            break
        await asyncio.sleep(0.01)
    await reader.stop()

    assert reader.test_status()["good_tags_sent"] == 5
    assert len(messages) == 5


@pytest.mark.unit
def test_runtime_settings_cannot_change_while_running() -> None:
    reader = Reader()
    reader.radio_active = True
    with pytest.raises(RuntimeError):
        reader.update_test_config({"runner_count": 10})
