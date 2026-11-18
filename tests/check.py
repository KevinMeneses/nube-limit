"""Compara los renders de tests/out con lo que dice la teoría. Sale con código 1 si algo falla."""
import numpy as np, soundfile as sf, pathlib, sys, re
from scipy import signal as sg
D = pathlib.Path(__file__).parent / "out"; S = pathlib.Path(__file__).parent / "signals"; SR = 48000
def a(db): return 10 ** (db / 20)
def db(x): return 20 * np.log10(np.abs(x) + 1e-15)
def load(name):
    x, sr = sf.read(D / f"{name}.wav"); assert sr == SR; return x
def tone(name, f, t0=1.0, t1=1.9, ch=0):
    x = load(name)[:, ch]; seg = x[int(t0 * SR):int(t1 * SR)]; tt = np.arange(int(t0 * SR), int(t1 * SR)) / SR
    M = np.stack([np.sin(2 * np.pi * f * tt), np.cos(2 * np.pi * f * tt)], 1)
    c, *_ = np.linalg.lstsq(M, seg, rcond=None); return db(np.hypot(*c))
def truepeak(x): return db(np.abs(sg.resample_poly(x, 4, 1, axis=0)).max())   # 4x, como BS.1770 (medidores de streaming)
def samplepeak(x): return db(np.abs(x).max())
def lufs(x):
    """BS.1770-4 con los coeficientes oficiales de 48 kHz (independiente del plugin)"""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1, -2, 1], [1, -1.99004745483398, 0.99007225036621]
    y = sg.lfilter(b2, a2, sg.lfilter(b1, a1, x, axis=0), axis=0)
    n, h = int(0.4 * SR), int(0.1 * SR)
    z = np.array([np.mean(y[i:i + n] ** 2, 0).sum() for i in range(0, len(y) - n + 1, h)])
    l = -0.691 + 10 * np.log10(z + 1e-20); z = z[l > -70]
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    return -0.691 + 10 * np.log10(z[-0.691 + 10 * np.log10(z) > rel].mean())
LOG = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in
       re.finditer(r"caso (\S+) .*LUFS_I=(\S+) TP=(\S+)", (D / "log.txt").read_text())}
def ripple(x):
    """distorsión de un seno: residuo tras quitar la fundamental (dB bajo ella)"""
    seg = x[SR:int(1.9 * SR)]; X = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    k = X.argmax(); fund = X[k - 3:k + 4].sum(); X[k - 3:k + 4] = 0; return db(X.sum() / fund)

fails = 0
def scalar(name, got, want, tol):
    global fails
    ok = abs(got - want) <= tol; fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:40s} {got:+8.2f}   (esperado {want:+.2f} ± {tol})")
def inrange(name, got, lo, hi):
    global fails
    ok = lo <= got <= hi; fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:40s} {got:+8.2f}   (entre {lo:+.2f} y {hi:+.2f})")

for p in sorted(q for q in D.glob("*.wav") if not q.stem.startswith("perf_")):
    x = load(p.stem)
    if not np.all(np.isfinite(x)) or np.abs(x).max() > 2:
        fails += 1; print("MAL", p.stem, "tiene NaN o pasa de +6 dBFS")

ref, _ = sf.read(S / "s1k_m20.wav")
scalar("bajo el techo = intacto (nulo)", db(np.abs(load("bajo_techo") - ref).max()), -140, 20)
scalar("estatico: seno limitado al techo -6", tone("estatico", 1000), -6, 0.1)
scalar("estatico: techo -1", tone("estatico_c1", 1000), -1, 0.1)
scalar("igual volumen (+10 sin limitar)", tone("unity", 1000), -20, 0.05)
inrange("escuchar cambios bajo el techo", samplepeak(load("delta_bajo")), -300, -100)
scalar("escuchar cambios (-2 -> -6)", tone("delta", 1000), db(a(-2) - a(-6)), 0.15)
scalar("enlace 100 %: R baja lo mismo", tone("link100", 1000, ch=1), -30 + 10 - 10, 0.15)
scalar("enlace 0 %: R intacto", tone("link0", 1000, ch=1), -20, 0.05)
scalar("enlace 0 %: L al techo", tone("link0", 1000, ch=0), -6, 0.1)
x = load("isp_tp"); print(f"    12 kHz con pico entre muestras: muestra {samplepeak(x):.2f}, real {truepeak(x):.2f}")
scalar("pico real 4x: pico real = techo", truepeak(x), -1, 0.15)
inrange("pico de muestra: se pasa (como debe)", truepeak(load("isp_sp")) - (-1), 0.5, 4)

