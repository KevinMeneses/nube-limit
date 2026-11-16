"""Señales de prueba (48 kHz, float32)."""
import numpy as np, soundfile as sf, pathlib
from scipy import signal as sg
D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
def a(db): return 10 ** (db / 20)
def save(name, *ch): sf.write(D / name, np.stack(ch, 1).astype(np.float32), SR, subtype="FLOAT")
n = SR * 2; t = np.arange(n) / SR
s = lambda f, db, tt=t, ph=0: a(db) * np.sin(2 * np.pi * f * tt + ph)
save("s1k_m6.wav", s(1000, -6), s(1000, -6))
save("s1k_m20.wav", s(1000, -20), s(1000, -20))
save("s100_m6.wav", s(100, -6), s(100, -6))
save("lr.wav", s(1000, -6), s(1000, -30))
# pico entre muestras: 12 kHz (fs/4) con fase de 45°: las muestras quedan 3 dB bajo el pico real
save("isp.wav", s(12000, -6, ph=np.pi / 4), s(12000, -6, ph=np.pi / 4))
# escalón: -30 dBFS 0-1 s, -6 dBFS 1-2 s, -30 dBFS 2-3 s
t3 = np.arange(SR * 3) / SR
lv = np.where((t3 >= 1) & (t3 < 2), a(-6), a(-30)); st = lv * np.sin(2 * np.pi * 1000 * t3); save("step.wav", st, st)
# ráfaga desde 1.0 s empezando en el pico
b = np.zeros(n); i0 = SR; b[i0:] = a(-6) * np.cos(2 * np.pi * 1000 * (t[i0:] - 1.0)); save("burst.wav", b, b)
# batería sintética: kick (55 Hz con click) y snare (ruido) con picos distintos, 4 s
rng = np.random.default_rng(3); t4 = np.arange(SR * 4) / SR; dr = np.zeros(len(t4))
for k in range(16):
    i = int(k * 0.25 * SR); m = len(t4) - i; tt = np.arange(m) / SR; g = a(-rng.uniform(0, 8))
    if k % 2 == 0: dr[i:] += g * np.sin(2 * np.pi * (55 + 150 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 8)
    else: dr[i:] += g * 0.8 * rng.standard_normal(m) * np.exp(-tt * 25)
dr *= a(-3) / np.abs(dr).max(); save("drums.wav", dr, np.roll(dr, 7) * 0.9)
# música real: 20 s del premaster de Nube baja
mp = pathlib.Path.home() / "Music/ClaudeBeats/Mezcla/nube_baja_mezcla_premaster_X20.wav"
if mp.exists():
    x, sr = sf.read(mp, start=int(40 * 48000), frames=20 * 48000)
    if sr == SR: sf.write(D / "music.wav", x.astype(np.float32), SR, subtype="FLOAT")
print("ok", sorted(p.name for p in D.iterdir()))
tl = np.arange(SR * 12) / SR; save("s1k_m20_12s.wav", s(1000, -20, tl), s(1000, -20, tl))
