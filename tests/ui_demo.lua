-- Abre una pestaña de demo: pista con la voz seca (fader en -inf, no suena), Nube Limit con un preset,
-- ventana del FX flotante y reproducción en loop para ver las gráficas. Cerrar con tests/ui_close.lua.
local ROOT = os.getenv("HOME") .. "/Music/NubeLimit/tests"
-- opciones (REAPER no ve las variables de la terminal): tests/out/demo_opts.txt = "preset ganancia"
local o = io.open(ROOT .. "/out/demo_opts.txt"); local OPTS = {}
if o then for w in o:read("a"):gmatch("%S+") do OPTS[#OPTS + 1] = tonumber(w) end o:close() end
local AUDIO = ROOT .. "/signals/music.wav"
reaper.Main_OnCommand(40859, 0)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "Nube Limit demo", true)
reaper.SetMediaTrackInfo_Value(tr, "D_VOL", 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
local src = reaper.PCM_Source_CreateFromFile(AUDIO); reaper.SetMediaItemTake_Source(take, src)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", reaper.GetMediaSourceLength(src))
reaper.UpdateArrange()
local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Limit/nube_limit.jsfx", false, -1)
reaper.TrackFX_SetParam(tr, fx, 11, OPTS[1] or 2)
if OPTS[2] then reaper.TrackFX_SetParam(tr, fx, 0, OPTS[2]) end
reaper.TrackFX_Show(tr, fx, 3)
reaper.GetSet_LoopTimeRange(true, true, 0, reaper.GetMediaSourceLength(src), false)
reaper.SetEditCurPos(0, false, false)
reaper.GetSetRepeat(1)
reaper.OnPlayButton()
local f = io.open(ROOT .. "/out/ui.txt", "w"); f:write("done\n"); f:close()
