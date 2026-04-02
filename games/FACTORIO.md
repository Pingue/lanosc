# Factorio integration

This integration uses a server-side Factorio mod that writes game events to a
file. The LANOSC adapter tails that file and triggers playbacks on new events.

No participant machine changes are required.

## Architecture

1. The `lanosc-bridge` Factorio mod writes JSON event lines to `script-output/lanosc_events.log`.
2. `games.factorio:FactorioAdapter` tails the file and processes new lines.
3. Adapter triggers named LANOSC playbacks.

## Installing the mod

Copy `games/factorio_mod/` to the Factorio mods directory on the server machine,
renaming it to `lanosc-bridge_1.0.0`:

```bash
cp -r games/factorio_mod ~/.factorio/mods/lanosc-bridge_1.0.0
```

Enable the mod in the Factorio mod manager or add it to `mod-list.json`.

The event log is written to:
```
~/.factorio/script-output/lanosc_events.log
```

## LANOSC config

Set `log_path` to the full path of the event log file:

```toml
[[games]]
name    = "factorio"
enabled = true
adapter = "games.factorio:FactorioAdapter"
log_path = "/home/user/.factorio/script-output/lanosc_events.log"
```

See `lanosc.factorio.example.toml` for the full example.

## Event vocabulary

| Event name          | Trigger                           |
|---------------------|-----------------------------------|
| `player_join`       | Player joins the server           |
| `player_leave`      | Player leaves                     |
| `player_death`      | Player dies                       |
| `rocket_launched`   | Rocket launched (win condition)   |
| `research_finished` | Research technology completed     |

## Files in this repo

- `games/factorio.py` — LANOSC adapter
- `games/factorio_mod/` — Factorio server mod source
- `games/FACTORIO.md` — this file
- `lanosc.factorio.example.toml` — ready-to-copy config template
