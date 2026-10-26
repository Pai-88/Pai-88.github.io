#!/usr/bin/env python3
"""OXI-1 figures for the page: assets/img/oxi_hero.webp and oxi_exploded.webp.

    python3 tools/make_oxi.py

Sources: ../oxi/cad/compact/site_hero.png and site_exploded.png, rendered by
`Blender -b -P compact/site_render.py -- compact 1.0 128 hero exploded` in ~/Documents/oxi/cad
(the site's black studio: transparent film, floor fading to transparent, black solder mask).
Same trim + cwebp settings as make_images.py, kept separate so that script's other sources need not exist.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "oxi/cad/compact"
OUT = ROOT / "assets/img"


def trim(img: Image.Image, margin: float = 0.035) -> Image.Image:
    alpha = np.asarray(img)[..., 3]
    ys, xs = np.where(alpha > 8)
    m = int(margin * max(xs.max() - xs.min(), ys.max() - ys.min()))
    return img.crop((max(0, xs.min() - m), max(0, ys.min() - m), min(img.width, xs.max() + m), min(img.height, ys.max() + m)))


def webp(img: Image.Image, name: str, quality: int = 88, max_width: int = 1600) -> None:
    if img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)
    dst = OUT / f"{name}.webp"
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        img.save(tmp.name)
        subprocess.run(["cwebp", "-quiet", "-mt", "-m", "6", "-q", str(quality), "-alpha_q", "95", "-sharp_yuv", tmp.name, "-o", str(dst)], check=True)
    print(f"{dst.name:<22} {img.width} x {img.height}  {dst.stat().st_size / 1024:.0f} KB")


for view in ("hero", "exploded"):
    webp(trim(Image.open(SRC / f"site_{view}.png").convert("RGBA")), f"oxi_{view}")
