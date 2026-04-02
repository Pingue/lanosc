"""Minecraft server-side Paper plugin integration.

A Paper plugin on the organizer-controlled Minecraft server sends UDP JSON
events to LANOSC. This adapter listens for those events and triggers named
LANOSC playbacks.

Expected datagram payload (JSON object):

    {
      "event": "player_death",
      "player": "username",
      "ts": 1710000000.1
    }

Only the ``event`` field is required.

The matching Paper plugin source lives in games/minecraft_plugin/.
"""

from __future__ import annotations

import asyncio
import json
import socket
import time
from collections.abc import Mapping
from typing import Any

from lanosc import BaseGameAdapter


DEFAULT_CUE_MAP: dict[str, str] = {
    "player_join": "mc_player_join",
    "player_leave": "mc_player_leave",
    "player_death": "mc_player_death",
    "advancement_unlock": "mc_advancement",
    "challenge_start": "mc_challenge_start",
    "challenge_win": "mc_challenge_win",
}

DEFAULT_COOLDOWNS: dict[str, float] = {
    "player_join": 0.5,
    "player_leave": 0.5,
    "player_death": 0.5,
    "advancement_unlock": 0.5,
    "challenge_start": 5.0,
    "challenge_win": 5.0,
}


class MinecraftAdapter(BaseGameAdapter):
    name = "minecraft"

    def __init__(self, bridge, config=None):
        super().__init__(bridge=bridge, config=config)

        self.listen_host = str(self.config.get("listen_host", "127.0.0.1"))
        self.listen_port = int(self.config.get("listen_port", 10052))
        self.log_unknown_events = bool(self.config.get("log_unknown_events", True))
        self.queue_size = int(self.config.get("queue_size", 2048))

        raw_map = self.config.get("cue_map", {})
        if raw_map and not isinstance(raw_map, Mapping):
            raise ValueError("minecraft.cue_map must be a table of event_name -> playback_name")
        self.cue_map: dict[str, str] = {**DEFAULT_CUE_MAP, **{str(k): str(v) for k, v in dict(raw_map).items()}}

        raw_cooldowns = self.config.get("cooldowns", {})
        if raw_cooldowns and not isinstance(raw_cooldowns, Mapping):
            raise ValueError("minecraft.cooldowns must be a table of event_name -> seconds")
        self.cooldowns: dict[str, float] = {**DEFAULT_COOLDOWNS}
        for key, value in dict(raw_cooldowns).items():
            self.cooldowns[str(key)] = float(value)

        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_size)
        self._socket: socket.socket | None = None
        self._recv_task: asyncio.Task[None] | None = None
        self._last_trigger: dict[str, float] = {}

    async def setup(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self.listen_host, self.listen_port))
        self._socket.setblocking(False)
        self.log.info("Minecraft listener bound on udp://%s:%s", self.listen_host, self.listen_port)

        self._recv_task = asyncio.create_task(self._recv_loop(), name="minecraft-udp-recv")

    async def run(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.25)
            except TimeoutError:
                continue

            self._handle_event(event)

    async def shutdown(self) -> None:
        if self._recv_task is not None:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass
            self._recv_task = None

        if self._socket is not None:
            self._socket.close()
            self._socket = None

    async def _recv_loop(self) -> None:
        assert self._socket is not None
        loop = asyncio.get_running_loop()
        while True:
            data, _peer = await loop.sock_recvfrom(self._socket, 65535)
            try:
                decoded = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.log.debug("Ignoring non-JSON Minecraft datagram")
                continue

            if isinstance(decoded, str):
                event = {"event": decoded}
            elif isinstance(decoded, dict):
                event = decoded
            else:
                self.log.debug("Ignoring Minecraft datagram with unsupported JSON payload type")
                continue

            if self._queue.full():
                self.log.warning("Minecraft event queue full; dropping event: %s", event)
                continue

            self._queue.put_nowait(event)

    def _handle_event(self, event: Mapping[str, Any]) -> None:
        event_name_raw = event.get("event", event.get("type"))
        if not isinstance(event_name_raw, str) or not event_name_raw:
            self.log.debug("Ignoring Minecraft event without a valid event name: %s", event)
            return

        event_name = event_name_raw.strip().lower()

        playback = self.cue_map.get(event_name)
        if not playback:
            if self.log_unknown_events:
                self.log.info("Unmapped Minecraft event: %s", event_name)
            return

        now = time.monotonic()
        cooldown = max(0.0, self.cooldowns.get(event_name, 0.0))
        last = self._last_trigger.get(event_name)
        if last is not None and (now - last) < cooldown:
            return

        self._last_trigger[event_name] = now
        try:
            self.trigger_playback(playback)
            self.log.info("Minecraft cue %s -> playback %s", event_name, playback)
        except KeyError:
            self.log.warning("Minecraft cue %s mapped to unknown playback %s", event_name, playback)
