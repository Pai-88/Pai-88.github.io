"""Write crank-charger/circuit.html: how the crank charger turns a hand at 90 rpm into 10 W at a phone.

Every number comes from the crank charger project, not from this file:
  ~/Documents/crank_charger/figure/model.json      design.py's prediction against crank rpm
  ~/Documents/crank_charger/sim/alternator_sweep.json  the motor constants used by design.py
  ~/Documents/crank_charger/sim/waveforms_90rpm.csv    ngspice, the circuit at the design point

    python3 tools/make_crank_circuit.py

Graphs are drawn with matplotlib as SVG and put inline, with their text left as text, so they
use the page's own font (Archivo). Standard light plots on white plates, labelled directly.
"""
import csv
import io
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
CRANK = Path.home() / "Documents" / "crank_charger"
OUT = ROOT / "crank-charger" / "circuit.html"

MODEL = json.loads((CRANK / "figure" / "model.json").read_text())
SWEEP = json.loads((CRANK / "sim" / "alternator_sweep.json").read_text())["nema23"]["params"]
WAVE = list(csv.DictReader((CRANK / "sim" / "waveforms_90rpm.csv").open()))

# ── the numbers, worked once, used everywhere on the page ────────────────────
RING, SUN, PLANET = MODEL["ring"], MODEL["sun"], MODEL["planet"]
RATIO = RING / SUN
HAND = 90.0
N_MOTOR = round(HAND * RATIO)            # rounded the way the design document rounds it,
W_MOTOR = round(N_MOTOR * 2 * math.pi / 60, 1)   # so every line can be checked with a calculator
W_HAND = HAND * 2 * math.pi / 60
K = round(SWEEP["ke"], 3)
R_COIL, L_COIL, POLES = SWEEP["r"], SWEEP["l"], SWEEP["pole_pairs"]
E_PK = K * W_MOTOR
F_E = POLES * N_MOTOR / 60
X = 2 * math.pi * F_E * L_COIL
Z = math.hypot(R_COIL, X)
I_MAX = E_PK / Z
I_CEIL = K / (POLES * L_COIL)
VF = 0.5
BUCK_EFF, USB_W, V_BUS = 0.88, 10.0, 7.0
P_BUCK_IN = USB_W / BUCK_EFF
I_BUS = P_BUCK_IN / V_BUS
CAP = 1000e-6
RIPPLE_EST = I_BUS / (4 * F_E * CAP)
row90 = next(r for r in MODEL["rows"] if r["rpm"] == 90)
P_HAND = row90["crank"]
MESH = 0.9 * 0.9
P_SHAFT = P_HAND * MESH
P_GEN_LOSS = P_SHAFT - P_BUCK_IN
T_MOTOR = P_SHAFT / W_MOTOR
T_HAND = P_HAND / W_HAND
F_GRIP = T_HAND / (MODEL["arm"] / 1000)
vbus = [float(r["v_bus"]) for r in WAVE]
ia = [float(r["i_a"]) for r in WAVE]
SIM_VBUS = sum(vbus) / len(vbus)
SIM_RIPPLE = max(vbus) - min(vbus)
SIM_IPK = max(abs(x) for x in ia)
W_MIN_OC = (V_BUS + 2 * VF) / K
N_MIN_OC = W_MIN_OC * 60 / (2 * math.pi) / RATIO
first_w = next(r["rpm"] for r in MODEL["rows"] if r["usb"] > 0)

f1 = lambda v: f"{v:.1f}"
f2 = lambda v: f"{v:.2f}"

# ── graphs ────────────────────────────────────────────────────────────────
# placeholder colours, swapped for the site's own tokens in the finished SVG, so the
# drawings sit on the page's black ground in its own inks (and print in its print inks)
TOKENS = {"#0b0b01": "var(--ink)", "#0b0b02": "var(--ink-2)", "#0b0b03": "var(--ink-3)", "#0b0b04": "var(--rule)",
          "#0b0b05": "var(--rule-2)", "#0b0b06": "var(--accent)", "#0b0b07": "var(--ground)", "#0b0b08": "var(--raise)"}
