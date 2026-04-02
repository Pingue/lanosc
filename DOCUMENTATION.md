# LANOSC

LANOSC is a generic OSC bridge for LAN and tournament game events.

It is designed to sit between game-specific event sources and OSC consumers such as QLC+.

## What it does

- loads named playbacks from TOML
- sends OSC over UDP
- runs one or more game adapters
- keeps game-specific logic separate from the generic bridge

## Project goals

- one reusable OSC bridge core
- game integrations as separate adapters
- tournament-safe integrations only
- organizer-controlled infrastructure preferred

See [INTEGRATIONS.md](INTEGRATIONS.md) for the integration policy.

## Current integrations

- `dummy` — local test adapter for validating the bridge
- `bar` — Beyond All Reason spectator integration (spectator client)
- `minecraft` — Minecraft Paper plugin integration (server-side)
- `cs2` — CS2 Game State Integration adapter (GOTV/observer)
- `factorio` — Factorio server mod integration (server-side log)

Deferred integrations should not stay in the tree unless they satisfy the policy in [INTEGRATIONS.md](INTEGRATIONS.md).

## Deferred integrations

The following games from the current event schedule were assessed and do not
satisfy the integration policy. They require participant-side software or have
no organizer-controlled event source available:

- **VALORANT** — game events only accessible from participant client
- **Rocket League** — no organizer-controlled server event API
- **Overwatch** — no server-side event API
- **Hytale** — game not yet released
- **Mario Kart 64 / GoldenEye 64** — emulators, no server events
- **Golf with Friends / GeoGuessr** — no server event API

## Requirements

- Python 3.11+
- dependencies from [requirements.txt](requirements.txt)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Basic usage

Run the bridge runtime:

```bash
python lanosc.py serve --config lanosc.toml
```

Trigger a configured playback manually:

```bash
python lanosc.py trigger dummy_a --config lanosc.toml
```

Send a raw OSC message:

```bash
python lanosc.py send /qlcplus/playback/1 255 --config lanosc.toml
```

## Configuration

Configuration is TOML.

Main sections:

- `[osc]` — destination host/port
- `[playbacks]` — named OSC messages
- `[[games]]` — enabled adapters and per-adapter settings

Start from [lanosc.example.toml](lanosc.example.toml).

## Example adapters

### Dummy

The dummy adapter cycles through configured playback names and is useful for end-to-end OSC testing.

Relevant files:

- [games/dummy.py](games/dummy.py)
- [lanosc.toml](lanosc.toml)
- [qlcplus/README.md](qlcplus/README.md)

### Beyond All Reason

BAR is implemented from a spectator point of view.

Relevant files:

- [games/bar.py](games/bar.py)
- [games/BAR_SPECTATOR.md](games/BAR_SPECTATOR.md)
- [games/bar_lua/lanosc_spectator.lua](games/bar_lua/lanosc_spectator.lua)
- [games/install_bar_widget.sh](games/install_bar_widget.sh)
- [lanosc.bar.example.toml](lanosc.bar.example.toml)

### Minecraft

Server-side Paper plugin sends UDP JSON events to LANOSC.

Relevant files:

- [games/minecraft.py](games/minecraft.py)
- [games/MINECRAFT.md](games/MINECRAFT.md)
- [games/minecraft_plugin/](games/minecraft_plugin/)
- [lanosc.minecraft.example.toml](lanosc.minecraft.example.toml)

### CS2

CS2 Game State Integration (GSI) sends HTTP POST requests from a GOTV/observer machine.

Relevant files:

- [games/cs2.py](games/cs2.py)
- [games/CS2.md](games/CS2.md)
- [games/cs2_gsi/gamestate_integration_lanosc.cfg](games/cs2_gsi/gamestate_integration_lanosc.cfg)
- [lanosc.cs2.example.toml](lanosc.cs2.example.toml)

### Factorio

Server-side Factorio mod writes event log; adapter tails the file.

Relevant files:

- [games/factorio.py](games/factorio.py)
- [games/FACTORIO.md](games/FACTORIO.md)
- [games/factorio_mod/](games/factorio_mod/)
- [lanosc.factorio.example.toml](lanosc.factorio.example.toml)

## QLC+

This repo includes a small QLC+ dummy workspace and OSC input profile under [qlcplus](qlcplus).

See [qlcplus/README.md](qlcplus/README.md).

## Architecture overview

- [lanosc.py](lanosc.py) contains the generic bridge runtime
- [games](games) contains game-specific adapters and related assets
- adapters subclass `BaseGameAdapter`
- adapters trigger named playbacks or send raw OSC messages through the shared bridge

## Adding a new game

1. Confirm it meets the policy in [INTEGRATIONS.md](INTEGRATIONS.md).
2. Add a LANOSC adapter under [games](games).
3. Add any required server or spectator plugin source to this repo.
4. Add a `<game>.md` setup document.
5. Add a `lanosc.<game>.example.toml` template.

## License

See [LICENSE](LICENSE).