# release: GR por ms tras bajar el escalón (sin auto)
ins, _ = sf.read(S / "step.wav")
def env(x, ms=1.0):
    e = np.abs(sg.hilbert(x)); n = int(SR * ms / 1000); m = len(e) // n; return e[:m * n].reshape(m, n).mean(1)
g = db(env(ins[:, 0]) * a(10) / np.maximum(env(load("release")[:, 0]), 1e-9))
print("    GR tras bajar: " + " ".join(f"{t}ms:{g[2000 + t]:.1f}" for t in (5, 50, 100, 200, 400)))
scalar("GR sostenida (+4 contra -6)", g[1800], 10, 0.2)
inrange("release 100 ms (GR a 100 ms)", g[2100], 10 * np.exp(-1) - 1.2, 10 * np.exp(-1) + 1.2)

# lookahead y latencia
for name in ("burst_la0", "burst_la3", "burst_la8"):
    x = load(name)[:, 0]; on = np.argmax(np.abs(x) > 1e-4)
    print(f"    {name}: arranca en la muestra {on} (debe ser ~48000)")
    if abs(on - 48000) > 3: fails += 1; print("MAL", name, "desalineado: la latencia no se compensó")
for name in ("burst_la3", "burst_la8"):
    inrange(f"{name}: pico de muestra <= techo", samplepeak(load(name)), -60, -6 + 0.001)
    inrange(f"{name}: pico real <= techo", truepeak(load(name)), -60, -6 + 0.2)

# batería y música: brickwall
for name in [f"drums_st{k}" for k in range(5)] + ["music"]:
    x = load(name)
    inrange(f"{name}: pico de muestra <= -1", samplepeak(x), -30, -1 + 0.001)
    inrange(f"{name}: pico real <= -1 (+0.2)", truepeak(x), -30, -1 + 0.2)
sp = [samplepeak(load(f"drums_st{k}")) for k in range(5)]
lu = [lufs(load(f"drums_st{k}")) for k in range(5)]
print("    estilos (batería +12): LUFS " + " ".join(f"{n}:{v:.1f}" for n, v in zip("TPDAS", lu)))
inrange("Agresivo suena mas fuerte que Seguro", lu[3] - lu[4], 0.2, 6)
inrange("pico de muestra (sin 4x): muestra <= -1", samplepeak(load("drums_sp")), -30, -1 + 0.001)
inrange("sin lookahead: muestra <= -1 (seguridad)", samplepeak(load("drums_la0")), -30, -1 + 0.001)

# distorsión en graves: auto release vs release fijo corto
r_auto, r_fast = ripple(load("s100_auto")[:, 0]), ripple(load("s100_fijo")[:, 0])
print(f"    100 Hz limitado 10 dB: distorsión auto release {r_auto:.1f} dB, release 10 ms {r_fast:.1f} dB")
inrange("auto release: graves limpios", r_auto, -200, -40)
if r_auto > r_fast - 6: fails += 1; print("MAL auto release no limpia mas que el release corto")
inrange("recorte 0 %: sin armonicos", ripple(load("clip0")[:, 0]), -200, -60)
inrange("recorte 100 %: agrega armonicos", ripple(load("clip100")[:, 0]), -45, -10)

# medidores: LUFS y pico real del plugin contra la referencia
scalar("LUFS: seno 1 kHz -20 dBFS estereo", LOG["lufs_sine"][0], lufs(load("lufs_sine")), 0.1)
scalar("LUFS integrado (musica limitada)", LOG["music"][0], lufs(load("music")), 0.1)
scalar("LUFS integrado (bateria)", LOG["drums_st0"][0], lufs(load("drums_st0")), 0.15)
scalar("medidor de pico real (musica)", LOG["music"][1], truepeak(load("music")), 0.2)
scalar("medidor de pico real (12 kHz sin 4x)", LOG["isp_sp"][1], truepeak(load("isp_sp")), 0.2)
for p in range(1, 19):
    x = load(f"preset{p}"); c = {1: -1, 2: -1, 3: -3, 4: -3.5, 5: -2, 6: -6, 7: -0.3, 8: -0.8, 9: -1, 10: -1, 11: -1,
                                 12: -0.8, 13: -1, 14: -3, 15: -3, 16: -0.5, 17: -1, 18: -1}[p]
    inrange(f"preset {p}: pico real <= techo {c}", truepeak(x), -60, c + 0.25)
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