INK, INK2, GREY, RULE, RULE2, ACC, GROUND, RAISE = TOKENS
A_COL, B_COL, BUS_COL = ACC, GREY, INK
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9.5, "svg.fonttype": "none", "text.color": INK2,
    "axes.edgecolor": RULE2, "axes.labelcolor": GREY, "xtick.color": GREY, "ytick.color": GREY,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.linewidth": 0.7,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": RULE, "grid.linewidth": 0.6,
    "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 6, "ytick.major.pad": 6,
    "lines.linewidth": 1.4, "figure.facecolor": "none", "axes.facecolor": "none", "savefig.transparent": True,
})

def svg_of(fig, label):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    s = buf.getvalue()
    s = s[s.index("<svg"):]
    s = re.sub(r"font-family:[^;\"']*", "font-family:var(--font)", s)
    for hexcol, token in TOKENS.items():
        s = s.replace(hexcol, token)
    s = re.sub(r'<svg ([^>]*?)width="[^"]*" height="[^"]*"', r'<svg \1', s, count=1)
    s = s.replace("<svg ", f'<svg role="img" aria-label="{label}" ', 1)
    return s

def graph_generator():
    rpm = [i * 10 for i in range(0, 101)]
    w = [n * 2 * math.pi / 60 for n in rpm]
    e = [K * x for x in w]
    i = [K * x / math.hypot(R_COIL, POLES * x * L_COIL) if x else 0 for x in w]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.0))
    a1.plot(rpm, e, color=A_COL)
    a1.plot([N_MOTOR], [E_PK], "o", color=INK, ms=5)
    a1.annotate(f"{f1(E_PK)} V at {N_MOTOR:.0f} rpm", (N_MOTOR, E_PK), xytext=(10, -14), textcoords="offset points", color=INK)
    a1.set_xlabel("motor speed, rpm"); a1.set_ylabel("coil voltage, V peak")
    a1.set_xlim(0, 1000); a1.set_ylim(0, 36)
    a2.plot(rpm, i, color=B_COL)
    a2.axhline(I_CEIL, color=RULE2, lw=0.8, ls=(0, (4, 3)))
    a2.text(980, I_CEIL + 0.08, f"ceiling k / pL = {f2(I_CEIL)} A", ha="right", va="bottom", color=GREY)
    a2.plot([N_MOTOR], [I_MAX], "o", color=INK, ms=5)
    a2.annotate(f"{f1(I_MAX)} A at {N_MOTOR:.0f} rpm", (N_MOTOR, I_MAX), xytext=(10, -16), textcoords="offset points", color=INK)
    a2.set_xlabel("motor speed, rpm"); a2.set_ylabel("current into a short, A peak")
    a2.set_xlim(0, 1000); a2.set_ylim(0, 3.2); a2.set_yticks([0, 1, 2, 3])
    fig.tight_layout(w_pad=3)
    return svg_of(fig, "Two graphs against motor speed. Left: coil voltage rises in a straight line, 16 volts at 482 rpm. Right: the current the coil can push into a short rises fast and then flattens near 2.5 amps.")

def graph_waveforms():
    t = [float(r["t_ms"]) for r in WAVE]
    ea = [float(r["emf_a"]) for r in WAVE]; eb = [float(r["emf_b"]) for r in WAVE]
    ib = [float(r["i_b"]) for r in WAVE]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.6), sharex=True, gridspec_kw={"height_ratios": [1.25, 1]})
    a1.plot(t, ea, color=A_COL, lw=1.4); a1.plot(t, eb, color=B_COL, lw=1.4)
    a1.plot(t, vbus, color=BUS_COL, lw=1.9)
    a1.axhline(0, color=RULE2, lw=0.6)
    a1.text(0.05, E_PK + 0.6, "coil A voltage", color=A_COL, va="bottom")
    a1.text(1.36, E_PK + 0.6, "coil B, a quarter wave later", color=B_COL, va="bottom")
    a1.text(2.5, SIM_VBUS + 0.9, f"DC bus {f1(SIM_VBUS)} V", color=BUS_COL, ha="center", va="bottom", fontweight="bold", bbox=dict(fc=GROUND, ec="none", pad=1.5))
    a1.set_ylabel("volts"); a1.set_ylim(-19, 21)
    a2.plot(t, ia, color=A_COL, lw=1.6); a2.plot(t, ib, color=B_COL, lw=1.6)
    a2.axhline(0, color=RULE2, lw=0.6)
    a2.text(0.05, SIM_IPK + 0.12, f"coil currents, {f1(SIM_IPK)} A peak", color=INK, va="bottom")
    a2.set_ylabel("amps"); a2.set_ylim(-2.1, 2.3)
    a2.set_xlabel(f"time, ms (two cycles of the {F_E:.0f} Hz coil wave)")
    a2.set_xlim(0, 5)
    fig.tight_layout(h_pad=1.2)
    return svg_of(fig, "ngspice at 90 rpm on the handle. Top: the two coil voltages, 16 volts peak and a quarter wave apart, and the DC bus flat at about 7.3 volts. Bottom: the coil currents, about 1.5 amps peak, flowing only near each coil's peaks.")

