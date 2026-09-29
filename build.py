#!/usr/bin/env python3
"""Build index.html from content/site.toml.

    python3 build.py            write index.html
    python3 build.py --check    exit 1 if index.html is not what the content would produce

Standard library only. Nothing is built on the server: this script runs here and the
index.html it writes is what gets committed and served.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import struct
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content" / "site.toml"
STYLES = ROOT / "styles.css"
OUT = ROOT / "index.html"

FONTS = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap"
TIERS = ("featured", "hardware", "software")
EVIDENCE = ("real", "sim", "untested")
LAYOUTS = ("side", "wide")
DASHES = (chr(0x2013), chr(0x2014))     # en and em dash: not used in the copy


# ── Freshness ────────────────────────────────────────────────────────────────
# Every project block carries `checked`, the date its facts were last compared
# against the repo. This is the one place the build can stop a stale claim from
# going out under your name.

def staleness(days: int, evidence: str) -> str:
    """Decide what the build does with a block last checked `days` ago.

    evidence is "real", "sim" or "untested". Return one of:
        "ok"     publish silently
        "warn"   publish, and print a reminder
        "block"  refuse to write index.html until the block is re-checked
    """
    # TODO(Paing): your policy, 5 to 10 lines. README.md lists the trade-offs.
    # The default below never blocks, so the site always builds.
    return "warn" if days > 30 else "ok"


def freshness(projects: list[dict], today: dt.date) -> bool:
    """Print what needs re-checking. True if anything blocks the build."""
    blocked = False
    for p in projects:
        days = (today - p["checked"]).days
        verdict = staleness(days, p["evidence"])
        if verdict not in ("ok", "warn", "block"):
            raise SystemExit(f"staleness() returned {verdict!r} for {p['id']}; expected ok, warn or block")
        if verdict != "ok":
            print(f"  {verdict.upper():<5} {p['id']:<10} last checked {p['checked']} ({days} days ago)")
        blocked |= verdict == "block"
    return blocked


# ── Small helpers ────────────────────────────────────────────────────────────

def esc(text: str) -> str:
    return html.escape(text, quote=True)


def rich(text: str) -> str:
    """Escape, then turn **bold** into <b>. That is the whole markup language."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(text))


def long_date(d: dt.date) -> str:
    return f"{d.day} {d:%B %Y}"


