import asyncio

import pytest

from fx90_simulator.simulator.reader import Reader


@pytest.mark.websocket
@pytest.mark.asyncio
async def test_disconnect_after_tag_count() -> None:
    reader = Reader()
    reader.update_test_config({
        "runner_count": 10,
        "bib_start": 1,
        "bib_end": 10,
        "noise_percent": 0,
        "max_burst_size": 1,
        "between_bursts_min": 0,
        "between_bursts_max": 0,
        "disconnect_after_tags": 2,
    })
    closed = asyncio.Event()

    async def sender(_: str) -> None:
        pass

    async def closer() -> None:
        closed.set()

    reader.register_sender(sender, closer)
    await reader.start()
    for _ in range(50):
        if closed.is_set():
            break
        await asyncio.sleep(0.01)
    await reader.stop()

    assert closed.is_set()
    assert reader.test_status()["tags_sent"] == 2
    assert reader.test_status()["clients"] == 0


@pytest.mark.stress
@pytest.mark.asyncio
async def test_high_volume_runner_generation() -> None:
    reader = Reader()
    reader.update_test_config({
        "runner_count": 400,
        "bib_start": 1,
        "bib_end": 400,
        "noise_percent": 0,
        "max_burst_size": 20,
        "max_burst_seconds": 0,
        "between_bursts_min": 0,
        "between_bursts_max": 0,
    })
    count = 0

    async def sender(_: str) -> None:
        nonlocal count
        count += 1

    async def closer() -> None:
        pass

    reader.register_sender(sender, closer)
    await reader.start()
    for _ in range(200):
        if count == 400:
            break
        await asyncio.sleep(0.005)
    await reader.stop()

    assert count == 400
