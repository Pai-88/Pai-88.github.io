"""Redraw of fracture pin figures 2 to 6 (14 Nov 2026), content corrected after source verification.

Content (structures, labels, numbers, positions) is copied from the student's own
figures in ../yours_original/. Only layout is changed: pointer ends, label overlaps,
pixel-scale text removed, timeline bars made to match their own labels.
Run:  python3 draw_figs.py   (writes fig2.png ... fig6.png next to this file)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon, Rectangle, FancyBboxPatch, Circle, Ellipse
from pathlib import Path
import matplotlib.patheffects as pe

OUT = Path(__file__).resolve().parent
for fam in ["Helvetica Neue", "Arial", "Liberation Sans"]:
    if any(fam == f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = fam
        break
plt.rcParams.update({"font.size": 13, "savefig.dpi": 200})

INK = "#2f3440"     # text
GREY = "#6b7280"    # secondary text, pointer lines
PIN = "#3a4250"     # metal
BONE = "#efe3cb"    # cancellous
CORTEX = "#c9b48f"  # cortex
RED = "#c4453a"     # artery, fracture, periosteum
YEL = "#d3a22c"     # nerves, growth plate
BLUE = "#2b5f8e"    # lateral pins, cap
PINK = "#f3d6d3"    # skin / soft tissue
LINE = "#6e5638"    # bone outline, textbook style
plt.rcParams["hatch.linewidth"] = 0.6
STROKE = lambda c: [pe.Stroke(linewidth=6.5, foreground=c), pe.Normal()]


def trabeculae(ax, clip, box, n=170, seed=7):
    """Short random strokes clipped to a patch: reads as spongy bone, not flat fill."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = box
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        a = rng.uniform(0, np.pi)
        L = rng.uniform(8, 20)
        ln, = ax.plot([x, x + L * np.cos(a)], [y, y + L * np.sin(a)], color=CORTEX, lw=1.0)
        ln.set_clip_path(clip)


def canvas(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w * 100)
    ax.set_ylim(0, h * 100)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def pointer(ax, xy_text, xy_end, text, ha="left", bold=False, size=13):
    ax.plot([xy_text[0], xy_end[0]], [xy_text[1], xy_end[1]], color=GREY, lw=1.1)
    ax.plot(*xy_end, "o", color=GREY, ms=3.5)
    dx = 8 if ha == "left" else -8
    ax.text(xy_text[0] + dx, xy_text[1], text, ha=ha, va="center", color=INK,
            fontsize=size, fontweight="bold" if bold else "normal")


