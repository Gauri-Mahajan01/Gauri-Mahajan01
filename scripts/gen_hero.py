"""Hero graphic: a UAV in flight over a scrolling character-ramp landscape.

Everything is drawn in the same glyph language as the rest of the profile.
The world scrolls in three parallax layers (far clouds, far ridge, near hills)
while the aircraft holds station, bobs, pitches and runs its pusher prop, so
the banner reads as flight without the aircraft ever leaving the frame.
Animation is SMIL only, which GitHub keeps when it serves an SVG as an image.
"""

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from theme import (  # noqa: E402
    AMBER, CELL_H, CELL_W, MELT, MONO, SLATE, SVG_CLOSE, esc, glyph_row,
    shade_style, svg_open,
)

OUT = pathlib.Path(__file__).resolve().parent.parent

COLS, ROWS = 84, 21
PAD_X, PAD_Y = 4, 26

NAME = "GAURI"
TAGLINE = "learning in public, one commit at a time"

SPAN = COLS * CELL_W  # one full period of every scrolling layer, in px


def _hash(ix: int, iy: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + seed * 144665) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 0xFFFF


def _wave(col: int, terms) -> float:
    """Sum of sines with whole-number cycles per period, so col 0 and col COLS
    meet exactly and the scroll loops without a seam."""
    return sum(a * math.sin(2 * math.pi * k * col / COLS + p) for a, k, p in terms)


def far_top(col: int) -> float:
    return 11.2 + _wave(col, [(2.0, 2, 0.5), (1.2, 5, 1.7), (0.5, 11, 0.2)])


def near_top(col: int) -> float:
    return 16.4 + _wave(col, [(1.3, 3, 2.0), (0.7, 7, 0.3), (0.3, 13, 1.1)])


CLOUDS = [  # (centre col, centre row, half-width, half-height)
    (8, 3.2, 9, 1.9), (33, 5.6, 11, 2.2), (54, 2.4, 8, 1.7), (72, 6.0, 10, 2.0),
]


def cloud_density(col: int, row: int) -> float:
    d = -1.0
    for cx, cy, rx, ry in CLOUDS:
        dx = min(abs(col - cx), COLS - abs(col - cx)) / rx  # wrap-around
        dy = (row - cy) / ry
        d = max(d, 1.0 - (dx * dx + dy * dy))
    return d + (_hash(col, row, 5) - 0.5) * 0.3


def row_runs(cells, y, x0):
    """cells: list of (char, shade) for one row. Emit one <text> per run."""
    out, start = [], 0
    for i in range(1, len(cells) + 1):
        if i == len(cells) or cells[i][1] != cells[start][1]:
            shade = cells[start][1]
            if shade:
                out.append(glyph_row([c for c, _ in cells[start:i]],
                                     x0 + start * CELL_W, y, size=13,
                                     cls=f"s{shade}"))
            start = i
    return out


def layer(cell_fn, rows, dur, extra=""):
    """A layer drawn twice side by side and slid left by one period, forever."""
    body = []
    for copy in (0, 1):
        x0 = PAD_X + copy * SPAN
        for row in rows:
            y = PAD_Y + row * CELL_H + 11
            body += row_runs([cell_fn(c, row) for c in range(COLS)], y, x0)
    return (
        f"<g>{extra}{''.join(body)}"
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 0" to="{-SPAN:.1f} 0" dur="{dur}s" repeatCount="indefinite"/></g>'
    )


def cloud_cell(col, row):
    d = cloud_density(col, row)
    if d < 0.05:
        return (" ", 0)
    if d < 0.35:
        return (".", 1)
    if d < 0.65:
        return (":", 1)
    return ("+", 2)


def far_cell(col, row):
    depth = row - far_top(col)
    if depth < 0:
        return (" ", 0)
    if depth < 1:
        return (".", 2)
    if depth < 2.5:
        return (":", 2)
    return ("+", 3)


def near_cell(col, row):
    depth = row - near_top(col) + (_hash(col, row, 11) - 0.5) * 0.8
    if depth < 0:
        return (" ", 0)
    if depth < 1:
        return ("+", 4)
    if depth < 2:
        return ("*", 5)
    if depth < 3:
        return ("#", 5)
    return ("@", 6)


def near_mask():
    """Background-coloured silhouette under the near hills, so the far ridge
    scrolling behind at a different speed never shows through them."""
    pts = []
    for copy in (0, 1):
        for c in range(COLS + 1):
            x = PAD_X + (copy * COLS + c) * CELL_W
            y = PAD_Y + (near_top(c % COLS) - 0.35) * CELL_H
            pts.append(f"{x:.1f},{y:.1f}")
    bottom = PAD_Y + ROWS * CELL_H + 4
    pts.append(f"{PAD_X + 2 * SPAN:.1f},{bottom:.1f}")
    pts.append(f"{PAD_X:.1f},{bottom:.1f}")
    return f'<polygon points="{" ".join(pts)}" class="bg"/>'


def speed_lines(w):
    out = []
    for i in range(7):
        y = PAD_Y + 18 + _hash(i, 1, 3) * CELL_H * 9
        x = w * _hash(i, 2, 3)
        ln = 18 + 30 * _hash(i, 3, 3)
        dur = 1.6 + 1.4 * _hash(i, 4, 3)
        out.append(
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + ln:.1f}" y2="{y:.1f}" '
            f'stroke="{MELT}" stroke-width="1" stroke-linecap="round" opacity="0.45">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{w * 0.4:.0f} 0" to="{-w * 0.9:.0f} 0" dur="{dur:.2f}s" '
            f'begin="-{dur * _hash(i, 5, 3):.2f}s" repeatCount="indefinite"/></line>'
        )
    return "".join(out)


