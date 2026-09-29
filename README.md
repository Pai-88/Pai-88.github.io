# paingheinhtet.com

Source for [paingheinhtet.com](https://paingheinhtet.com), served by GitHub Pages. One static page, no JavaScript.

## How it is built

Everything the page says lives in [`content/site.toml`](content/site.toml). [`build.py`](build.py) turns that file into `index.html`, and [`styles.css`](styles.css) styles it. The build needs Python 3.11 or newer and nothing else.

```bash
python3 build.py
```

```bash
python3 build.py --check
```

The second form changes nothing and exits 1 if `index.html` is not what the content file would produce.

To add or change a project, edit its `[[project]]` block, set `checked` to the date you compared its facts against the repo, and build. The build refuses a block with a missing field, a figure that does not exist, an image without alt text, or an em dash in the copy.

## Freshness

Each project block carries `checked`, the date its claims were last compared against the project itself. `staleness()` in `build.py` decides what the build does with an old one: publish, publish with a reminder, or refuse to write the page. The default only reminds after 30 days. Things to weigh when changing it:

- Hardware moves fastest. "Not yet flown" is wrong the day after a first hover, so blocks measured on real hardware may deserve the shortest leash.
- A published preprint does not change, so a long leash there costs nothing.
- Blocking is the only setting that cannot be ignored, but it also stops an unrelated fix from going out until every block is re-checked.

## Figures

| File | Made by | From |
|:--|:--|:--|
| `assets/img/pallorhb_stripes.png` | `tools/make_stripes.py` | colour statistics of the CP-AnemiC photographs, via the `pallor-hb` checkout |
| `assets/img/board_*.webp` | `tools/render_boards.sh`, then `tools/make_images.py` | the KiCad boards, rendered with one camera |
| `assets/img/*.webp` (the rest) | `tools/make_images.py` | figures from each project |
| `assets/og.png` | `tools/make_og.py` | the headline in `content/site.toml` |

The tools read the project folders that sit next to this one and never write to them.

## Licences of borrowed images

- Conjunctiva photographs in `pallorhb_pair.webp`: CP-AnemiC dataset (Asare, Mendeley Data), CC BY 4.0.
- The match frame in `ttscout_clip.webp` and everything under `tt-scout/`: OpenTTGames (OSAI), CC BY-NC-SA 4.0. `tt-scout/` is an example TT-Scout match report built from that dataset, credited on the page.
