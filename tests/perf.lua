-- CPU en el peor caso: 10 instancias con todo encendido, render de 60 s del premaster de Nube baja.
local OUT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/out"
local AUDIO = os.getenv("HOME") .. "/Music/ClaudeBeats/Mezcla/nube_baja_mezcla_premaster_X20.wav"
os.execute('mkdir -p "' .. OUT .. '"')
local f = io.open(OUT .. "/perf.txt", "w")
reaper.Main_OnCommand(40859, 0)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemTake_Source(take, reaper.PCM_Source_CreateFromFile(AUDIO))
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", 60)
local function render(name, nfx)
  while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
  for k = 1, nfx do
    local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Limit/nube_limit.jsfx", false, -1)
    for p, v in pairs({[0] = 12, [3] = 10, [4] = 2, [5] = 1, [7] = 1, [8] = 50}) do reaper.TrackFX_SetParam(tr, fx, p, v) end
  end
  os.remove(OUT .. "/" .. name .. ".wav")
  reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true); reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
  reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true); reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
  local t0 = reaper.time_precise(); reaper.Main_OnCommand(42230, 0); return reaper.time_precise() - t0
end
local t_empty = render("perf_vacio", 0)
local t_full = render("perf_todo", 10)
f:write(string.format("sin plugin %.2f s | 10 instancias en el peor caso %.2f s (60 s de audio) -> %.2f %% de un nucleo por instancia\n",
  t_empty, t_full, (t_full - t_empty) / 60 / 10 * 100))
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_perf.rpp", 0); reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_perf.rpp"); reaper.Main_OnCommand(40860, 0)
f:write("done\n"); f:close()
