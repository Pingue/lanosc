# Integration policy

This project exists to bridge tournament-safe game events into OSC/QLC+.

## Core rule

Integrations must work from infrastructure controlled by the organizer.

That means one of these is required:

- server-side logs
- server-side APIs
- server-side plugins/mods
- organizer-controlled observer/spectator clients

Integrations that require software on participant/player machines should not be included.

## Client plugins are allowed only when spectator-safe

Client-side integrations are acceptable only if they can run from a true non-participant point of view, such as:

- a built-in spectator mode
- an observer client run by tournament staff
- a dedicated replay/observer feed controlled by the organizer

If a game only exposes useful events from an active participant client, that integration should be deferred.

## Plugin source belongs in this repo

When a game needs a server plugin or an observer/spectator client plugin, that plugin should live in this repository alongside the LANOSC adapter.

Examples:

- Python LANOSC adapter in [games](games)
- server plugin source in a game-specific subdirectory
- spectator/observer plugin source in a game-specific subdirectory
- setup and deployment notes in a matching markdown document

## Suggested layout

- `games/<game>.py` — LANOSC adapter
- `games/<GAME>.md` — integration notes
- `games/<game>_plugin/` or similar — server/observer plugin source
- `lanosc.<game>.example.toml` — ready-to-copy config template

## Acceptance checklist

Before adding a new game, confirm:

1. Events can be sourced from the server or from organizer-controlled spectator infrastructure.
2. No participant machine changes are required.
3. Event semantics are stable enough to map to named playbacks.
4. Any required plugin source is committed in this repo.
5. A setup document and example config are included.

## Current status

- BAR is a valid target because it can be driven from a spectator client.
- Dummy adapter exists for local bridge testing.
- Games requiring participant-side mods should remain out of tree until a server-safe or spectator-safe path is available.