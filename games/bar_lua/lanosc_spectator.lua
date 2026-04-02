function widget:GetInfo()
  return {
    name = "LANOSC Spectator Bridge",
    desc = "Emit BAR global spectator cues over UDP JSON",
    author = "lanosc",
    layer = 0,
    enabled = true,
  }
end

local socket = require("socket")

local udp = nil
local host = "127.0.0.1"
local port = 10051

local commanderUnitDefIDs = {}
local nukeWeaponDefIDs = {}
local superWeaponDefIDs = {}
local knownTeamT3 = {}

local function lower(s)
  if type(s) ~= "string" then return "" end
  return string.lower(s)
end

local function json_escape(s)
  if type(s) ~= "string" then s = tostring(s) end
  return (s:gsub("\\", "\\\\"):gsub('"', '\\"'))
end

local function json_kv(key, value)
  local t = type(value)
  if t == "number" then
    return '"' .. json_escape(key) .. '":' .. tostring(value)
  elseif t == "boolean" then
    return '"' .. json_escape(key) .. '":' .. (value and "true" or "false")
  elseif t == "string" then
    return '"' .. json_escape(key) .. '":"' .. json_escape(value) .. '"'
  end
  return nil
end

local function encode_payload(eventName, extra)
  local spectating, spectatingFullView = false, false
  if Spring.GetSpectatingState then
    spectating, spectatingFullView = Spring.GetSpectatingState()
  end

  local parts = {
    json_kv("event", eventName),
    json_kv("spectator", spectating),
    json_kv("spectator_full_view", spectatingFullView),
    json_kv("ts", Spring.GetGameSeconds and Spring.GetGameSeconds() or 0),
  }

  if extra then
    for k, v in pairs(extra) do
      local piece = json_kv(k, v)
      if piece then table.insert(parts, piece) end
    end
  end

  return "{" .. table.concat(parts, ",") .. "}"
end

local function emit(eventName, extra)
  if not udp then return end
  local payload = encode_payload(eventName, extra)
  udp:sendto(payload, host, port)
end

local function prepareDefinitionSets()
  if UnitDefs then
    for udid, ud in pairs(UnitDefs) do
      local uname = lower(ud.name or "")
      local uhuman = lower(ud.humanName or "")
      local isCommander = false

      if ud.customParams and (ud.customParams.iscommander == "1" or ud.customParams.iscommander == 1) then
        isCommander = true
      end
      if not isCommander and (string.find(uname, "com") or string.find(uhuman, "commander")) then
        isCommander = true
      end

      if isCommander then
        commanderUnitDefIDs[udid] = true
      end
    end
  end

  if WeaponDefs then
    for wdid, wd in pairs(WeaponDefs) do
      local n = lower(wd.name or "")
      local d = lower(wd.description or "")
      local text = n .. " " .. d

      if string.find(text, "nuke") or string.find(text, "nuclear") then
        nukeWeaponDefIDs[wdid] = true
      end
      if string.find(text, "bertha") or string.find(text, "big bertha") or string.find(text, "disco") or string.find(text, "zenith") then
        superWeaponDefIDs[wdid] = true
      end
    end
  end
end

local function isT3Unit(unitDefID)
  local ud = UnitDefs and UnitDefs[unitDefID]
  if not ud then return false end

  if ud.customParams then
    local tech = ud.customParams.techlevel or ud.customParams.tech
    if tostring(tech) == "3" then
      return true
    end
  end

  local uname = lower(ud.name or "")
  return string.find(uname, "t3") ~= nil
end

function widget:Initialize()
  udp = socket.udp()
  udp:settimeout(0)
  prepareDefinitionSets()

  if Spring.Echo then
    Spring.Echo("[LANOSC] Spectator bridge enabled -> " .. host .. ":" .. tostring(port))
  end
end

function widget:Shutdown()
  if udp then
    udp:close()
    udp = nil
  end
end

function widget:GameStart()
  emit("match_started")
end

function widget:GameOver(winningAllyTeams)
  local winners = ""
  if type(winningAllyTeams) == "table" then
    local chunks = {}
    for i, ally in ipairs(winningAllyTeams) do
      chunks[i] = tostring(ally)
    end
    winners = table.concat(chunks, ",")
  end
  emit("match_ended", { winning_allyteams = winners })
end

function widget:UnitCreated(unitID, unitDefID, unitTeam)
  if isT3Unit(unitDefID) and not knownTeamT3[unitTeam] then
    knownTeamT3[unitTeam] = true
    emit("t3_unlocked", { team = unitTeam, unit_def_id = unitDefID })
  end
end

function widget:UnitDestroyed(unitID, unitDefID, unitTeam, attackerID, attackerDefID, attackerTeam)
  if commanderUnitDefIDs[unitDefID] then
    emit("commander_died", {
      team = unitTeam,
      attacker_team = attackerTeam or -1,
      unit_def_id = unitDefID,
    })
  end
end

function widget:ProjectileCreated(proID, proOwnerID, weaponDefID)
  if nukeWeaponDefIDs[weaponDefID] then
    emit("nuke_launched", { weapon_def_id = weaponDefID, owner_id = proOwnerID or -1 })
  elseif superWeaponDefIDs[weaponDefID] then
    emit("superweapon_fired", { weapon_def_id = weaponDefID, owner_id = proOwnerID or -1 })
  end
end

function widget:Explosion(weaponDefID, px, py, pz)
  if nukeWeaponDefIDs[weaponDefID] then
    emit("nuke_detonated", {
      weapon_def_id = weaponDefID,
      x = math.floor(px or 0),
      y = math.floor(py or 0),
      z = math.floor(pz or 0),
    })
  end
end