def graph_power():
    rows = MODEL["rows"]
    n = [r["rpm"] for r in rows]
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    ax.axvspan(0, first_w - 2, color=RAISE, lw=0)
    ax.text((first_w - 2) / 2, 18.6, "bus below 7 V:\nthe converter\ncannot start", ha="center", va="top", color=GREY, fontsize=9)
    ax.plot(n, [r["crank"] for r in rows], color=B_COL)
    ax.plot(n, [r["usb"] for r in rows], color=A_COL)
    ax.axhline(USB_W, color=RULE2, lw=0.8, ls=(0, (4, 3)))
    ax.text(first_w + 2, USB_W + 0.3, "10 W: a 5 V, 2 A port", ha="left", va="bottom", color=GREY)
    ax.text(150, 16.9, "your arm", color=B_COL, ha="right", va="bottom")
    ax.text(150, 10.4, "the phone", color=A_COL, ha="right", va="bottom")
    ax.plot([90], [row90["usb"]], "o", color=INK, ms=5)
    ax.annotate(f"90 rpm: {f1(row90['usb'])} W for {f1(P_HAND)} W of arm", (90, row90["usb"]), xytext=(8, -18), textcoords="offset points", color=INK)
    ax.set_xlabel("handle speed, rpm"); ax.set_ylabel("watts"); ax.set_xlim(0, 160); ax.set_ylim(0, 20); ax.set_yticks([0, 5, 10, 15, 20])
    fig.tight_layout()
    return svg_of(fig, "Predicted watts against handle speed. Nothing reaches the phone below about 40 rpm. The phone's share climbs to the port's 10 watt limit at 90 rpm and stays there, while the arm's work levels off near 17 watts.")

def graph_budget():
    steps = [("your arm", P_HAND), ("motor shaft", P_SHAFT), ("DC bus", P_BUCK_IN), ("phone", USB_W)]
    losses = [("two gear meshes, 0.9 each (a guess)", P_HAND - P_SHAFT), ("coil copper and the diodes (ngspice)", P_SHAFT - P_BUCK_IN), ("converter, 88 percent", P_BUCK_IN - USB_W)]
    fig, ax = plt.subplots(figsize=(8.6, 2.6))
    for i, (name, p) in enumerate(steps):
        ax.barh(i, p, color=ACC if name == "phone" else RULE2, height=0.5)
        ax.text(p + 0.3, i, f"{f1(p)} W", va="center", color=INK, fontweight="bold" if name == "phone" else "normal")
        if i:
            ax.text(p + 2.2, i - 0.5, f"minus {f1(losses[i - 1][1])} W: {losses[i - 1][0]}", va="center", color=GREY, fontsize=9)
    ax.set_yticks(range(len(steps)), [s[0] for s in steps]); ax.invert_yaxis()
    ax.set_xlim(0, 26); ax.set_xlabel("watts at 90 rpm"); ax.grid(False); ax.tick_params(axis="y", colors=INK2)
    fig.tight_layout()
    return svg_of(fig, f"Where the arm's {f1(P_HAND)} watts go at 90 rpm: {f1(P_SHAFT)} reach the motor shaft, {f1(P_BUCK_IN)} reach the DC bus and 10 reach the phone, {round(100 * USB_W / P_HAND)} percent overall.")

