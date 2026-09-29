#!/bin/sh
# Render every board with one camera, on a transparent ground, into tools/renders/.
# Reads the KiCad projects next to this checkout and never writes to them.
#
#     sh tools/render_boards.sh && python3 tools/make_images.py
#
# The zoom per board is the largest that keeps the whole outline inside the frame.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
docs=$(cd "$here/../.." && pwd)
kicad=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
mkdir -p "$here/renders"

render() {  # name  board  zoom
  "$kicad" pcb render --output "$here/renders/$1.png" \
    --width 2200 --height 1700 --background transparent --quality high \
    --perspective --rotate "-38,0,30" --zoom "$3" "$docs/$2" >/dev/null
  echo "rendered $1"
}

render pursuit pursuit_drone/hardware/pursuit.kicad_pcb        0.62
render pbr     algae_pbr/hardware/pbr-board/pbr-board.kicad_pcb 0.74
render emg     emg_hand/board/revd/kicad/emg.kicad_pcb          0.66
render eit16   eit/hardware/eit-16ch/eit-16ch.kicad_pcb         0.66
