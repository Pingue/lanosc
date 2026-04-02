"""CS2 Game State Integration adapter.

CS2 GSI sends HTTP POST requests containing the full game state to a configured
endpoint. This adapter runs a minimal async HTTP server, tracks state transitions,
and triggers named LANOSC playbacks.

The adapter is designed to run from a GOTV/observer machine (organizer-controlled).
No participant machine changes are required.

GSI config file: games/cs2_gsi/gamestate_integration_lanosc.cfg
Setup notes:     games/CS2.md
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from typing import Any

from lanosc import BaseGameAdapter


DEFAULT_CUE_MAP: dict[str, str] = {
    "round_started": "cs2_round_start",
    "round_ended": "cs2_round_end",
    "bomb_planted": "cs2_bomb_planted",
    "bomb_defused": "cs2_bomb_defused",
    "bomb_exploded": "cs2_bomb_exploded",
    "match_ended": "cs2_match_end",
}

# CS2 GSI phase values
_ROUND_LIVE = "live"
_ROUND_OVER = "over"
_ROUND_FREEZE = "freezetime"
_MAP_GAMEOVER = "gameover"


class Cs2GsiAdapter(BaseGameAdapter):
    name = "cs2"

    def __init__(self, bridge, config=None):
        super().__init__(bridge=bridge, config=config)

        self.listen_host = str(self.config.get("listen_host", "127.0.0.1"))
        self.listen_port = int(self.config.get("listen_port", 10053))
        self.queue_size = int(self.config.get("queue_size", 256))

        raw_map = self.config.get("cue_map", {})
        if raw_map and not isinstance(raw_map, Mapping):
            raise ValueError("cs2.cue_map must be a table of event_name -> playback_name")
        self.cue_map: dict[str, str] = {**DEFAULT_CUE_MAP, **{str(k): str(v) for k, v in dict(raw_map).items()}}

        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_size)
        self._server: asyncio.Server | None = None
        self._prev_state: dict[str, Any] = {}

    async def setup(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.listen_host,
            self.listen_port,
        )
        self.log.info("CS2 GSI listener bound on http://%s:%s/", self.listen_host, self.listen_port)

    async def run(self, stop_event: asyncio.Event) -> None:
        assert self._server is not None
        async with self._server:
            while not stop_event.is_set():
                try:
                    state = await asyncio.wait_for(self._queue.get(), timeout=0.25)
                except TimeoutError:
                    continue
                self._process_state(state)

    async def shutdown(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not request_line:
                return

            parts = request_line.decode(errors="replace").split()
            if len(parts) < 2 or parts[0] != "POST":
                writer.write(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
                await writer.drain()
                return

            headers: dict[str, str] = {}
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=5.0)
                if line in (b"\r\n", b"\n", b""):
                    break
                name, _, value = line.decode(errors="replace").partition(":")
                headers[name.strip().lower()] = value.strip()

            content_length = int(headers.get("content-length", "0"))
            body = b""
            if content_length > 0:
                body = await asyncio.wait_for(reader.readexactly(content_length), timeout=5.0)

            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()

            try:
                state = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.log.debug("Ignoring non-JSON CS2 GSI payload")
                return

            if not isinstance(state, dict):
                return

            if self._queue.full():
                self.log.warning("CS2 GSI queue full; dropping state update")
                return

            self._queue.put_nowait(state)

        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionResetError):
            pass
        finally:
            writer.close()

    def _process_state(self, state: dict[str, Any]) -> None:
        prev = self._prev_state
        self._prev_state = state

        map_phase = (state.get("map") or {}).get("phase", "")
        prev_map_phase = (prev.get("map") or {}).get("phase", "")

        round_phase = (state.get("round") or {}).get("phase", "")
        prev_round_phase = (prev.get("round") or {}).get("phase", "")

        bomb = (state.get("round") or {}).get("bomb", "")
        prev_bomb = (prev.get("round") or {}).get("bomb", "")

        if map_phase == _MAP_GAMEOVER and prev_map_phase != _MAP_GAMEOVER:
            self._fire("match_ended")
            return

        if round_phase == _ROUND_LIVE and prev_round_phase in (_ROUND_FREEZE, ""):
            self._fire("round_started")

        if round_phase == _ROUND_OVER and prev_round_phase == _ROUND_LIVE:
            self._fire("round_ended")

        if bomb == "planted" and prev_bomb != "planted":
            self._fire("bomb_planted")
        elif bomb == "defused" and prev_bomb != "defused":
            self._fire("bomb_defused")
        elif bomb == "exploded" and prev_bomb != "exploded":
            self._fire("bomb_exploded")

    def _fire(self, event_name: str) -> None:
        playback = self.cue_map.get(event_name)
        if not playback:
            self.log.info("Unmapped CS2 GSI event: %s", event_name)
            return
        try:
            self.trigger_playback(playback)
            self.log.info("CS2 cue %s -> playback %s", event_name, playback)
        except KeyError:
            self.log.warning("CS2 cue %s mapped to unknown playback %s", event_name, playback)
