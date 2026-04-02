# Minecraft integration

This integration uses a server-side Paper plugin on the organizer-controlled Minecraft server.

## Architecture

1. The Paper plugin (`LanoscBridge`) fires on server events.
2. It sends UDP JSON datagrams to LANOSC.
3. `games.minecraft:MinecraftAdapter` receives them and triggers named playbacks.

No client/player machine changes are required.

## Building the plugin

Requires Java 21 and Gradle.

```bash
cd games/minecraft_plugin
./gradlew jar
```

The built jar will be in `build/libs/`. Copy it to your Paper server's `plugins/` directory.

## Plugin config

After first run, `plugins/LanoscBridge/config.yml` is created. Edit to point at LANOSC:

```yaml
lanosc:
  host: 127.0.0.1   # host running lanosc.py
  port: 10052
```

## Triggering challenge events

The plugin emits `player_join`, `player_leave`, `player_death`, and `advancement_unlock` automatically.

For challenge lifecycle events (`challenge_start`, `challenge_win`), send them manually via RCON or a server command. You can fire these from lanosc.py directly:

```bash
python lanosc.py trigger mc_challenge_start --config lanosc.toml
python lanosc.py trigger mc_challenge_win --config lanosc.toml
```

## LANOSC config example

```toml
[playbacks]
mc_player_join    = { address = "/qlcplus/playback/30", arguments = [255] }
mc_player_leave   = { address = "/qlcplus/playback/31", arguments = [255] }
mc_player_death   = { address = "/qlcplus/playback/32", arguments = [255] }
mc_advancement    = { address = "/qlcplus/playback/33", arguments = [255] }
mc_challenge_start = { address = "/qlcplus/playback/34", arguments = [255] }
mc_challenge_win  = { address = "/qlcplus/playback/35", arguments = [255] }

[[games]]
name = "minecraft"
enabled = true
adapter = "games.minecraft:MinecraftAdapter"
listen_host = "127.0.0.1"
listen_port = 10052

[games.cue_map]
player_join       = "mc_player_join"
player_leave      = "mc_player_leave"
player_death      = "mc_player_death"
advancement_unlock = "mc_advancement"
challenge_start   = "mc_challenge_start"
challenge_win     = "mc_challenge_win"
```

## Event vocabulary

| Event name          | Trigger                        |
|---------------------|-------------------------------|
| `player_join`       | Player connects to server     |
| `player_leave`      | Player disconnects            |
| `player_death`      | Player dies                   |
| `advancement_unlock`| Player unlocks an advancement |
| `challenge_start`   | Manual trigger via lanosc CLI |
| `challenge_win`     | Manual trigger via lanosc CLI |

## Files in this repo

- `games/minecraft.py` — LANOSC adapter
- `games/minecraft_plugin/` — Paper plugin source
- `games/MINECRAFT.md` — this file
- `lanosc.minecraft.example.toml` — ready-to-copy config template
