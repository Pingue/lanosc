-- LANOSC Bridge mod for Factorio 2.x
-- Writes game events as JSON lines to script-output/lanosc_events.log
-- The LANOSC adapter (games/factorio.py) tails this file.

local LOG_FILE = "lanosc_events.log"

local function write_event(event_name, extra)
    local payload = { event = event_name, tick = game.tick }
    if extra then
        for k, v in pairs(extra) do
            payload[k] = v
        end
    end
    helpers.write_file(LOG_FILE, game.table_to_json(payload) .. "\n", true --[[append]])
end

script.on_event(defines.events.on_player_joined_game, function(e)
    local player = game.get_player(e.player_index)
    write_event("player_join", { player = player and player.name or "unknown" })
end)

script.on_event(defines.events.on_player_left_game, function(e)
    local player = game.get_player(e.player_index)
    write_event("player_leave", { player = player and player.name or "unknown" })
end)

script.on_event(defines.events.on_player_died, function(e)
    local player = game.get_player(e.player_index)
    write_event("player_death", { player = player and player.name or "unknown" })
end)

script.on_event(defines.events.on_rocket_launched, function(e)
    write_event("rocket_launched", { surface = e.rocket.surface.name })
end)

script.on_event(defines.events.on_research_finished, function(e)
    write_event("research_finished", { research = e.research.name })
end)