def image_size(path: Path) -> tuple[int, int]:
    """Pixel size of a PNG or WebP, read from the header, so every <img> can carry
    width and height and the page does not jump while images load."""
    head = path.read_bytes()[:32]
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        kind = head[12:16]
        if kind == b"VP8 ":
            w, h = struct.unpack("<HH", head[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if kind == b"VP8L":
            bits = struct.unpack("<I", head[21:25])[0]
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if kind == b"VP8X":
            w = int.from_bytes(head[24:27], "little") + 1
            h = int.from_bytes(head[27:30], "little") + 1
            return w, h
    raise SystemExit(f"cannot read the size of {path}")


def validate(site: dict) -> None:
    """Fail loudly on the mistakes that are easy to make when editing the content file."""
    seen = set()
    for p in site["project"]:
        where = f"project {p.get('id', '?')!r}"
        for key in ("id", "tier", "name", "what", "evidence", "status", "checked", "summary"):
            if key not in p:
                raise SystemExit(f"{where}: missing {key}")
        if p["id"] in seen:
            raise SystemExit(f"{where}: id used twice")
        seen.add(p["id"])
        if p["tier"] not in TIERS:
            raise SystemExit(f"{where}: tier must be one of {TIERS}")
        if p["evidence"] not in EVIDENCE:
            raise SystemExit(f"{where}: evidence must be one of {EVIDENCE}")
        if p.get("layout", "side") not in LAYOUTS:
            raise SystemExit(f"{where}: layout must be one of {LAYOUTS}")
        if not isinstance(p["checked"], dt.date):
            raise SystemExit(f"{where}: checked must be a date, like 2026-09-29")
        for f in p.get("figure", []):
            if not (ROOT / f["src"]).is_file():
                raise SystemExit(f"{where}: figure {f['src']} does not exist")
            if not f.get("alt"):
                raise SystemExit(f"{where}: figure {f['src']} needs alt text")
    text = CONTENT.read_text(encoding="utf-8")
    for n, line in enumerate(text.splitlines(), 1):
        if any(dash in line for dash in DASHES):
            raise SystemExit(f"content/site.toml line {n}: no em or en dashes in the copy")


# ── Pieces of the page ───────────────────────────────────────────────────────

MARK = '<span class="mark" aria-hidden="true"></span>'


def figure(f: dict, cls: str = "") -> str:
    w, h = image_size(ROOT / f["src"])
    extra = f" {cls}" if cls else ""
    return (
        f'<figure class="fig fig--{f["kind"]}{extra}">'
        f'<div class="fig__in"><img src="{esc(f["src"])}" width="{w}" height="{h}" '
        f'alt="{esc(f["alt"])}" loading="lazy" decoding="async"></div>'
        f'<figcaption>{rich(f["caption"])}</figcaption></figure>'
    )


def links(items: list[dict]) -> str:
    if not items:
        return ""
    anchors = "".join(f'<a href="{esc(a["href"])}">{esc(a["label"])}</a>' for a in items)
    return f'<p class="links">{anchors}</p>'


def facts(items: list[dict]) -> str:
    rows = []
    for f in items:
        value = rich(f["value"])
        if "href" in f:
            value = f'<a href="{esc(f["href"])}">{value}</a>'
        rows.append(f"<div><dt>{esc(f['label'])}</dt><dd>{value}</dd></div>")
    return "\n        ".join(rows)


def featured(p: dict) -> str:
    layout = p.get("layout", "side")
    tools = f'<p class="tools">{esc(p["tools"])}</p>' if p.get("tools") else ""
    figs = "\n        ".join(figure(f) for f in p.get("figure", []))
    table = f'<dl class="kv">\n        {facts(p.get("fact", []))}\n      </dl>'
    text = (
        f'<p class="work__summary">{rich(p["summary"])}</p>\n'
        f'        <div class="work__more">{links(p.get("link", []))}{tools}</div>'
    )
    if layout == "wide":          # text | facts, figures below
        body = f'<div class="work__text">\n        {text}\n      </div>\n      {table}'
    else:                         # text and facts | figure
        body = f'<div class="work__text">\n        {text}\n        {table}\n      </div>'
    return f"""
  <article class="work work--{layout}" id="{esc(p['id'])}">
    <header class="work__head">
      <h3 class="work__name">{esc(p['name'])}</h3>
      <div class="work__intro">
        <p class="work__what">{esc(p['what'])}</p>
        <p class="status">{MARK}{esc(p['status'])}</p>
      </div>
    </header>
    <div class="work__body">
      {body}
      <div class="work__figs">
        {figs}
      </div>
    </div>
  </article>"""


def row(p: dict) -> str:
    figs = p.get("figure", [])
    fig = figure(figs[0], "row__fig") if figs else ""
    tools = f'<p class="tools">{esc(p["tools"])}</p>' if p.get("tools") else ""
    return f"""
    <article class="row" id="{esc(p['id'])}">
      <div class="row__id">
        <h4 class="row__name">{esc(p['name'])}</h4>
        <p class="row__what">{esc(p['what'])}</p>
      </div>
      <div class="row__text">
        <p class="status">{MARK}{esc(p['status'])}</p>
        <p>{rich(p['summary'])}</p>
        {links(p.get('link', []))}{tools}
      </div>
      {fig}
    </article>"""


def person_schema(site: dict) -> str:
    me = site["person"]
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": me["name"],
        "url": site["site"]["url"],
        "email": f"mailto:{me['email']}",
        "address": {"@type": "PostalAddress", "addressLocality": me["location"]},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "University College London"},
        "sameAs": [e["href"] for e in site["elsewhere"]],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


# ── The page ─────────────────────────────────────────────────────────────────

def page(site: dict) -> str:
    meta, me, band = site["site"], site["person"], site["band"]
    projects = site["project"]
    by_tier = {t: [p for p in projects if p["tier"] == t] for t in TIERS}
    checked = max(p["checked"] for p in projects)
    css = hashlib.sha256(STYLES.read_bytes()).hexdigest()[:10]
    url = meta["url"]
    bw, bh = image_size(ROOT / band["src"])

    selected = "".join(featured(p) for p in by_tier["featured"])
    ledger = "".join(
        f'\n    <h3 class="label ledger__group">{title}</h3>' + "".join(row(p) for p in by_tier[tier])
        for tier, title in (("hardware", "Hardware"), ("software", "Software")) if by_tier[tier])
    pubs = "".join(f"""
    <div class="cite">
      <p class="cite__ref">{esc(c['authors'])} ({esc(c['year'])}). <cite>{esc(c['title'])}.</cite> {esc(c['venue'])}. <a href="https://doi.org/{esc(c['doi'])}">doi:{esc(c['doi'])}</a></p>
      <p class="cite__note">{rich(c['note'])}</p>
    </div>""" for c in site["publication"])
    background = "".join(f"""
      <li>
        <p class="time__when">{esc(b['when'])}</p>
        <p class="time__what">{esc(b['what'])}</p>
        <p class="time__detail">{rich(b['detail'])}</p>
      </li>""" for b in site["background"])
    elsewhere = "".join(f'\n        <li><a href="{esc(e["href"])}">{esc(e["label"])}</a></li>' for e in site["elsewhere"])

    return f"""<!doctype html>
<!-- Generated by build.py from content/site.toml. Edit those, not this file. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta['title'])}</title>
<meta name="description" content="{esc(meta['description'])}">
<meta name="author" content="{esc(me['name'])}">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#090807">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:site_name" content="{esc(meta['title'])}">
<meta property="og:title" content="{esc(meta['title'])}">
<meta property="og:description" content="{esc(meta['og_description'])}">
<meta property="og:image" content="{esc(url + meta['og_image'])}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(meta['title'])}">
<meta name="twitter:description" content="{esc(meta['og_description'])}">
<meta name="twitter:image" content="{esc(url + meta['og_image'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{esc(FONTS)}">
<link rel="stylesheet" href="styles.css?v={css}">
<script type="application/ld+json">
{person_schema(site)}
</script>
</head>
<body>
<a class="skip" href="#work">Skip to the work</a>

<header class="bar">
  <div class="wrap bar__in">
    <a class="bar__name" href="#top">{esc(me['name'])}</a>
    <nav aria-label="Sections">
      <a href="#work">Work</a>
      <a href="#more">More</a>
      <a href="#publication">Paper</a>
      <a href="#background">Background</a>
      <a href="#contact">Contact</a>
    </nav>
    <a class="bar__cv" href="{esc(me['cv'])}">CV <span>PDF</span></a>
  </div>
</header>

<main id="top">

<section class="hero wrap">
  <h1>{esc(me['headline'])}</h1>
  <div class="hero__cols">
    <div class="hero__text">
      <p class="lead">{rich(me['intro'])}</p>
      <p class="avail">{rich(me['availability'])}</p>
      <p class="actions">
        <a class="btn" href="{esc(me['cv'])}">Download CV</a>
        <a href="mailto:{esc(me['email'])}">{esc(me['email'])}</a>
      </p>
    </div>
    <dl class="kv hero__facts">
        {facts(site['fact'])}
    </dl>
  </div>
</section>

<figure class="band">
  <div class="band__axis" aria-hidden="true">
    <span class="band__low">{esc(band['low'])}</span>
    <span class="band__mark" style="left:{band['mark_at']}%">{esc(band['mark'])}<i>, {esc(band['mark_note'])}</i></span>
    <span class="band__high">{esc(band['high'])}</span>
  </div>
  <img class="band__img" src="{esc(band['src'])}" width="{bw}" height="{bh}" alt="{esc(band['alt'])}">
  <figcaption class="wrap"><span>{rich(band['caption'])}</span></figcaption>
</figure>

<section class="section wrap" id="work">
  <h2 class="vh">Selected work</h2>{selected}
</section>

<section class="section wrap" id="more">
  <div class="section__head">
    <h2 class="label">More work</h2>
  </div>
  <div class="ledger">{ledger}
  </div>
</section>

<section class="section wrap" id="publication">
  <div class="section__head">
    <h2 class="label">Publication</h2>
  </div>{pubs}
</section>

<section class="section wrap" id="background">
  <div class="section__head">
    <h2 class="label">Background</h2>
  </div>
  <ul class="time">{background}
  </ul>
</section>

<section class="section wrap" id="skills">
  <div class="section__head">
    <h2 class="label">Tools and methods</h2>
  </div>
  <dl class="kv skills">
        {facts(site['skill'])}
  </dl>
</section>

</main>

<footer class="foot" id="contact">
  <div class="wrap">
    <h2 class="label">Contact</h2>
    <a class="foot__mail" href="mailto:{esc(me['email'])}">{esc(me['email'])}</a>
    <p class="foot__avail">{rich(me['availability'])}</p>
    <ul class="foot__links">
        <li><a href="{esc(me['cv'])}">CV (PDF)</a></li>{elsewhere}
        <li><a href="mailto:{esc(me['email_personal'])}">{esc(me['email_personal'])}</a></li>
    </ul>
    <p class="foot__meta"><span>{esc(me['location'])}</span><span>Facts last checked {long_date(checked)}</span></p>
  </div>
</footer>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    site = tomllib.loads(CONTENT.read_text(encoding="utf-8"))
    validate(site)
    print(f"{len(site['project'])} projects")
    if freshness(site["project"], dt.date.today()):
        print("not written: re-check the blocked projects and update `checked`")
        return 1
    built = page(site)
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != built:
            print("index.html is out of date: run python3 build.py")
            return 1
        print("index.html is up to date")
        return 0
    OUT.write_text(built, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(built.encode()) / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
