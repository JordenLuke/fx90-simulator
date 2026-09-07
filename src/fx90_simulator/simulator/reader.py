import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from datetime import datetime

from .. import config
from .events import create_tag_event
from .tag_generator import TagGenerator

Sender = Callable[[str], Awaitable[None]]
logger = logging.getLogger(__name__)


class Reader:
    """Simulates the subset of FXR90 reader behavior consumed by Ultra Tracker."""

    def __init__(self) -> None:
        self.radio_active = False
        self.event_num = 0
        self._task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._senders: set[Sender] = set()
        self._tag_generator = TagGenerator()
        self._tags_sent = 0
        self._good_tags_sent = 0
        self._noise_tags_sent = 0

    def register_sender(self, sender: Sender) -> None:
        self._senders.add(sender)
        logger.info("[FX90] WebSocket CONNECTED | clients=%d", len(self._senders))

    def unregister_sender(self, sender: Sender) -> None:
        self._senders.discard(sender)
        logger.info("[FX90] WebSocket DISCONNECTED | clients=%d", len(self._senders))

    def status(self) -> dict:
        return {
            "antennas": {str(i): "connected" for i in range(1, 7)},
            "ble": {
                "beaconCounts": {
                    "altBeacon": 0,
                    "eddystone": 0,
                    "generic": 0,
                    "iBeacon": 0,
                    "total": 0,
                },
                "scanStartTime": "",
                "scanState": "scanning" if self.radio_active else "stopped",
            },
            "cpu": {"system": 0, "user": 1},
            "flash": {
                key: {"free": 0, "total": 0, "used": 0}
                for key in ["platform", "readerConfig", "readerData", "rootFileSystem"]
            },
            "impinjGen2X": {"feature": "none", "isActive": False},
            "interfaceConnectionStatus": {
                "data": [{
                    "connectionError": "",
                    "connectionStatus": "connected" if self._senders else "disconnected",
                    "description": "WEBSOCKET_TEST",
                    "interface": "WEBSOCKET_TEST",
                }]
            },
            "ntp": {"offset": 0, "reach": -1},
            "powerNegotiation": "POE+",
            "powerSource": "PWR_BRICK",
            "radioActivity": "active" if self.radio_active else "inactive",
            "radioConnection": "connected",
            "ram": {"free": 70, "total": 100, "used": 30},
            "systemTime": datetime.now().strftime("%m/%d/%Y %H:%M"),
            "temperature": 31,
            "uptime": "0D0H0M0S",
        }

    def mode(self) -> dict:
        return {
            "delayBetweenAntennaCycles": {"duration": 0, "type": "DISABLED"},
            "environment": "AUTO_DETECT",
            "transmitPower": [27, 27, 27, 27, 27, 27],
            "type": "CUSTOM",
        }

    async def start(self) -> None:
        if self.radio_active:
            return
        self.radio_active = True
        self._tags_sent = 0
        self._good_tags_sent = 0
        self._noise_tags_sent = 0
        self._task = asyncio.create_task(self._generate_race())
        self._heartbeat_task = asyncio.create_task(self._heartbeat())
        logger.info("[FX90] SCANNING | sent=0 good=0 noise=0 clients=%d", len(self._senders))

    async def stop(self) -> None:
        self.radio_active = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        self._heartbeat_task = None
        logger.info(
            "[FX90] STOPPED | sent=%d good=%d noise=%d clients=%d",
            self._tags_sent,
            self._good_tags_sent,
            self._noise_tags_sent,
            len(self._senders),
        )

    async def _heartbeat(self) -> None:
        while self.radio_active:
            await asyncio.sleep(config.HEARTBEAT_SECONDS)
            if not self.radio_active:
                return
            logger.info(
                "[FX90] SCANNING | sent=%d good=%d noise=%d clients=%d",
                self._tags_sent,
                self._good_tags_sent,
                self._noise_tags_sent,
                len(self._senders),
            )

    async def _generate_race(self) -> None:
        if config.MAX_BURST_SIZE < 1:
            raise RuntimeError("FX90_MAX_BURST_SIZE must be at least 1")
        remaining = self._tag_generator.race_tags()
        race_complete_logged = False
        while self.radio_active:
            if config.REPORT_EACH_TAG_ONCE and not remaining:
                if not race_complete_logged:
                    race_complete_logged = True
                    logger.info(
                        "[FX90] RACE COMPLETE | sent=%d good=%d noise=%d clients=%d",
                        self._tags_sent,
                        self._good_tags_sent,
                        self._noise_tags_sent,
                        len(self._senders),
                    )
                await asyncio.sleep(1)
                continue

            count = min(
                random.randint(1, config.MAX_BURST_SIZE),
                len(remaining) if config.REPORT_EACH_TAG_ONCE else config.MAX_BURST_SIZE,
            )

            for _ in range(count):
                tag_id, is_noise = self._tag_generator.next_tag(remaining)
                self.event_num += 1
                self._tags_sent += 1
                if is_noise:
                    self._noise_tags_sent += 1
                else:
                    self._good_tags_sent += 1
                await self._broadcast(create_tag_event(self.event_num, tag_id))
                if count > 1:
                    await asyncio.sleep(
                        random.uniform(
                            config.MAX_BURST_SECONDS / count * 0.25,
                            config.MAX_BURST_SECONDS / count * 1.5,
                        )
                    )

            await asyncio.sleep(
                random.uniform(config.BETWEEN_BURSTS_MIN, config.BETWEEN_BURSTS_MAX)
            )

    async def _broadcast(self, message: str) -> None:
        for sender in list(self._senders):
            try:
                await sender(message)
            except Exception:
                self.unregister_sender(sender)
