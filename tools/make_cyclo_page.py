"""Write cycloidal-arm/joint.html: how one printed cycloidal joint turns a stepper into 21:1.

Numbers from ~/Documents/cyclo_actuator/design.py (imported, not copied), so the page follows the design:
22 pins on R 36, E 1.0, 6 output pins on R 22, the stall prediction and the backlash budget.

    python3 tools/make_cyclo_page.py

Graphs are drawn with matplotlib as inline SVG in the site's own tokens and font, on the page ground.
"""
import importlib.util
import io
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

ROOT = Path(__file__).resolve().parent.parent
CYCLO = Path.home() / "Documents" / "cyclo_actuator"
OUT = ROOT / "cycloidal-arm" / "joint.html"

spec = importlib.util.spec_from_file_location("design", CYCLO / "design.py")
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)

N, R, RR, E = D.N_PINS, D.R_PIN, D.PIN_SLEEVE_D / 2, D.E
LOBES, RATIO = N - 1, D.RATIO
R_OUT, N_OUT = D.R_OUT, D.N_OUT
HOLE_R = RR + E + D.HOLE_CLR
EFF = 0.6
T_MOTOR = D.MOTOR_HOLD_MEAS_NM
T_STALL = T_MOTOR * RATIO * EFF
T_TEST = 1.47
# the print-ready estimate design.py prints: drawn 0.08 / 0.12 expected to print as about 0.04 / 0.05 real
LOBE_REAL, HOLE_REAL, BED_IN = 0.04, 0.05, 0.015
PITCH_ARM = (N - 1) * E
deg = math.degrees
B_LOBE = deg(2 * LOBE_REAL / PITCH_ARM)
B_BED = deg(2 * BED_IN / PITCH_ARM)
B_HOLE = deg(2 * HOLE_REAL / R_OUT)
B_CAM = D.CAM_PLAY_DEG / RATIO
B_FLOAT = 0.103
B_TOTAL = B_LOBE + B_BED + B_HOLE + B_CAM + B_FLOAT
GATE = 0.9


def cycloid(n=1400):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        psi = math.atan2(math.sin((1 - N) * t), R / (E * N) - math.cos((1 - N) * t))
        x = R * math.cos(t) - RR * math.cos(t + psi) - E * math.cos(N * t)
        y = -R * math.sin(t) + RR * math.sin(t + psi) + E * math.sin(N * t)
        pts.append((x, y))
    return pts


PROFILE = cycloid()
radii = [math.hypot(x, y) for x, y in PROFILE]
R_MIN, R_MAX = min(radii), max(radii)

# ── site tokens as placeholder colours, swapped in the finished SVG ─────────────
TOKENS = {"#0b0b01": "var(--ink)", "#0b0b02": "var(--ink-2)", "#0b0b03": "var(--ink-3)", "#0b0b04": "var(--rule)",
          "#0b0b05": "var(--rule-2)", "#0b0b06": "var(--accent)", "#0b0b07": "var(--ground)", "#0b0b08": "var(--raise)"}
INK, INK2, GREY, RULE, RULE2, ACC, GROUND, RAISE = TOKENS
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
    return s.replace("<svg ", f'<svg role="img" aria-label="{label}" ', 1)


def disc_at(cam_deg):
    """Disc outline, holes and a marker, for the cam turned cam_deg: the disc is thrown E along the cam and has turned
    back cam/(N-1) about its own centre."""
    c = math.radians(cam_deg)
    spin = -c / LOBES
    cx, cy = E * math.cos(c), E * math.sin(c)
    rot = lambda x, y: (cx + x * math.cos(spin) - y * math.sin(spin), cy + x * math.sin(spin) + y * math.cos(spin))
    outline = [rot(x, y) for x, y in PROFILE]
    holes = [rot(R_OUT * math.cos(2 * math.pi * i / N_OUT), R_OUT * math.sin(2 * math.pi * i / N_OUT)) for i in range(N_OUT)]
    mark = [rot(0, 0), rot(R_MAX * math.cos(math.pi / 2), R_MAX * math.sin(math.pi / 2))]
    return outline, holes, mark, (cx, cy)


