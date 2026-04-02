"""Factorio server-side mod integration.

A server-side Factorio mod writes game events as JSON lines to a file in the
Factorio script-output directory. This adapter tails that file and triggers
named LANOSC playbacks.

The mod source lives in games/factorio_mod/.
Setup notes:      games/FACTORIO.md
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lanosc import BaseGameAdapter


DEFAULT_CUE_MAP: dict[str, str] = {
    "player_join": "factorio_player_join",
    "player_leave": "factorio_player_leave",
    "player_death": "factorio_player_death",
    "rocket_launched": "factorio_rocket_launched",
    "research_finished": "factorio_research",
}

_POLL_INTERVAL = 0.25


class FactorioAdapter(BaseGameAdapter):
    name = "factorio"

    def __init__(self, bridge, config=None):
        super().__init__(bridge=bridge, config=config)

        log_path_raw = self.config.get("log_path")
        if not isinstance(log_path_raw, str) or not log_path_raw:
            raise ValueError("factorio.log_path is required (path to the mod's event log file)")
        self.log_path = Path(log_path_raw)

        self.log_unknown_events = bool(self.config.get("log_unknown_events", True))

        raw_map = self.config.get("cue_map", {})
        if raw_map and not isinstance(raw_map, Mapping):
            raise ValueError("factorio.cue_map must be a table of event_name -> playback_name")
        self.cue_map: dict[str, str] = {**DEFAULT_CUE_MAP, **{str(k): str(v) for k, v in dict(raw_map).items()}}

    async def run(self, stop_event: asyncio.Event) -> None:
        # Wait for the log file to exist before starting to tail it.
        while not stop_event.is_set() and not self.log_path.exists():
            self.log.debug("Waiting for Factorio event log: %s", self.log_path)
            await asyncio.sleep(2.0)

        if stop_event.is_set():
            return

        self.log.info("Tailing Factorio event log: %s", self.log_path)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: None)  # yield to event loop

        partial = b""
        with self.log_path.open("rb") as fh:
            fh.seek(0, 2)  # seek to end — ignore history
            while not stop_event.is_set():
                chunk = fh.read(65536)
                if chunk:
                    partial += chunk
                    while b"\n" in partial:
                        line, _, partial = partial.partition(b"\n")
                        self._handle_line(line)
                else:
                    await asyncio.sleep(_POLL_INTERVAL)

    def _handle_line(self, raw: bytes) -> None:
        line = raw.strip()
        if not line:
            return
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.log.debug("Ignoring non-JSON line from Factorio log: %r", raw[:120])
            return

        if not isinstance(event, dict):
            return

        event_name_raw = event.get("event", event.get("type"))
        if not isinstance(event_name_raw, str) or not event_name_raw:
            return

        event_name = event_name_raw.strip().lower()
        playback = self.cue_map.get(event_name)
        if not playback:
            if self.log_unknown_events:
                self.log.info("Unmapped Factorio event: %s", event_name)
            return

        try:
            self.trigger_playback(playback)
            self.log.info("Factorio cue %s -> playback %s", event_name, playback)
        except KeyError:
            self.log.warning("Factorio cue %s mapped to unknown playback %s", event_name, playback)
