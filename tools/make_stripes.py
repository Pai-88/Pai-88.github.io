#!/usr/bin/env python3
"""Draw the stripe band: one stripe per distinct CP-AnemiC photograph, in its mean
conjunctiva colour, ordered by laboratory haemoglobin.

    python3 tools/make_stripes.py

Needs the pallor-hb checkout (with the dataset unpacked) next to this one, plus NumPy
and Pillow. It uses derived colour statistics only, the same ones as
pallor-hb/scripts/make_banner.py. No dataset photograph is reproduced.
Prints the numbers that belong in the [band] block of content/site.toml.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PALLOR = ROOT.parent / "pallor-hb"
sys.path.insert(0, str(PALLOR / "src"))
from pallor_hb.dataset import WHO_ANEMIA_HB_THRESHOLD, load_cp_anemic  # noqa: E402

PX_PER_STRIPE, HEIGHT = 6, 8       # the page stretches it; hard edges, no smoothing

ds = load_cp_anemic(str(PALLOR / "data/cp-anemic/cp-anemic"), dedup="perceptual", verbose=False)
order = np.argsort(ds.y, kind="stable")
hb = np.asarray(ds.y)[order]
rgb = np.clip(ds.X[["r_mean", "g_mean", "b_mean"]].to_numpy()[order], 0, 1)
below = int(np.searchsorted(hb, WHO_ANEMIA_HB_THRESHOLD))

row = np.repeat((rgb * 255).round().astype(np.uint8), PX_PER_STRIPE, axis=0)
img = np.broadcast_to(row[None], (HEIGHT, len(row), 3)).copy()
out = ROOT / "assets/img/pallorhb_stripes.png"
Image.fromarray(img, "RGB").save(out, optimize=True)

print(f"wrote {out.relative_to(ROOT)}: {len(hb)} stripes")
print(f'low = "{hb.min():.1f} g/dL"   high = "{hb.max():.1f} g/dL"')
print(f"mark_at = {100 * below / len(hb):.1f}   # {below} of {len(hb)} below {WHO_ANEMIA_HB_THRESHOLD:g} g/dL")
