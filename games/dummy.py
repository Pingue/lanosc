"""Dummy LANOSC adapter for end-to-end testing."""

from __future__ import annotations

import asyncio
from itertools import cycle

from lanosc import BaseGameAdapter


class DummyGameAdapter(BaseGameAdapter):
	name = "dummy"

	def __init__(self, bridge, config=None):
		super().__init__(bridge=bridge, config=config)
		self.interval = float(self.config.get("interval", 2.0))
		if self.interval <= 0:
			raise ValueError("dummy.interval must be > 0")

		sequence = self.config.get("sequence", ["dummy_a", "dummy_b"])
		if not isinstance(sequence, list) or any(not isinstance(item, str) for item in sequence):
			raise ValueError("dummy.sequence must be a list of playback names")
		self.sequence = sequence
		self.startup_playback = self.config.get("startup_playback")
		self.shutdown_playback = self.config.get("shutdown_playback")

	async def setup(self) -> None:
		if isinstance(self.startup_playback, str) and self.startup_playback:
			self.trigger_playback(self.startup_playback)

	async def run(self, stop_event: asyncio.Event) -> None:
		if not self.sequence:
			self.log.warning("Dummy adapter has empty sequence; waiting for stop")
			await stop_event.wait()
			return

		self.log.info("Dummy adapter started with interval=%ss sequence=%s", self.interval, self.sequence)
		sequence_iter = cycle(self.sequence)

		while not stop_event.is_set():
			playback_name = next(sequence_iter)
			try:
				self.trigger_playback(playback_name)
			except KeyError:
				self.log.warning("Playback %s is not configured", playback_name)

			try:
				await asyncio.wait_for(stop_event.wait(), timeout=self.interval)
			except TimeoutError:
				continue

	async def shutdown(self) -> None:
		if isinstance(self.shutdown_playback, str) and self.shutdown_playback:
			self.trigger_playback(self.shutdown_playback)