def draw_joint(ax, cam_deg, big=False):
    outline, holes, mark, centre = disc_at(cam_deg)
    for i in range(N):
        a = 2 * math.pi * i / N
        ax.add_patch(Circle((R * math.cos(a), R * math.sin(a)), RR, fc=RULE2, ec=INK2, lw=0.6 if big else 0.5))
    ax.add_patch(Polygon(outline, closed=True, fc=RAISE, ec=ACC, lw=1.3 if big else 1.0))
    for x, y in holes:
        ax.add_patch(Circle((x, y), HOLE_R, fc=GROUND, ec=INK2, lw=0.6))
    spin = -math.radians(cam_deg) / LOBES                 # the output pins turn with the slow output, on the true axis
    for i in range(N_OUT):
        a = 2 * math.pi * i / N_OUT + spin
        ax.add_patch(Circle((R_OUT * math.cos(a), R_OUT * math.sin(a)), RR, fc=INK2, ec="none"))
    ax.add_patch(Circle(centre, 10.5, fc=GROUND, ec=INK2, lw=0.6))
    ax.plot([mark[0][0], mark[1][0]], [mark[0][1], mark[1][1]], color=INK, lw=1.4)
    ax.plot([0, 0], [0, R + 6], color=RULE2, lw=0.6, ls=(0, (3, 3)))
    ax.set_xlim(-R - 6, R + 6); ax.set_ylim(-R - 6, R + 6); ax.set_aspect("equal"); ax.axis("off")


def graph_joint():
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    draw_joint(ax, 0, big=True)
    ax.annotate(f"{N} steel pins", (R * math.cos(math.radians(40)), R * math.sin(math.radians(40))), xytext=(16, 18), textcoords="offset points", color=INK2, arrowprops=dict(arrowstyle="-", color=RULE2, lw=0.6))
    ax.annotate(f"{LOBES}-lobe disc, thrown {E:.1f} mm", (R_MAX * math.cos(math.radians(-35)), R_MAX * math.sin(math.radians(-35))), xytext=(10, -28), textcoords="offset points", color=ACC, arrowprops=dict(arrowstyle="-", color=RULE2, lw=0.6))
    ax.annotate(f"{N_OUT} output pins in {2 * HOLE_R:.1f} mm holes", (R_OUT * math.cos(math.radians(180)), R_OUT * math.sin(math.radians(180))), xytext=(-150, -105), textcoords="offset points", color=INK2, arrowprops=dict(arrowstyle="-", color=RULE2, lw=0.6))
    return svg_of(fig, f"The cycloid disc inside its ring of {N} pins: {LOBES} lobes, thrown {E} mm off centre, with {N_OUT} output pins through oversized holes.")


def graph_turn():
    steps = [0, 120, 240, 360]
    fig, axes = plt.subplots(1, 4, figsize=(8.8, 2.6))
    for ax, cam in zip(axes, steps):
        draw_joint(ax, cam)
        ax.set_title(f"motor {cam}°\noutput {-cam / LOBES:.1f}°", color=INK2, fontsize=9.5, pad=4)
    fig.tight_layout(w_pad=0.6)
    return svg_of(fig, f"Four snapshots across one motor turn. The disc wobbles round the ring once and its marker turns back {360 / LOBES:.1f} degrees, one lobe: {LOBES} motor turns make one output turn.")


def graph_torque():
    rows = [("motor holding torque", T_MOTOR, RULE2), (f"× {RATIO}, ideal", T_MOTOR * RATIO, RULE2), (f"× {EFF}, predicted stall", T_STALL, ACC)]
    fig, ax = plt.subplots(figsize=(8.6, 2.2))
    for i, (name, v, c) in enumerate(rows):
        ax.barh(i, v, color=c, height=0.5)
        ax.text(v + 0.08, i, f"{v:.2f} N m", va="center", color=INK, fontweight="bold" if c == ACC else "normal")
    ax.axvline(T_TEST, color=INK2, lw=0.8, ls=(0, (4, 3)))
    ax.text(T_TEST + 0.06, 2.42, f"test load {T_TEST} N m", color=INK2, va="bottom")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.invert_yaxis()
    ax.tick_params(axis="y", colors=INK2)
    ax.set_xlim(0, 8.4); ax.set_xlabel("N m at the joint's output"); ax.grid(False)
    fig.tight_layout()
    return svg_of(fig, f"Torque from motor to output: {T_MOTOR} N m at the motor, {T_MOTOR * RATIO:.2f} N m ideal through 21 to 1, {T_STALL:.2f} N m predicted with 60 percent efficiency, against a {T_TEST} N m test load.")


