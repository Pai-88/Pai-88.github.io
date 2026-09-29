#!/usr/bin/env python3
"""Make assets/og.png, the 1200 x 630 picture that LinkedIn and others show for a link.

    python3 build.py && python3 tools/make_og.py

The page is rebuilt at the end, because its link to the picture carries the picture's hash.

It is a capture of the first screen of the page itself, taken with headless Chrome at
1800 x 945 (the same shape) and reduced, so the card always matches the site.
Needs Google Chrome and Pillow.
"""
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VIEW = (1800, 945)
CARD = (1200, 630)

with tempfile.TemporaryDirectory() as tmp:
    shot = Path(tmp) / "hero.png"
    chrome = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
         f"--user-data-dir={tmp}/profile", "--force-device-scale-factor=1",
         "--force-prefers-reduced-motion",            # capture the settled page, not the entrance
         f"--window-size={VIEW[0]},{VIEW[1]}", "--virtual-time-budget=6000",
         f"--screenshot={shot}", (ROOT / "index.html").as_uri()],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Chrome writes the picture and then often stays open, so wait for the file, not the process
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and not (shot.exists() and shot.stat().st_size):
        time.sleep(0.25)
    time.sleep(1)
    chrome.terminate()
    try:
        chrome.wait(timeout=10)
    except subprocess.TimeoutExpired:
        chrome.kill()
    if not shot.exists():
        raise SystemExit("Chrome did not produce a capture within 60 s")
    card = Image.open(shot).convert("RGB")
    if card.size != VIEW:
        raise SystemExit(f"capture is {card.size}, expected {VIEW}")
    card = card.resize(CARD, Image.LANCZOS)

out = ROOT / "assets/og.png"
card.save(out, optimize=True)
print(f"wrote {out.relative_to(ROOT)} {card.size}, {out.stat().st_size / 1024:.0f} KB")
subprocess.run(["python3", str(ROOT / "build.py")], check=True)
