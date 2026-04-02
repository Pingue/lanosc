# CS2 integration

This integration uses CS2 Game State Integration (GSI), which sends HTTP POST
requests from the game client to a local endpoint. For a tournament, the GSI
config is placed on a GOTV/observer machine run by the organizer.

No participant machine changes are required when running from a dedicated observer.

## Architecture

1. CS2 (running on the organizer's GOTV/observer machine) sends HTTP POST with game state.
2. `games.cs2:Cs2GsiAdapter` receives state updates and fires on transitions.
3. Adapter triggers named LANOSC playbacks.

## Setup

1. Copy `games/cs2_gsi/gamestate_integration_lanosc.cfg` to the CS2 `cfg/` directory on the observer machine:

   - Steam: `Steam/steamapps/common/Counter-Strike Global Offensive/game/csgo/cfg/`
   - Adjust the `uri` if LANOSC is not on the same machine.

2. Add the CS2 adapter and playbacks to `lanosc.toml` (use `lanosc.cs2.example.toml`).

3. Start LANOSC before launching CS2.

## LANOSC config example

```toml
[playbacks]
cs2_round_start  = { address = "/qlcplus/playback/40", arguments = [255] }
cs2_round_end    = { address = "/qlcplus/playback/41", arguments = [255] }
cs2_bomb_planted = { address = "/qlcplus/playback/42", arguments = [255] }
cs2_bomb_defused = { address = "/qlcplus/playback/43", arguments = [255] }
cs2_bomb_exploded = { address = "/qlcplus/playback/44", arguments = [255] }
cs2_match_end    = { address = "/qlcplus/playback/45", arguments = [255] }

[[games]]
name    = "cs2"
enabled = true
adapter = "games.cs2:Cs2GsiAdapter"
listen_host = "127.0.0.1"
listen_port = 10053

[games.cue_map]
round_started = "cs2_round_start"
round_ended   = "cs2_round_end"
bomb_planted  = "cs2_bomb_planted"
bomb_defused  = "cs2_bomb_defused"
bomb_exploded = "cs2_bomb_exploded"
match_ended   = "cs2_match_end"
```

## Event vocabulary

Events are derived from CS2 GSI state transitions:

| Event name     | Transition                                       |
|----------------|--------------------------------------------------|
| `round_started`| round.phase: freezetime → live                   |
| `round_ended`  | round.phase: live → over                         |
| `bomb_planted` | round.bomb becomes "planted"                     |
| `bomb_defused` | round.bomb becomes "defused"                     |
| `bomb_exploded`| round.bomb becomes "exploded"                    |
| `match_ended`  | map.phase becomes "gameover"                     |

## Files in this repo

- `games/cs2.py` — LANOSC CS2 GSI adapter
- `games/cs2_gsi/gamestate_integration_lanosc.cfg` — GSI config to deploy on observer machine
- `games/CS2.md` — this file
- `lanosc.cs2.example.toml` — ready-to-copy config template
