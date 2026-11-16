"""Pruebas de la interfaz con el mouse. Requiere la demo abierta (tests/reopen.sh) y la ventana del FX al frente."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from ui import *
OUT = os.environ.get("NUBE_SHOTS", str(ROOT / "tests/out"))
fails = 0
def check(name, got, want):
    global fails
    ok = (want(got) if callable(want) else got == want); fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:44s} {got!r}")

subprocess.run(["osascript", "-e", 'tell application "REAPER" to activate']); time.sleep(0.6)
cc(f"c:{pt(500, 5)}")
check("arranca con preset 2 (Denso)", param(5), "Denso")
cc(f"c:{pt(*STYLE(1))}"); check("clic en Punch", param(5), "Punch")
cc(f"c:{pt(*STYLE(3))}"); check("clic en Agresivo", param(5), "Agresivo")
g0 = num(param(1)); x, y = KNOB(0); drag(x, y, x, y - 40)
check("arrastrar Ganancia hacia arriba sube", num(param(1)), lambda v: v > g0 + 1)
cc(f"dc:{pt(x, y)}"); check("doble clic en Ganancia = 0", num(param(1)), 0.0)
drag(*GRAPH, GRAPH[0], GRAPH[1] - 60)
check("arrastrar en la grafica sube la ganancia", num(param(1)), lambda v: 2.5 < v < 5)
yc = h2y(num(param(2))); drag(500, yc, 500, yc + 40)
check("arrastrar el techo hacia abajo", num(param(2)), lambda v: v < -4)
yc = h2y(num(param(2))); cc(f"dc:{pt(500, yc)}"); check("doble clic en el techo = -1", num(param(2)), -1.0)
x, y = KNOB(2); cc(f"m:{pt(x, y)}"); r0 = num(param(3)); wheel(5)
check("rueda sobre Release cambia", num(param(3)), lambda v: v != r0)
cc(f"c:{pt(*TP)}"); check("pico real apagado", param(8), lambda v: v.startswith("Apagado"))
cc(f"c:{pt(*TP)}"); check("pico real encendido", param(8), lambda v: v.startswith("Encendido"))
cc(f"c:{pt(*UNITY)}"); check("igual volumen", param(10), "Encendido")
cc(f"c:{pt(*UNITY)}"); check("igual volumen apagado", param(10), "Apagado")
cc(f"c:{pt(*DELTA)}"); check("escuchar cambios", param(11), lambda v: v.startswith("Solo"))
cc(f"c:{pt(*DELTA)}"); check("escuchar cambios apagado", param(11), "Normal")
a0 = param(6); cc(f"c:{pt(*AUTOREL)}"); check("auto release cambia", param(6), lambda v: v != a0)
cc(f"c:{pt(*PRESETS)}"); time.sleep(0.6); cc("kp:arrow-down", "kp:return")
check("menu Presets -> Master -14 (ganancia 4)", (num(param(1)), param(5)), (4.0, "Transparente"))
print("FALLAS:", fails)
sys.exit(1 if fails else 0)
