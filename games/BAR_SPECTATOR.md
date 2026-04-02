# Beyond All Reason (Spectator) integration

This integration is designed for **spectator-only operation**.

## Architecture

1. BAR spectator client runs a Lua widget.
2. Widget emits UDP JSON events to LANOSC (`games.bar:BarSpectatorAdapter`).
3. Adapter maps events to named playbacks in `lanosc.toml`.

No custom BAR server is required for this workflow.

## Quick start (client side)

1. Enable BAR adapter/playbacks in `lanosc.toml` (use the config block below).
  - Fast path: copy `lanosc.bar.example.toml` to `lanosc.toml` and adjust playback addresses.
2. Install the BAR widget from this repo:

```bash
cd /home/michael/git/lanosc
bash games/install_bar_widget.sh
```

3. Start LANOSC:

```bash
cd /home/michael/git/lanosc
python lanosc.py serve --config lanosc.toml
```

4. Start BAR as spectator and enable widget `LANOSC Spectator Bridge` in the BAR widget list.
5. Watch LANOSC logs for lines like `BAR cue commander_died -> playback ...`.

## LANOSC config example

```toml
[playbacks]
bar_match_start = { address = "/qlcplus/playback/20", arguments = [255] }
bar_match_end = { address = "/qlcplus/playback/21", arguments = [255] }
bar_commander_down = { address = "/qlcplus/playback/22", arguments = [255] }
bar_nuke_launch = { address = "/qlcplus/playback/23", arguments = [255] }
bar_nuke_detonation = { address = "/qlcplus/playback/24", arguments = [255] }
bar_superweapon = { address = "/qlcplus/playback/25", arguments = [255] }
bar_tech3_unlock = { address = "/qlcplus/playback/26", arguments = [255] }

[[games]]
name = "bar"
enabled = true
adapter = "games.bar:BarSpectatorAdapter"
listen_host = "127.0.0.1"
listen_port = 10051
require_spectator = true

[games.cue_map]
match_started = "bar_match_start"
match_ended = "bar_match_end"
commander_died = "bar_commander_down"
nuke_launched = "bar_nuke_launch"
nuke_detonated = "bar_nuke_detonation"
superweapon_fired = "bar_superweapon"
t3_unlocked = "bar_tech3_unlock"

[games.cooldowns]
match_started = 5.0
match_ended = 5.0
commander_died = 1.0
nuke_launched = 0.25
nuke_detonated = 0.25
superweapon_fired = 0.25
t3_unlocked = 0.5
```

## Files in this repo

- `games/bar.py` – LANOSC BAR spectator adapter (UDP JSON listener)
- `games/bar_lua/lanosc_spectator.lua` – BAR widget that emits global cues
- `games/install_bar_widget.sh` – install helper for common BAR/Spring paths
- `lanosc.bar.example.toml` – BAR-only LANOSC config template

## Suggested global cue vocabulary

- `match_started`
- `match_ended`
- `commander_died`
- `nuke_launched`
- `nuke_detonated`
- `superweapon_fired`
- `t3_unlocked`

You can emit additional event names and map them via `cue_map`.

## Expected UDP payload

JSON object with at least:

```json
{
  "event": "commander_died",
  "spectator": true,
  "team": 3,
  "ts": 1710000000.1
}
```

Only `event` is required. If `require_spectator = true`, events carrying `"spectator": false` are ignored.

Widget source in this repo: `games/bar_lua/lanosc_spectator.lua`