def save(fig, name):
    fig.savefig(globals()["OUT"] / name, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 2
def fig2():
    fig, ax = canvas(11.3, 4.6)
    def wire(y, d, length, tip=60, threaded=False, x0=40):
        h = d * 10  # 10 units per mm, same scale for both wires
        ax.add_patch(Polygon([[x0, y - h / 2], [x0 + length, y - h / 2],
                              [x0 + length + tip, y], [x0 + length, y + h / 2],
                              [x0, y + h / 2]], closed=True, fc=PIN, ec="#1f242c", lw=0.8))
        ax.plot([x0 + 4, x0 + length - 4], [y + h * 0.22] * 2, color="#8a93a3", lw=max(0.6, h * 0.08),
                solid_capstyle="butt")
        if threaded:
            for k in range(6):
                xx = x0 + length - 150 + k * 22
                ax.plot([xx, xx + 12], [y - h / 2, y + h / 2], color="white", lw=2)
    ax.text(40, 425, "K-wire, 1.6 mm, smooth, trocar tip", fontsize=14, fontweight="bold", color=INK)
    wire(385, 1.6, 820)
    ax.text(940, 385, "1.6 mm", va="center", color=GREY)
    ax.text(40, 305, "Steinmann pin, 4.0 mm, smooth, trocar tip", fontsize=14, fontweight="bold", color=INK)
    wire(258, 4.0, 820, tip=100)
    ax.text(980, 258, "4.0 mm", va="center", color=GREY)
    ax.text(40, 195, "Diameters to the same scale; lengths not to scale. Bending stiffness rises with "
            "diameter$^4$: (4.0 / 1.6)$^4$ ≈ 39.", color=GREY, fontsize=12)
    ax.text(40, 150, "Tip shapes", fontsize=14, fontweight="bold", color=INK)
    for x0, lab, thr in [(40, "Trocar: three facets,\n129 °C drilled dry", False),
                         (400, "Diamond: four facets,\n98 °C drilled dry", False),
                         (750, "Threaded: more grip,\nnot across a growth plate", True)]:
        wire(95, 3.0, 110 if not thr else 170, tip=60, threaded=thr, x0=x0)
        ax.text(x0, 50, lab, va="top", color=INK, fontsize=12)
    save(fig, "fig2-kwire-vs-steinmann-pin-tips.png")


# ---------------------------------------------------------------- Figure 3
def fig3():
    fig, ax = canvas(11.3, 5.6)
    outer = [[480, 540], [660, 540], [660, 320], [725, 230], [725, 100], [670, 70],
             [470, 70], [405, 100], [405, 230], [480, 320]]
    inner = [[518, 540], [622, 540], [622, 310], [675, 225], [675, 115], [655, 100],
             [490, 100], [455, 115], [455, 225], [518, 310]]
    ax.add_patch(Polygon(outer, closed=True, fc=CORTEX, ec=LINE, lw=1.6, hatch="////"))
    core = Polygon(inner, closed=True, fc=BONE, ec=LINE, lw=0.8)
    ax.add_patch(core)
    trabeculae(ax, core, (455, 675, 100, 540), n=260)
    peri = np.array(outer + [outer[0]], float)
    peri[:, 0] += np.where(peri[:, 0] > 565, 12, -12)
    peri[:, 1] = np.where(peri[:, 1] < 100, peri[:, 1] - 12, peri[:, 1])
    ax.plot(peri[1:-1, 0], peri[1:-1, 1], ls=(0, (4, 3)), color=RED, lw=2.5)
    ax.plot(peri[[0, -2], 0], peri[[0, -2], 1], ls=(0, (4, 3)), color=RED, lw=2.5)
    xs = np.linspace(405, 725, 9)
    ax.plot(xs, 250 + 12 * np.array([0, 1, -1, 1, -1, 1, -1, 1, 0]), color=RED, lw=2)
    xx = np.linspace(410, 720, 200)
    ax.plot(xx, 135 + 6 * np.sin((xx - 410) / 310 * 6 * np.pi), color=YEL, lw=5)
    # left labels
    pointer(ax, (330, 470), (499, 470), "Cortex, thick in the shaft", ha="right")
    pointer(ax, (330, 400), (468, 400), "Periosteum, thick in a child", ha="right")
    pointer(ax, (330, 185), (430, 185), "Cortex thins near the elbow", ha="right")
    # right labels
    ax.add_patch(Ellipse((565, 272), 96, 44, fc="white", ec=LINE, lw=1.0, ls=(0, (3, 2)), alpha=0.8, zorder=3))
    pointer(ax, (800, 345), (570, 345), "Cancellous bone (spongy core)")
    pointer(ax, (800, 300), (600, 278), "Thin bone joining the two columns")
    pointer(ax, (800, 255), (712, 255), "Supracondylar fracture line")
    pointer(ax, (800, 175), (700, 137), "Growth plate (physis), cartilage")
    pointer(ax, (800, 95), (690, 85), "Epiphysis, then joint cartilage")
    ax.text(40, 30, "Schematic, not to scale. Front view, lower end of a child's humerus.",
            color=GREY, fontsize=12)
    save(fig, "fig3-childs-distal-humerus-section.png")


# ---------------------------------------------------------------- Figure 4
def fig4():
    fig, ax = canvas(11.3, 3.9)
    x0, wk = 120, 80  # x of week 0, units per week
    X = lambda w: x0 + w * wk
    bars = [  # (start wk, end wk, colour, label, text colour, continues)
        (0, 1, "#d4675c", "Inflammation: peaks in a day, over in a week", INK, False),
        (0.5, 2, YEL, "Soft cartilage callus: peaks days 7 to 9*", INK, False),
        (1, 4, CORTEX, "Hard bony callus: peaks by day 14*", INK, False),
        (3, 12, "#efe3cb", "Remodelling: starts weeks 3 to 4, continues for years", GREY, True),
    ]
    for i, (a, b, col, lab, tc, cont) in enumerate(bars):
        y = 330 - i * 40
        ax.add_patch(Rectangle((X(a), y - 13), X(b) - X(a), 26, color=col, ec=CORTEX if col == "#efe3cb" else col))
        if cont:
            ax.annotate("", xy=(X(12) + 30, y), xytext=(X(12), y),
                        arrowprops=dict(arrowstyle="-|>", color=col if col != "#efe3cb" else CORTEX, lw=2))
        if b - a >= 5:
            ax.text((X(a) + X(b)) / 2, y, lab, ha="center", va="center", color=tc, fontsize=12.5)
        else:
            ax.text(X(b) + 12, y, lab, va="center", color=tc, fontsize=12.5)
    ax.plot([X(0), X(12)], [157, 157], color=GREY, lw=1.2)
    for w in [0, 1, 2, 3, 4, 6, 8, 10, 12]:
        ax.plot([X(w)] * 2, [151, 163], color=GREY, lw=1.2)
        ax.text(X(w), 128, f"{w}" + (" wk" if w == 12 else ""), ha="center", va="top", color=INK,
                fontweight="bold" if w == 3 else "normal")
    ax.plot([X(3)] * 2, [157, 197], color=BLUE, lw=2.5)
    ax.plot(X(3), 157, "o", color=BLUE, ms=7)
    ax.text(X(3), 92, "Child's elbow pins out at week 3", ha="center", va="top",
            fontweight="bold", color=INK)
    ax.text(40, 30, "* Peak timings are from animal models; healing is faster in the young.", color=GREY, fontsize=12)
    save(fig, "fig4-healing-timeline.png")


# ---------------------------------------------------------------- Figure 5
def fig5():
    fig, ax = canvas(11.3, 6.0)
    hum = [[470, 600], [660, 600], [660, 390], [745, 300], [745, 210], [360, 210], [360, 330], [470, 400]]
    ax.add_patch(Polygon(hum, closed=True, fc=BONE, ec=LINE, lw=1.6))
    for x, lab in [(385, "Radius"), (597, "Ulna")]:
        ax.add_patch(FancyBboxPatch((x, 40), 95 if x == 385 else 125, 150,
                                    boxstyle="round,pad=0,rounding_size=14", fc=BONE, ec=LINE, lw=1.6))
        ax.text(x + (47 if x == 385 else 62), 75, lab, ha="center", color=GREY)
    xs = np.linspace(365, 740, 9)
    ax.plot(xs, 265 + 8 * np.array([0, 1, -1, 1, -1, 1, -1, 1, 0]), color=RED, lw=2)
    ax.add_patch(Circle((765, 225), 40, color="#f1c9c6", alpha=0.85, zorder=1))
    # nerves and artery (courses as in the student's figure)
    ax.plot([492, 470, 430, 380, 370, 358], [600, 480, 380, 300, 240, 130], color=YEL, lw=4, path_effects=STROKE("#8a6512"))      # radial
    ax.plot([565, 565, 548, 535], [600, 330, 220, 130], color=RED, lw=4.5, path_effects=STROKE("#7d231c"))                         # brachial a.
    ax.plot([583, 583, 568, 552], [600, 330, 220, 130], color=YEL, lw=4, path_effects=STROKE("#8a6512"))                           # median
    ax.plot([633, 633, 680, 730, 765, 780], [600, 380, 310, 260, 225, 130], color=YEL, lw=4, path_effects=STROKE("#8a6512"))       # ulnar
    # pins
    ax.plot([220, 470], [200, 395], color=BLUE, lw=4)
    ax.plot([235, 517], [145, 365], color=BLUE, lw=4)
    ax.plot([628, 905], [375, 160], color=PIN, lw=4, ls=(0, (3, 2)))
    # labels
    ax.text(30, 560, "Front view, right elbow. Schematic.", color=GREY, fontsize=12)
    ax.text(680, 540, "Humerus", color=GREY)
    ax.text(30, 385, "Lateral-only: two or three\npins from the outer side", fontweight="bold", color=INK,
            va="center", fontsize=14)
    ax.text(1100, 385, "Crossed: adds a medial pin,\nentering at the ulnar nerve", fontweight="bold", color=INK,
            ha="right", va="center", fontsize=14)
    ax.text(30, 335, "Ulnar nerve injury 0.7%", color=GREY, fontsize=12.5)
    ax.text(1100, 335, "Ulnar nerve injury 3.4%", color=GREY, fontsize=12.5, ha="right")
    ax.text(30, 255, "Lateral (outer) side", color=GREY)
    ax.text(790, 300, "Fracture", color=GREY)
    ax.text(825, 248, "Medial epicondyle", color=GREY)
    ax.text(800, 120, "Ulnar nerve", fontweight="bold", color=INK, fontsize=14)
    ax.text(240, 95, "Radial nerve", fontweight="bold", color=INK, fontsize=14)
    pointer(ax, (590, 18), (560, 175), "Brachial artery and median nerve, in front")
    save(fig, "fig5-elbow-nerves-artery-pin-paths.png")


# ---------------------------------------------------------------- Figure 6
def fig6():
    fig, ax = canvas(11.3, 4.8)
    x0, x1 = 95, 565
    layers = [  # (top, bottom, colour)
        (415, 375, PINK), (375, 335, "#e9eef2"), (335, 270, "#ecc0bb"), (270, 258, RED),
        (258, 230, CORTEX), (230, 140, BONE), (140, 112, CORTEX), (112, 40, PINK)]
    for top, bot, col in layers:
        r = Rectangle((x0, bot), x1 - x0, top - bot, fc=col, ec=LINE if col in (CORTEX, BONE) else "none",
                      lw=0.6, hatch="////" if col == CORTEX else None)
        ax.add_patch(r)
        if col == BONE:
            trabeculae(ax, r, (x0, x1, bot, top), n=220, seed=11)
    ax.add_patch(Rectangle((x0, 40), x1 - x0, 375, fill=False, ec=LINE, lw=1.2))
    ax.add_patch(Rectangle((280, 120), 15, 330, fc=PIN, ec="#1f242c", lw=0.8, zorder=5))
    ax.plot([284, 284], [125, 445], color="#8a93a3", lw=1.2, zorder=6)
    ax.add_patch(Polygon([[280, 120], [295, 120], [287.5, 95]], closed=True, color=PIN, zorder=5))
    ax.add_patch(FancyBboxPatch((252, 440), 70, 20, boxstyle="round,pad=0,rounding_size=6", color=BLUE, zorder=6))
    ax.plot(392, 70, "o", color=YEL, ms=13)
    ax.plot(455, 70, "o", color=RED, ms=13)
    rows = [(450, "Cap on the bent, cut end"),
            (395, "Skin: the barrier the pin holds open for weeks"),
            (355, "Fat: deeper in obese patients, so more unsupported pin"),
            (302, "Muscle and tendon: a pin through a tendon stops the joint"),
            (264, "Periosteum: living wrapping, source of healing cells"),
            (240, "Near cortex: first grip, thin in a child"),
            (185, "Cancellous bone: little grip; heat limit 47 °C for 1 min"),
            (126, "Far cortex: second grip, then a sudden give"),
            (70, "Beyond: ulnar nerve or brachial artery")]
    for y, t in rows:
        ax.text(590 if y < 440 else 335, y, t, va="center", color=INK, fontsize=12.5)
    ax.text(95, 18, "Schematic, not to scale. Tip stopped just past the far cortex.", color=GREY, fontsize=12)
    save(fig, "fig6-layers-the-pin-crosses.png")


if __name__ == "__main__":
    import sys
    if "--sketch" in sys.argv:
        # hand-drawn look: wobbly strokes, same content; output in sketch/
        OUT = OUT / "sketch"
        OUT.mkdir(exist_ok=True)
        fam = plt.rcParams["font.family"]
        with plt.xkcd(scale=0.8, length=120, randomness=2):
            plt.rcParams["font.family"] = fam
            plt.rcParams["path.effects"] = []
            plt.rcParams["font.size"] = 13
            for f in (fig2, fig3, fig4, fig5, fig6):
                f()
    else:
        for f in (fig2, fig3, fig4, fig5, fig6):
            f()
    print("done")