# ── schematic: the real card is a ladder, so the drawing is one too ───────────
def schematic():
    W, H, TOP, BOT, MID = 940, 330, 52, 282, 167
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Schematic. Coil A and coil B of the stepper, each a voltage source with 0.9 ohm and 2.5 millihenry in series, sit between two legs of two Schottky diodes. The four legs join a PLUS rail on top and a MINUS rail below. A 1000 microfarad capacitor bridges the rails, which feed a 5 volt buck converter, a USB meter and the phone." class="cc-sch">']
    line = lambda x1, y1, x2, y2, c="var(--ink-2)", w=1.2: s.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{c}" stroke-width="{w}" fill="none"/>')
    dot = lambda x, y: s.append(f'<circle cx="{x}" cy="{y}" r="2.4" fill="var(--ink-2)"/>')
    text = lambda x, y, t, a="middle", c="var(--ink-2)", sz=13, wt=400: s.append(f'<text x="{x}" y="{y}" text-anchor="{a}" fill="{c}" font-size="{sz}" font-weight="{wt}" font-family="var(--font)">{t}</text>')
    def diode_up(x, yc):   # anode below, cathode above: current flows up
        s.append(f'<path d="M{x - 9} {yc + 7}L{x + 9} {yc + 7}L{x} {yc - 7}Z" fill="var(--ink-2)"/>')
        line(x - 9, yc - 7, x + 9, yc - 7, "var(--ink-2)", 1.8)
    def leg(x):
        line(x, TOP, x, BOT)
        diode_up(x, (TOP + MID) / 2); diode_up(x, (MID + BOT) / 2)
        dot(x, MID); dot(x, TOP); dot(x, BOT)
    def coil(x1, x2, col, name):
        xc = (x1 + x2) / 2
        src, r0, l0 = xc - 46, xc - 8, xc + 26
        line(x1, MID, src - 15, MID, col)
        s.append(f'<circle cx="{src}" cy="{MID}" r="15" fill="var(--ground)" stroke="{col}" stroke-width="1.2"/>')
        s.append(f'<path d="M{src - 8} {MID}q4 -8 8 0t8 0" stroke="{col}" stroke-width="1.2" fill="none"/>')
        zig = " ".join(f"L{r0 + i * 4} {MID + (-6 if i % 2 else 6)}" for i in range(1, 7))
        s.append(f'<path d="M{src + 15} {MID}L{r0} {MID}{zig}L{r0 + 28} {MID}L{l0} {MID}" stroke="{col}" stroke-width="1.2" fill="none"/>')
        bumps = "".join("a6 6 0 0 1 12 0" for _ in range(3))
        s.append(f'<path d="M{l0} {MID}{bumps}" stroke="{col}" stroke-width="1.2" fill="none"/>')
        line(l0 + 36, MID, x2, MID, col)
        text(xc, MID - 26, name, "middle", col, 13, 600)
        text(xc, MID + 34, f"{f1(E_PK)} V pk, {R_COIL} Ω, {L_COIL * 1000:.1f} mH", "middle", "var(--ink-3)", 11)
    LEGS = [70, 270, 340, 540]
    line(LEGS[0], TOP, 640, TOP); line(LEGS[0], BOT, 640, BOT)
    for x in LEGS: leg(x)
    coil(LEGS[0], LEGS[1], "var(--accent)", "coil A"); coil(LEGS[2], LEGS[3], "var(--ink)", "coil B")
    text(LEGS[0] - 6, TOP - 14, f"PLUS, the DC bus ({f1(SIM_VBUS)} V)", "start", "var(--ink)", 12, 600)
    text(LEGS[0] - 6, BOT + 26, "MINUS", "start", "var(--ink)", 12, 600)
    text(305, BOT + 26, "8 × Schottky (SB560), two bridges", "middle", "var(--ink-3)", 11)
    xc = 600
    line(xc, TOP, xc, MID - 6); line(xc, MID + 6, xc, BOT)
    line(xc - 16, MID - 6, xc + 16, MID - 6, "var(--ink-2)", 2); line(xc - 16, MID + 6, xc + 16, MID + 6, "var(--ink-2)", 2)
    dot(xc, TOP); dot(xc, BOT)
    text(xc + 22, MID + 4, "1000 µF", "start", "var(--ink-2)", 12)
    bx, by, bw, bh = 668, 112, 108, 110
    line(640, TOP, bx + 20, TOP); line(bx + 20, TOP, bx + 20, by)
    line(640, BOT, bx + 20, BOT); line(bx + 20, BOT, bx + 20, by + bh)
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="4" fill="var(--ground)" stroke="var(--ink-2)" stroke-width="1.2"/>')
    text(bx + bw / 2, by + 44, "buck", "middle", "var(--ink)", 14, 600)
    text(bx + bw / 2, by + 62, "7 V in, 5 V out", "middle", "var(--ink-3)", 11)
    text(bx + bw / 2, by + 78, "QC3.0, 88 %", "middle", "var(--ink-3)", 11)
    mx, my = 800, 142
    line(bx + bw, MID, mx, MID)
    s.append(f'<rect x="{mx}" y="{my}" width="58" height="50" rx="4" fill="var(--ground)" stroke="var(--ink-2)" stroke-width="1.2"/>')
    text(mx + 29, my + 22, "USB", "middle", "var(--ink)", 12, 600); text(mx + 29, my + 38, "meter", "middle", "var(--ink)", 12, 600)
    px, py = 884, 120
    line(mx + 58, MID, px, MID)
    s.append(f'<rect x="{px}" y="{py}" width="44" height="94" rx="9" fill="var(--ground)" stroke="var(--ink-2)" stroke-width="1.2"/>')
    s.append(f'<path d="M{px + 24} {MID - 16}L{px + 15} {MID + 2}L{px + 22} {MID + 2}L{px + 19} {MID + 17}L{px + 30} {MID - 3}L{px + 23} {MID - 3}Z" fill="var(--accent)"/>')
    text(px + 22, py + 112, "phone", "middle", "var(--ink)", 12, 600)
    text(bx + bw + 12, MID - 10, "5 V", "start", "var(--ink-3)", 11)
    s.append("</svg>")
    return "".join(s)