def graph_backlash():
    parts = [("lobe to pin", B_LOBE), ("output holes", B_HOLE), ("lobes bedding in", B_BED), ("cam play", B_CAM), ("dowel float", B_FLOAT)]
    fig, ax = plt.subplots(figsize=(8.6, 1.9))
    left = 0
    for i, (name, v) in enumerate(parts):
        ax.barh(0, v, left=left, color=ACC if i == 0 else (RULE2 if i % 2 else INK2), height=0.42, edgecolor=GROUND, lw=1.2)
        ax.text(left + v / 2, 0.36 if i % 2 == 0 else -0.36, f"{name}\n{v:.2f}°", ha="center", va="bottom" if i % 2 == 0 else "top", color=INK2, fontsize=8.8)
        left += v
    ax.axvline(GATE, color=INK, lw=0.9, ls=(0, (4, 3)))
    ax.text(GATE + 0.01, 0, f"gate {GATE}°", va="center", color=INK)
    ax.text(B_TOTAL, -0.05, f"  {B_TOTAL:.2f}°", va="center", color=INK, fontweight="bold")
    ax.set_xlim(0, 1.05); ax.set_ylim(-0.9, 0.9); ax.set_yticks([]); ax.set_xlabel("degrees of play at the output"); ax.grid(False)
    fig.tight_layout()
    return svg_of(fig, f"The backlash budget: lobe to pin {B_LOBE:.2f}, output holes {B_HOLE:.2f}, bedding in {B_BED:.2f}, cam play {B_CAM:.2f} and dowel float {B_FLOAT:.2f} degrees add to {B_TOTAL:.2f}, under the {GATE} degree gate.")


def ledger(rows):
    return '<dl class="kv cc-calc">' + "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in rows) + "</dl>"


def fig(svg, caption, cls=""):
    return f'<figure class="fig cc-fig {cls}"><div class="fig__in">{svg}</div><figcaption>{caption}</figcaption></figure>'


SECTIONS = [
    ("1. Pins, lobes and a wobble",
     f"<p>A cycloidal drive is a ring of pins and a disc with one lobe fewer than there are pins. An eccentric cam on the motor shaft throws the disc {E:.1f} mm off centre and swings that offset round the ring. The disc cannot spin with the cam: its lobes are trapped between the pins. So it rolls round the inside of the ring, and because it has one lobe fewer, every time the wobble goes round once the disc has turned back by one lobe.</p>",
     fig(graph_joint(), f"The disc as drawn in the part files, inside its ring of {N} steel dowels on a {2 * R:.0f} mm circle. A second disc, half a turn round, sits behind it so the two wobbles cancel."),
     ledger([
         ("Pins and lobes", f"{N} pins, {LOBES} lobes"),
         ("Ratio", f"one lobe per motor turn: 1 / {LOBES}, so <b>{RATIO} : 1</b>, output turning the other way"),
         ("Disc shape", f"radius swings {R_MIN - D.PROFILE_OFFSET:.1f} to {R_MAX - D.PROFILE_OFFSET:.1f} mm (cut {D.PROFILE_OFFSET} mm inside the ideal curve): lobes {R_MAX - R_MIN:.1f} mm deep"),
         ("No cusps", f"E · N / R = {E} × {N} / {R:.0f} = <b>{E * N / R:.2f}</b>, under 1, so every lobe is round enough to print"),
         ("Output", f"{N_OUT} dowels on a {2 * R_OUT:.0f} mm circle through holes of pin + 2E + clearance = <b>{2 * HOLE_R:.1f} mm</b>: the holes swallow the wobble and pass only the slow turn"),
     ])),
    ("2. One motor turn",
     "<p>Follow the dark line on the disc. The motor turns the cam a full circle; the disc's centre goes round with it, a millimetre off the axis, while the disc itself creeps backwards. After one motor turn it has moved one lobe.</p>",
     fig(graph_turn(), f"Snapshots at 0, 120, 240 and 360 degrees of the motor. The output turns {360 / LOBES:.1f} degrees the other way per motor turn."),
     ""),
    ("3. Why a printed disc can carry it",
     f"<p>Spur gears touch on one or two teeth at a time. Here, at any moment several lobes press on several pins, so the load is shared and the contact stress on each printed lobe stays low. That is what lets PETG carry what printed spur teeth would strip. The torque the joint can hold is the motor's, multiplied by the ratio and by the drive's efficiency, which is a guess until the joint is measured.</p>",
     fig(graph_torque(), f"Predicted, not measured: {T_MOTOR} N m is the motor's holding torque at the bench current, and the 60 percent efficiency is the number the test replaces. {T_STALL:.2f} N m is {T_STALL / T_TEST:.2f} times the {T_TEST} N m test load."),
     ""),
    ("4. The price: backlash",
     "<p>Every gap in the load path lets the output turn a little before the load is taken: between lobe and pin, between output hole and dowel, in the cam on the motor shaft, in the dowels' fit. The gaps are in series, so they add. The prediction below is written down before the test, so the dial gauge can disagree with it.</p>",
     fig(graph_backlash(), f"The print-ready estimate from the design script: drawn clearances of 0.08 and 0.12 mm are expected to print at about 0.04 and 0.05. If the printer were exact, the same drawing would give 1.24 degrees, over the gate; printed coupons decide which."),
     ledger([
         ("Lobe to pin", f"2 × {LOBE_REAL} mm at the {PITCH_ARM:.0f} mm pitch arm = <b>{B_LOBE:.2f}°</b>"),
         ("Output holes", f"2 × {HOLE_REAL} mm at the {R_OUT:.0f} mm pin circle = <b>{B_HOLE:.2f}°</b>"),
         ("Bedding in", f"2 × {BED_IN} mm of PETG flattening at the pitch arm = <b>{B_BED:.2f}°</b>"),
         ("Cam play", f"{D.CAM_PLAY_DEG}° at the cam, divided by {RATIO} = <b>{B_CAM:.2f}°</b> (an upper bound)"),
         ("Dowel float", f"<b>{B_FLOAT}°</b> (an estimate)"),
         ("Total", f"<b>{B_TOTAL:.2f}°</b> against the {GATE}° gate"),
     ])),
]