def uav():
    """Fixed-wing UAV in three-quarter side view, nose right, pusher prop aft.
    Drawn around (0, 0); the caller places, bobs and pitches it."""
    p = []
    # Far wing, receding up and back: lighter, it is further away.
    p.append('<path d="M 4 -3 L -10 -19 L -17 -19 L -8 -3 Z" class="mut" opacity="0.7"/>')
    # Tail: V-tail, far fin lighter.
    p.append('<path d="M -40 -2 L -51 -13 L -46 -13 L -35 -2 Z" class="mut" opacity="0.7"/>')
    # Fuselage with the satcom bulge over the nose.
    p.append(
        '<path d="M -52 -1 L -44 -4 L 16 -5 C 30 -12 46 -9 52 -1 '
        'C 48 4 30 5 16 4 L -44 3 Z" class="fg"/>'
    )
    # Near wing, sweeping forward toward the viewer.
    p.append('<path d="M 6 1 L -16 27 L -8 27 L 14 1 Z" class="fg"/>')
    p.append('<path d="M -40 1 L -50 12 L -45 12 L -35 1 Z" class="fg"/>')
    # Chin sensor ball with a lens.
    p.append('<circle cx="30" cy="6" r="3.6" class="fg"/>')
    p.append(f'<circle cx="31.3" cy="6.6" r="1.3" fill="{MELT}"/>')
    # Pusher prop: a blur disc that flickers, plus the hub.
    p.append(
        f'<ellipse cx="-54" cy="0" rx="1.6" ry="10" fill="{MELT}" opacity="0.55">'
        '<animate attributeName="ry" values="10;3;10" dur="0.12s" repeatCount="indefinite"/>'
        '</ellipse>'
    )
    p.append('<circle cx="-53" cy="0" r="1.6" class="fg"/>')
    # Nav strobe on the near wingtip.
    p.append(
        f'<circle cx="-12" cy="27" r="1.8" fill="{AMBER}">'
        '<animate attributeName="opacity" values="1;0;0;1;0;0;0;0" dur="1.6s" '
        'repeatCount="indefinite"/></circle>'
    )
    return "".join(p)


def main() -> None:
    w = int(PAD_X * 2 + COLS * CELL_W)
    h = int(PAD_Y + ROWS * CELL_H + 40)
    parts = [svg_open(w, h, "A UAV flying over a scrolling landscape",
                      extra_style=shade_style())]
    parts.append(
        f'<defs><clipPath id="field"><rect x="{PAD_X}" y="{PAD_Y - 4}" '
        f'width="{SPAN:.1f}" height="{ROWS * CELL_H + 8}"/></clipPath></defs>'
    )

    parts.append(
        f'<text x="{PAD_X}" y="17" class="fg" font-family="{MONO}" font-size="16" '
        f'font-weight="700" letter-spacing="3.5">{NAME}</text>'
    )
    # Small HUD, top right.
    parts.append(
        f'<text x="{w - PAD_X - 64}" y="17" fill="{SLATE}" font-family="{MONO}" '
        f'font-size="10.5" text-anchor="end">alt 4.2 km · hdg 090</text>'
    )
    parts.append(
        f'<circle cx="{w - PAD_X - 50}" cy="13.5" r="3" fill="{AMBER}">'
        '<animate attributeName="opacity" values="1;0.15;1" dur="1.8s" '
        'repeatCount="indefinite"/></circle>'
    )
    parts.append(
        f'<text x="{w - PAD_X - 42}" y="17" fill="{AMBER}" font-family="{MONO}" '
        f'font-size="10.5">live</text>'
    )

    scene = [
        layer(cloud_cell, range(0, 9), 70),
        layer(far_cell, range(7, ROWS), 45),
        layer(near_cell, range(13, ROWS), 18, extra=near_mask()),
        speed_lines(w),
    ]

    # Aircraft: placed, then bobbing, then pitching in step with the bob.
    cx, cy = w * 0.42, PAD_Y + CELL_H * 6.5
    ground = PAD_Y + CELL_H * 16.0 - cy
    beam = (
        f'<polygon points="30,8 {-8},{ground:.0f} {70},{ground:.0f}" '
        f'fill="{AMBER}" opacity="0">'
        '<animate attributeName="opacity" values="0;0;0.16;0.16;0" '
        'keyTimes="0;0.35;0.45;0.8;1" dur="9s" repeatCount="indefinite"/></polygon>'
    )
    scene.append(
        f'<g transform="translate({cx:.1f} {cy:.1f})"><g>'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0; 26 -10; 52 3; 18 9; 0 0" keyTimes="0;0.25;0.5;0.75;1" '
        'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1" '
        'dur="12s" repeatCount="indefinite"/>'
        f"{beam}"
        '<g transform="scale(1.35)"><g>'
        '<animateTransform attributeName="transform" type="rotate" '
        'values="0; -4; 1.5; 3; 0" keyTimes="0;0.25;0.5;0.75;1" '
        'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1" '
        'dur="12s" repeatCount="indefinite"/>'
        f"{uav()}</g></g></g></g>"
    )

    parts.append(f'<g clip-path="url(#field)">{"".join(scene)}</g>')
    parts.append(
        f'<text x="{PAD_X}" y="{h - 12}" fill="{SLATE}" font-family="{MONO}" '
        f'font-size="11">{esc(TAGLINE)}</text>'
    )
    parts.append(SVG_CLOSE)

    path = OUT / "hero.svg"
    path.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {path.name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