# ── the page ───────────────────────────────────────────────────────────────
def ledger(rows):
    return '<dl class="kv cc-calc">' + "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in rows) + "</dl>"

def plate(svg, caption):
    return f'<figure class="fig cc-fig"><div class="fig__in">{svg}</div><figcaption>{caption}</figcaption></figure>'

SECTIONS = [
    ("The whole path",
     f"<p>Your hand turns the ring gear; the planets spin the sun {f2(RATIO)} times faster; the sun turns the stepper, and the stepper, run backwards, is a generator with two separate coils. Each coil makes alternating current, so each gets its own bridge of four diodes. Both bridges pour into one DC bus, a capacitor keeps it steady, a buck converter brings it down to 5 V, and the phone takes what it wants through a USB meter.</p>",
     plate(schematic(), "Drawn the way the card is built: a PLUS rail along the top, a MINUS rail along the bottom, four legs of two diodes between them, and each coil sitting between its own pair of legs."),
     ""),
    ("1. The stepper is a generator",
     "<p>Turn the shaft and the rotor's magnet sweeps its flux through each coil 50 times per turn. Faraday's law makes the voltage proportional to how fast that flux changes, so the peak voltage grows in a straight line with speed. The one constant that sets it is the same one that links torque to current, and it can be read off the motor's label.</p>",
     ledger([
         ("Gear ratio", f"{RING} / {SUN} = <b>{f2(RATIO)}</b>"),
         ("Motor speed", f"{HAND:.0f} rpm × {f2(RATIO)} = <b>{N_MOTOR:.0f} rpm</b>, ω = {N_MOTOR:.0f} × 2π / 60 = <b>{f1(W_MOTOR)} rad/s</b>"),
         ("Motor constant", f"k = T<sub>hold</sub> / (√2 · I<sub>rated</sub>) = 1.26 / (1.414 × 2.8) = <b>{K:.3f} V per rad/s</b>"),
         ("Coil voltage", f"E = k · ω = {K:.3f} × {f1(W_MOTOR)} = <b>{f1(E_PK)} V peak</b> per coil"),
         ("Frequency", f"f = 50 pole pairs × {N_MOTOR:.0f} / 60 = <b>{F_E:.0f} Hz</b>"),
         ("Inductance in ohms", f"X = 2π f L = 2π × {F_E:.0f} × {L_COIL} = <b>{f1(X)} Ω</b>, against R = {R_COIL} Ω"),
         ("Current ceiling", f"I = E / √(R² + X²) = {f1(E_PK)} / {f1(Z)} = <b>{f1(I_MAX)} A</b>; the limit at any speed is k / (p L) = {f2(I_CEIL)} A"),
     ]),
     plate(graph_generator(), "Crank faster and the voltage keeps climbing, but the coil's inductance pushes back just as fast, so the current it can deliver flattens near 2.5 A. Torque follows current, so the torque is pinned too: the only way to more watts is more speed, which is why the gears multiply speed and not torque.")),
    ("2. Two bridges and a capacitor",
     "<p>Each coil swings between plus and minus 16 V. Four Schottky diodes round it flip every negative half upward, two of them carrying the current at any moment, each taking about half a volt. The two coils are a quarter wave apart, so one is near its peak while the other passes through zero, and the bus is topped up four times per cycle. The capacitor fills on each bump and gives back in the gaps.</p>",
     ledger([
         ("After the diodes, nothing drawn", f"{f1(E_PK)} − 2 × {VF} = <b>{f1(E_PK - 2 * VF)} V</b>"),
         ("Bus current at 10 W out", f"{f1(P_BUCK_IN)} W / {V_BUS:.0f} V = <b>{f1(I_BUS)} A</b>"),
         ("Ripple, hand estimate", f"I / (4 f C) = {f1(I_BUS)} / (4 × {F_E:.0f} × 0.001) ≈ <b>{f1(RIPPLE_EST)} V at most</b>"),
         ("Ripple, ngspice", f"<b>{SIM_RIPPLE:.2f} V</b> peak to peak on a {f1(SIM_VBUS)} V bus"),
         ("Why 7 V and not 15", f"under load the coil's own {f1(Z)} Ω uses up most of the 16 V; the diodes and the bus hold the coil's ends about 8 V apart"),
     ]),
     plate(graph_waveforms(), f"ngspice at 90 rpm on the handle, the coils loaded so the bus takes the converter's {f1(P_BUCK_IN)} W. The current only flows near each coil's peak, when its voltage is higher than the bus plus two diode drops, and the bus barely moves.")),
    ("3. The converter and the USB port",
     f"<p>The buck converter switches the bus on and off fast and smooths the result, keeping about 88 percent of what it takes in. It needs about 7 V to make 5 V, and that fixes everything upstream: the coil has to produce 7 V plus two diode drops before any watt reaches the phone. On the other side, a plain 5 V, 2 A port gives the phone at most 10 W, and the phone decides how much of that it asks for.</p>",
     ledger([
         ("Converter in", f"{USB_W:.0f} W / {BUCK_EFF} = <b>{f1(P_BUCK_IN)} W</b>"),
         ("Duty, ideal", f"5 V / {V_BUS:.0f} V = <b>{100 * 5 / V_BUS:.0f} percent</b> of the time switched on"),
         ("Slowest useful crank", f"coil must give {V_BUS:.0f} + 2 × {VF} = {V_BUS + 2 * VF:.0f} V, so ω = {V_BUS + 2 * VF:.0f} / {K:.3f} = {W_MIN_OC:.0f} rad/s: about <b>{N_MIN_OC:.0f} rpm</b> at the handle with nothing drawn, more with the phone on"),
         ("Port limit", "5 V × 2 A = <b>10 W</b>, reached at about 90 rpm"),
         ("1 percent of a phone", f"15 Wh / 100 / {USB_W:.0f} W = <b>{60 * 0.15 / USB_W:.1f} min</b> of cranking"),
     ]),
     plate(graph_power(), f"The design script's prediction against handle speed. The model's first watts appear near {first_w} rpm, where its coarse simulation grid starts; the hand estimate above puts the useful start a little higher. From 90 rpm on, extra speed only makes your arm work: the port is already full.")),
    ("4. Where the arm's work goes",
     f"<p>Walking backwards from the phone: power out is power in times efficiency, and power is torque times speed. At the motor that is {T_MOTOR:.2f} N m; at the handle {f2(T_HAND)} N m, about {f1(F_GRIP)} N on a {MODEL['arm']:.0f} mm grip, roughly 2 kg.</p>",
     plate(graph_budget(), f"{round(100 * USB_W / P_HAND)} percent of the arm's work reaches the phone. The gear loss is a guess (0.9 per mesh); the coil and diode loss comes from ngspice; iron loss in the stepper is not modelled, so the real numbers will be a little worse."),
     ""),
]

