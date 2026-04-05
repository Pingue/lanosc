# LANOSC

LANOSC is a lightweight bridge that turns game events into OSC messages for show-control tools such as QLC+.

The goal is simple: let tournament or LAN infrastructure trigger lighting, effects, or other OSC-driven automation from supported games.

## What LANOSC is for

- bridging game events to OSC
- mapping those events to named playbacks
- keeping game-specific integrations separate from the core bridge
- supporting organizer-controlled deployments rather than participant-side mods

## Project status

LANOSC is early-stage, but the core bridge is in place and the repository already includes:

- a generic Python OSC bridge runtime
- a dummy adapter for local end-to-end testing
- a Beyond All Reason spectator-side integration scaffold
- a small QLC+ dummy workspace and OSC input profile

## Design principles

This project is built for tournament and event operators.

That means integrations should prefer:

- server-side logs, APIs, or plugins
- organizer-controlled observer or spectator clients
- code and plugin source that lives in this repository

Integrations that depend on software running on participant machines are intentionally out of scope.

## Quick start

Create an environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the bridge:

```bash
python lanosc.py serve --config lanosc.toml
```

Trigger a playback manually:

```bash
python lanosc.py trigger dummy_a --config lanosc.toml
```

Send a raw OSC message:

```bash
python lanosc.py send /qlcplus/playback/1 255 --config lanosc.toml
```

## Repository layout

- [lanosc.py](lanosc.py) — generic OSC bridge runtime
- [games](games) — game-specific adapters and related assets
- [qlcplus](qlcplus) — QLC+ test assets
- [lanosc.example.toml](lanosc.example.toml) — base example configuration
- [lanosc.bar.example.toml](lanosc.bar.example.toml) — BAR example configuration

## Current integrations

- `dummy` — local bridge testing
- `bar` — Beyond All Reason, from a spectator point of view

## Documentation

For setup details, integration policy, and development notes, see:

- [DOCUMENTATION.md](DOCUMENTATION.md)
- [INTEGRATIONS.md](INTEGRATIONS.md)
- [games/BAR_SPECTATOR.md](games/BAR_SPECTATOR.md)
- [qlcplus/README.md](qlcplus/README.md)

## Disclaimer

This project is entirely AI vibe coded, as it is unfeasible to learn the language for writing each game's plugin. I am open to having human review from people with the relevant expertise.

## License

See [LICENSE](LICENSE).
