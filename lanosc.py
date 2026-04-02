"""LANOSC: generic OSC bridge for LAN party integrations.

This module provides the common runtime that future game-specific adapters can
plug into. The bridge is intentionally generic:

* it can send raw OSC messages over UDP to QLC+
* it can register named playbacks/triggers from a TOML config file
* it can dynamically load one or more game adapter classes
* it exposes a small base class that future per-game modules can inherit from

Example usage:

    python lanosc.py serve --config lanosc.toml
    python lanosc.py trigger intro --config lanosc.toml
    python lanosc.py send /qlcplus/playback/1 255
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import re
import signal
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from pythonosc.udp_client import SimpleUDPClient

try:
	import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
	import tomli as tomllib  # type: ignore[no-redef]


LOGGER = logging.getLogger("lanosc")
DEFAULT_CONFIG_PATH = Path("lanosc.toml")
OscValue = str | int | float | bool | bytes | None

if __name__ == "__main__":
	sys.modules.setdefault("lanosc", sys.modules[__name__])


@dataclass(slots=True)
class Playback:
	"""A named OSC action that can be triggered by integrations."""

	address: str
	arguments: tuple[OscValue, ...] = ()

	@classmethod
	def from_mapping(cls, raw: Mapping[str, Any]) -> "Playback":
		address = raw.get("address")
		if not isinstance(address, str) or not address:
			raise ValueError("Playback entries require a non-empty 'address' value")

		arguments = raw.get("arguments", [])
		if not isinstance(arguments, Sequence) or isinstance(arguments, (str, bytes, bytearray)):
			raise ValueError("Playback 'arguments' must be a list-like value")

		return cls(address=address, arguments=tuple(arguments))


class OscUdpClient:
	"""UDP OSC client backed by python-osc."""

	def __init__(self, host: str, port: int) -> None:
		self.host = host
		self.port = port
		self._client = SimpleUDPClient(host, port)

	def send(self, address: str, *arguments: OscValue) -> None:
		if not address.startswith("/"):
			raise ValueError(f"OSC address must start with '/': {address!r}")

		payload: OscValue | list[OscValue]
		if not arguments:
			payload = []
		elif len(arguments) == 1:
			payload = arguments[0]
		else:
			payload = list(arguments)

		self._client.send_message(address, payload)

	def close(self) -> None:
		return None


class OscBridge:
	"""Central OSC bridge used by all game adapters."""

	def __init__(self, host: str, port: int, playbacks: Mapping[str, Playback] | None = None) -> None:
		self.client = OscUdpClient(host, port)
		self.playbacks: dict[str, Playback] = dict(playbacks or {})

	def register_playback(self, name: str, address: str, *arguments: OscValue) -> None:
		self.playbacks[name] = Playback(address=address, arguments=tuple(arguments))
		LOGGER.debug("Registered playback %s -> %s %s", name, address, arguments)

	def send(self, address: str, *arguments: OscValue) -> None:
		LOGGER.info("OSC -> %s %s", address, arguments)
		self.client.send(address, *arguments)

	def trigger(self, name: str, *override_arguments: OscValue) -> None:
		playback = self.playbacks.get(name)
		if playback is None:
			raise KeyError(f"Unknown playback: {name}")

		arguments = override_arguments or playback.arguments
		self.send(playback.address, *arguments)

	def close(self) -> None:
		self.client.close()


class BaseGameAdapter(ABC):
	"""Base class for future per-game bridge modules.

	Adapters are expected to inherit from this class, use the helper methods to
	trigger named playbacks or raw OSC messages, and implement `run()`.
	"""

	name = "base"

	def __init__(self, bridge: OscBridge, config: Mapping[str, Any] | None = None) -> None:
		self.bridge = bridge
		self.config = dict(config or {})
		self.log = logging.getLogger(f"lanosc.game.{self.name}")

	async def setup(self) -> None:
		"""Optional async setup hook before `run()` starts."""

	async def shutdown(self) -> None:
		"""Optional async cleanup hook when the runtime stops."""

	def send_osc(self, address: str, *arguments: OscValue) -> None:
		self.bridge.send(address, *arguments)

	def trigger_playback(self, name: str, *override_arguments: OscValue) -> None:
		self.bridge.trigger(name, *override_arguments)

	@abstractmethod
	async def run(self, stop_event: asyncio.Event) -> None:
		"""Run the integration until `stop_event` is set."""


@dataclass(slots=True)
class AdapterSpec:
	name: str
	adapter_path: str
	enabled: bool = True
	config: dict[str, Any] = field(default_factory=dict)


def _parse_playbacks(raw_playbacks: Mapping[str, Any] | None) -> dict[str, Playback]:
	if not raw_playbacks:
		return {}

	playbacks: dict[str, Playback] = {}
	for name, raw in raw_playbacks.items():
		if not isinstance(raw, Mapping):
			raise ValueError(f"Playback {name!r} must be a TOML table")
		playbacks[name] = Playback.from_mapping(raw)
	return playbacks


def _parse_adapters(raw_games: Sequence[Any] | None) -> list[AdapterSpec]:
	if not raw_games:
		return []

	adapters: list[AdapterSpec] = []
	for index, raw in enumerate(raw_games, start=1):
		if not isinstance(raw, Mapping):
			raise ValueError(f"games entry #{index} must be a TOML table")

		name = str(raw.get("name") or f"game{index}")
		adapter_path = raw.get("adapter")
		if not isinstance(adapter_path, str) or not adapter_path:
			raise ValueError(f"games entry {name!r} requires an 'adapter' value")

		config = {key: value for key, value in raw.items() if key not in {"name", "adapter", "enabled"}}
		adapters.append(
			AdapterSpec(
				name=name,
				adapter_path=adapter_path,
				enabled=bool(raw.get("enabled", True)),
				config=config,
			)
		)
	return adapters


def load_config(path: Path) -> tuple[OscBridge, list[AdapterSpec]]:
	with path.open("rb") as config_file:
		config = tomllib.load(config_file)

	osc = config.get("osc", {})
	if not isinstance(osc, Mapping):
		raise ValueError("[osc] must be a TOML table")

	host = osc.get("host", "127.0.0.1")
	port = osc.get("port", 7700)
	if not isinstance(host, str):
		raise ValueError("osc.host must be a string")
	if not isinstance(port, int):
		raise ValueError("osc.port must be an integer")

	bridge = OscBridge(host=host, port=port, playbacks=_parse_playbacks(config.get("playbacks")))
	return bridge, _parse_adapters(config.get("games"))


def load_adapter(spec: AdapterSpec, bridge: OscBridge) -> BaseGameAdapter:
	module_name, separator, object_name = spec.adapter_path.partition(":")
	if not separator:
		raise ValueError(
			f"Adapter {spec.adapter_path!r} must use the format 'module.path:ClassName'"
		)

	module = importlib.import_module(module_name)
	adapter_class = getattr(module, object_name)
	adapter = adapter_class(bridge=bridge, config=spec.config)
	if not isinstance(adapter, BaseGameAdapter):
		raise TypeError(f"{spec.adapter_path!r} is not a BaseGameAdapter")
	return adapter


class BridgeRuntime:
	def __init__(self, bridge: OscBridge, specs: Sequence[AdapterSpec]) -> None:
		self.bridge = bridge
		self.specs = [spec for spec in specs if spec.enabled]
		self.stop_event = asyncio.Event()
		self._adapters: list[BaseGameAdapter] = []

	async def run(self) -> None:
		try:
			if not self.specs:
				LOGGER.warning("No enabled game adapters configured; nothing to run")
				return

			self._install_signal_handlers()
			self._adapters = [load_adapter(spec, self.bridge) for spec in self.specs]

			for adapter in self._adapters:
				LOGGER.info("Starting adapter %s", adapter.name)
				await adapter.setup()

			tasks = [asyncio.create_task(adapter.run(self.stop_event), name=adapter.name) for adapter in self._adapters]
			await asyncio.gather(*tasks)
		finally:
			self.stop_event.set()
			for adapter in reversed(self._adapters):
				await adapter.shutdown()
			self.bridge.close()

	def _install_signal_handlers(self) -> None:
		loop = asyncio.get_running_loop()
		for sig in (signal.SIGINT, signal.SIGTERM):
			try:
				loop.add_signal_handler(sig, self.stop_event.set)
			except NotImplementedError:
				LOGGER.debug("Signal handlers not supported in this environment")


_INTEGER_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?(?:\d+\.\d+|\d+\.\d*|\.\d+)$")


def parse_cli_value(raw: str) -> OscValue:
	raw_lower = raw.lower()
	if raw_lower in {"true", "false"}:
		return raw_lower == "true"
	if raw_lower in {"none", "null"}:
		return None
	if _INTEGER_RE.match(raw):
		return int(raw)
	if _FLOAT_RE.match(raw):
		return float(raw)
	return raw


def build_argument_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Bridge game events to QLC+ over OSC")
	parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to TOML config file")
	parser.add_argument(
		"--log-level",
		default="INFO",
		choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
		help="Logging verbosity",
	)

	subparsers = parser.add_subparsers(dest="command", required=False)
	subparsers.add_parser("serve", help="Run the bridge runtime")

	trigger_parser = subparsers.add_parser("trigger", help="Trigger a named playback from config")
	trigger_parser.add_argument("name", help="Playback name")
	trigger_parser.add_argument("arguments", nargs="*", help="Optional OSC arguments overriding the config")

	send_parser = subparsers.add_parser("send", help="Send a raw OSC message")
	send_parser.add_argument("address", help="OSC address, for example /qlcplus/playback/1")
	send_parser.add_argument("arguments", nargs="*", help="OSC arguments")

	return parser


async def async_main() -> int:
	parser = build_argument_parser()
	args = parser.parse_args()

	logging.basicConfig(
		level=getattr(logging, args.log_level),
		format="%(asctime)s %(levelname)s %(name)s: %(message)s",
	)

	command = args.command or "serve"
	bridge, adapters = load_config(args.config)

	if command == "send":
		bridge.send(args.address, *(parse_cli_value(value) for value in args.arguments))
		bridge.close()
		return 0

	if command == "trigger":
		bridge.trigger(args.name, *(parse_cli_value(value) for value in args.arguments))
		bridge.close()
		return 0

	runtime = BridgeRuntime(bridge=bridge, specs=adapters)
	await runtime.run()
	return 0


def main() -> int:
	try:
		return asyncio.run(async_main())
	except FileNotFoundError as error:
		LOGGER.error("Config file not found: %s", error)
		return 1
	except (TypeError, ValueError, KeyError) as error:
		LOGGER.error("Configuration/runtime error: %s", error)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