body = []
for title, intro, a, b in SECTIONS:
    body.append(f'<section class="cc-sec"><h2 class="cc-h2">{title}</h2>{intro}{a}{b}</section>')

HTML = f"""<!doctype html>
<!-- Generated by tools/make_crank_circuit.py. Edit that, not this file. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crank Charger: the circuit · Paing Hein Htet</title>
<meta name="description" content="How a hand-crank phone charger turns 90 rpm into 10 W: a stepper motor as a generator, two Schottky bridges, a capacitor, a buck converter and a USB port, with every number worked through.">
<meta name="author" content="Paing Hein Htet">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#090807">
<link rel="canonical" href="https://paingheinhtet.com/crank-charger/circuit.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&amp;display=swap">
<link rel="stylesheet" href="../styles.css">
<style>
.cc-page {{ width: min(100% - 2 * var(--gutter, 1.25rem), 72rem); margin: 0 auto; padding: 2.5rem 0 5rem; }}
.cc-back {{ display: inline-block; margin-bottom: 2.5rem; color: var(--ink-2); }}
.cc-title {{ font-stretch: 72%; font-weight: 800; font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: .95; margin: 0 0 1.25rem; }}
.cc-lede {{ max-width: 62ch; font-size: 1.125rem; line-height: 1.6; color: var(--ink-2); }}
.cc-sec {{ margin-top: 4.5rem; padding-top: 2rem; border-top: 1px solid var(--rule-2, #2a2826); }}
.cc-h2 {{ font-stretch: 72%; font-weight: 800; font-size: clamp(1.6rem, 3.4vw, 2.4rem); margin: 0 0 1rem; }}
.cc-sec > p {{ max-width: 66ch; line-height: 1.65; color: var(--ink-2); }}
.cc-calc {{ margin: 1.75rem 0 2rem; max-width: 60rem; }}
.cc-calc sub {{ font-size: .7em; }}
.cc-fig {{ margin-top: 1.5rem; }}
.cc-fig svg {{ display: block; width: 100%; height: auto; }}
.cc-fig .fig__in {{ overflow-x: auto; }}
.cc-sch {{ min-width: 640px; }}
.cc-fig svg text {{ font-family: var(--font); }}
.cc-note {{ margin-top: 4.5rem; max-width: 66ch; font-size: .875rem; line-height: 1.6; color: var(--ink-3); }}
</style>
</head>
<body>
<main class="cc-page">
  <a class="cc-back" href="../#crank">← Crank Charger</a>
  <h1 class="cc-title">The circuit, from hand to phone</h1>
  <p class="cc-lede">A hand at {HAND:.0f} rpm, a stepper motor run backwards, eight diodes, a capacitor and a converter: how the crank charger is predicted to put {USB_W:.0f} W into a phone, worked through one number at a time. Every figure here comes from the project's design script and its ngspice model, the same numbers as the <a href="design-document.pdf">design document</a>.</p>
  {"".join(body)}
  <p class="cc-note">Generated from the crank charger repository: design.py, sim/alternator_sweep.py and sim/waveforms.py. Motor constants from the NEMA23 label: 1.26 N m holding, 2.8 A, 0.9 Ω, 2.5 mH. The converter's 88 percent and the 0.9 per gear mesh are assumptions.</p>
</main>
</body>
</html>
"""

for ch in ("\u2014", "\u2013"):
    if ch in HTML:
        raise SystemExit("no em or en dashes on the site")
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(HTML) / 1024:.0f} KB)")
print(f"E {E_PK:.2f} V, f {F_E:.0f} Hz, X {X:.2f}, Z {Z:.2f}, I {I_MAX:.2f} A, ceiling {I_CEIL:.2f} A")
print(f"shaft {P_SHAFT:.2f} W, gen loss {P_GEN_LOSS:.2f} W, T motor {T_MOTOR:.3f}, T hand {T_HAND:.2f}, F {F_GRIP:.1f} N")
print(f"sim bus {SIM_VBUS:.2f} V ripple {SIM_RIPPLE:.3f} V, I pk {SIM_IPK:.2f} A; min crank {N_MIN_OC:.0f} rpm; first watts {first_w} rpm")