body = []
for title, intro, a, b in SECTIONS:
    body.append(f'<section class="cc-sec"><h2 class="cc-h2">{title}</h2>{intro}{a}{b}</section>')

HTML = f"""<!doctype html>
<!-- Generated by tools/make_cyclo_page.py. Edit that, not this file. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cycloidal Arm: the joint · Paing Hein Htet</title>
<meta name="description" content="How a printed cycloidal joint turns a NEMA 17 into 21 to 1: pins, lobes and an eccentric cam, the torque it is predicted to hold, and the backlash budget, with every number worked through.">
<meta name="author" content="Paing Hein Htet">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#090807">
<link rel="canonical" href="https://paingheinhtet.com/cycloidal-arm/joint.html">
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
.cc-fig {{ margin-top: 1.5rem; }}
.cc-fig svg {{ display: block; width: 100%; height: auto; }}
.cc-fig svg text {{ font-family: var(--font); }}
.cc-sec:first-of-type .cc-fig svg {{ max-width: 30rem; }}
.cc-note {{ margin-top: 4.5rem; max-width: 66ch; font-size: .875rem; line-height: 1.6; color: var(--ink-3); }}
</style>
</head>
<body>
<main class="cc-page">
  <a class="cc-back" href="../#cyclo">← Cycloidal Arm</a>
  <h1 class="cc-title">One joint, {RATIO} to 1</h1>
  <p class="cc-lede">Each of the arm's three joints is the same printed cycloidal reducer on a NEMA 17: {N} steel pins, two {LOBES}-lobe discs and an eccentric cam. How it turns a fast, weak motor into a slow, strong joint, what it is predicted to hold, and what it costs in play. Drawn and checked, not yet built: every number here is a prediction from the design script.</p>
  {"".join(body)}
  <p class="cc-note">Generated from the cycloidal arm repository's design.py. Motor torque {T_MOTOR} N m is a placeholder until the bench reading; the efficiency, the clearances and the dowel float are estimates the joint test replaces.</p>
</main>
</body>
</html>
"""
for ch in ("—", "–"):
    if ch in HTML:
        raise SystemExit("no em or en dashes on the site")
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(HTML) / 1024:.0f} KB)  r {R_MIN:.2f}..{R_MAX:.2f}  stall {T_STALL:.2f}  backlash {B_TOTAL:.3f}")
