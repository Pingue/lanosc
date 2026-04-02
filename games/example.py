"""Example LANOSC adapter.

This file is only a stub showing how future game-specific integrations should be
structured.
"""

from __future__ import annotations

import asyncio

from lanosc import BaseGameAdapter


class ExampleGameAdapter(BaseGameAdapter):
    name = "example"

    async def run(self, stop_event: asyncio.Event) -> None:
        self.log.info("Example adapter running; waiting for stop signal")
        await stop_event.wait()
