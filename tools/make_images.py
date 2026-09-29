#!/usr/bin/env python3
"""Turn source figures into the files the page serves (assets/img/*.webp).

    python3 tools/make_images.py

Needs NumPy, SciPy, Pillow and cwebp (brew install webp). Sources:
  tools/renders/*.png             from tools/render_boards.sh
  ../rlcar/aero/docs/car_hero_v5.png
  ../pallor-hb/results/fig13_shifted_pair.png
  ../eit/recon/recon_comparison.png
  tools/src/ttscout_clip.png      a frame of a generated point clip (OpenTTGames footage)
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT.parent
OUT = ROOT / "assets/img"


def webp(img: Image.Image, name: str, quality: int = 86, lossless: bool = False, max_width: int = 1600) -> None:
    if img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)
    dst = OUT / f"{name}.webp"
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        img.save(tmp.name)
        mode = ["-lossless", "-z", "9"] if lossless else ["-q", str(quality), "-alpha_q", "95", "-sharp_yuv"]
        subprocess.run(["cwebp", "-quiet", "-mt", "-m", "6", *mode, tmp.name, "-o", str(dst)], check=True)
    print(f"{dst.name:<22} {img.width} x {img.height}  {dst.stat().st_size / 1024:.0f} KB")


def trim(img: Image.Image, margin: float = 0.035) -> Image.Image:
    """Crop a transparent render to its content, so every board sits at the same scale."""
    alpha = np.asarray(img)[..., 3]
    ys, xs = np.where(alpha > 8)
    if xs.min() == 0 or ys.min() == 0 or xs.max() == img.width - 1 or ys.max() == img.height - 1:
        raise SystemExit("a render touches the edge of its frame: lower its zoom in render_boards.sh")
    m = int(margin * max(xs.max() - xs.min(), ys.max() - ys.min()))
    return img.crop((max(0, xs.min() - m), max(0, ys.min() - m),
                     min(img.width, xs.max() + m), min(img.height, ys.max() + m)))


def cut_out(img: Image.Image) -> Image.Image:
    """Lift an object off a white floor. The car is anything clearly coloured or clearly
    dark; the floor and its soft shadow are light and neutral. Edge pixels are un-mixed
    from white so no pale fringe is left on a black page."""
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    hi, lo = a.max(2), a.min(2)
    sat = hi - lo
    core = ndi.binary_opening((sat > 0.10) | (hi < 0.33), iterations=2)
    labels, n = ndi.label(core)
    sizes = ndi.sum(core, labels, range(1, n + 1))
    shape = ndi.binary_fill_holes(ndi.binary_closing(np.isin(labels, 1 + np.where(sizes > 5000)[0]), iterations=6))
    rim = shape & ~ndi.binary_erosion(shape, iterations=7)
    shape &= ~(rim & (hi > 0.72) & (sat < 0.08))          # bright neutral specks between the tyre treads
    shape = ndi.binary_opening(shape, iterations=1)
    alpha = np.clip(ndi.gaussian_filter(ndi.binary_erosion(shape, iterations=2).astype(np.float32), 1.2), 0, 1)[..., None]
    colour = np.clip(np.where(alpha > 0.02, (a - (1 - alpha)) / np.maximum(alpha, 0.02), 0), 0, 1)
    out = Image.fromarray((np.dstack([colour, alpha]) * 255).round().astype(np.uint8), "RGBA")
    ys, xs = np.where(alpha[..., 0] > 0.03)
    return out.crop((max(xs.min() - 50, 0), max(ys.min() - 50, 0),
                     min(xs.max() + 50, img.width), min(ys.max() + 50, img.height)))


OUT.mkdir(parents=True, exist_ok=True)
for name in ("pursuit", "pbr", "emg", "eit16"):
    webp(trim(Image.open(ROOT / f"tools/renders/{name}.png").convert("RGBA")), f"board_{name}", quality=88)
webp(cut_out(Image.open(DOCS / "rlcar/aero/docs/car_hero_v5.png")), "rlcar", quality=88, max_width=1400)
webp(Image.open(DOCS / "pallor-hb/results/fig13_shifted_pair.png").convert("RGB"), "pallorhb_pair", quality=90, max_width=2000)
webp(Image.open(DOCS / "eit/recon/recon_comparison.png").convert("RGB"), "eit_recon", lossless=True, max_width=1104)
webp(Image.open(ROOT / "tools/src/ttscout_clip.png").convert("RGB"), "ttscout_clip", quality=86, max_width=960)
