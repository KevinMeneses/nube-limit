-- Carga Nube Limit en una pestaña nueva, renderiza cada caso y cierra la pestaña.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local OUT = ROOT .. "/out"
local FX = "JS:Nube Limit/nube_limit.jsfx"
local PRESET = 12
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for _, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

-- slider N (1..14) = parámetro N-1. Los sliders con forma :log=mid van normalizados 0..1
local LOGP = {[3] = {1, 1000, 100}}
local function to_norm(s, v)
  local mn, mx, mid = table.unpack(LOGP[s])
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end
local function with(a, b) local r = {} for k, v in pairs(a) do r[k] = v end for k, v in pairs(b or {}) do r[k] = v end return r end
-- base: Transparente, techo -6, release 100 sin auto, lookahead 3, pico real
local B = {[1] = 10, [2] = -6, [3] = 100, [4] = 3, [5] = 0, [6] = 0, [8] = 1}

local CASES = {
  {"bajo_techo",   "s1k_m20.wav", with(B, {[1] = 0})},
  {"estatico",     "s1k_m6.wav",  B},
  {"estatico_c1",  "s1k_m6.wav",  with(B, {[2] = -1})},
  {"unity",        "s1k_m20.wav", with(B, {[1] = 10, [2] = 0, [10] = 1})},
  {"delta_bajo",   "s1k_m20.wav", with(B, {[1] = 0, [11] = 1})},
  {"delta",        "s1k_m6.wav",  with(B, {[1] = 4, [11] = 1})},
  {"link100",      "lr.wav",      B},
  {"link0",        "lr.wav",      with(B, {[7] = 0})},
  {"isp_tp",       "isp.wav",     with(B, {[1] = 6, [2] = -1})},
  {"isp_sp",       "isp.wav",     with(B, {[1] = 6, [2] = -1, [8] = 0})},
  {"release",      "step.wav",    B},
  {"burst_la0",    "burst.wav",   with(B, {[4] = 0})},
  {"burst_la3",    "burst.wav",   B},
  {"burst_la8",    "burst.wav",   with(B, {[4] = 8})},
  {"s100_auto",    "s100_m6.wav", with(B, {[6] = 1})},
  {"s100_fijo",    "s100_m6.wav", with(B, {[3] = 10})},
  {"clip0",        "s1k_m6.wav",  with(B, {[3] = 500, [2] = 0, [1] = 3})},
  {"clip100",      "s1k_m6.wav",  with(B, {[3] = 500, [2] = 0, [1] = 3, [9] = 100})},
  {"lufs_sine",    "s1k_m20_12s.wav", with(B, {[1] = 0, [2] = 0})},
  {"music",        "music.wav",   with(B, {[1] = 10, [2] = -1, [6] = 1})},
}
for st = 0, 4 do CASES[#CASES + 1] = {"drums_st" .. st, "drums.wav", with(B, {[1] = 12, [2] = -1, [5] = st, [6] = 1})} end
CASES[#CASES + 1] = {"drums_sp", "drums.wav", with(B, {[1] = 12, [2] = -1, [8] = 0})}
CASES[#CASES + 1] = {"drums_la0", "drums.wav", with(B, {[1] = 12, [2] = -1, [4] = 0})}
for p = 1, 18 do CASES[#CASES + 1] = {"preset" .. p, "music.wav", {[PRESET] = p}} end

reaper.Main_OnCommand(40859, 0) -- nueva pestaña
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
local only = os.getenv("NUBE_CASE")

for _, c in ipairs(CASES) do
  local name, src, params = c[1], c[2], c[3]
  if not only or name:find(only) then
    reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", c[4] or 2)
    local s = reaper.PCM_Source_CreateFromFile(ROOT .. "/signals/" .. src)
    reaper.SetMediaItemTake_Source(take, s)
    reaper.SetMediaItemTakeInfo_Value(take, "D_VOL", 10 ^ ((c[5] or 0) / 20))
    reaper.SetMediaItemInfo_Value(item, "D_LENGTH", math.min(reaper.GetMediaSourceLength(s), 30))
    reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", 0)
    reaper.UpdateItemInProject(item)
    while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
    local fx = reaper.TrackFX_AddByName(tr, FX, false, -1)
    if fx < 0 then log("ERROR no cargó el FX") break end
    if params[PRESET] then reaper.TrackFX_SetParam(tr, fx, PRESET - 1, params[PRESET]) end
    for s_, v in pairs(params) do
      if s_ ~= PRESET then
        if LOGP[s_] then reaper.TrackFX_SetParamNormalized(tr, fx, s_ - 1, to_norm(s_, v))
        else reaper.TrackFX_SetParam(tr, fx, s_ - 1, v) end
      end
    end
    local file = OUT .. "/" .. name .. ".wav"
    os.remove(file)
    reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
    reaper.Main_OnCommand(42230, 0)
    local vals = {}
    for k = 1, 11 do local _, v = reaper.TrackFX_GetFormattedParamValue(tr, fx, k - 1, ""); vals[#vals + 1] = v end
    vals[#vals + 1] = string.format("LUFS_I=%.3f TP=%.3f", reaper.TrackFX_GetParam(tr, fx, 12), reaper.TrackFX_GetParam(tr, fx, 13))
    log("caso", name, table.concat(vals, " | "))
  end
end
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_test.rpp", 0)
reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_test.rpp")
reaper.Main_OnCommand(40860, 0) -- cerrar pestaña
log("done")
logf:close()
