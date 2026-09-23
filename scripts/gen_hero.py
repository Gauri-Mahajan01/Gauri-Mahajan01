"""Hero graphic: a Southern Ocean sea-ice field pushed through a character ramp.

The reference this borrows its technique from uses a photo portrait. A face
says nothing about the work; a marginal ice zone with a route threaded
through it says all of it. The field is procedural and deterministic, so the
graphic is reproducible and commits cleanly — it is an illustration of the
domain, not real forecast output, and the colophon says so.
"""

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from theme import (  # noqa: E402
    AMBER, CELL_H, CELL_W, MONO, RAMP, SLATE, SVG_CLOSE, esc, glyph_row,
    shade_style, svg_open,
)

OUT = pathlib.Path(__file__).resolve().parent.parent

COLS, ROWS = 84, 21
PAD_X, PAD_Y = 4, 26

NAME = "GAURI"
TAGLINE = "learning in public, one commit at a time"


def _hash(ix: int, iy: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + seed * 144665) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 0xFFFF


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def value_noise(x: float, y: float, seed: int) -> float:
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = _smooth(x - ix), _smooth(y - iy)
    a = _hash(ix, iy, seed)
    b = _hash(ix + 1, iy, seed)
    c = _hash(ix, iy + 1, seed)
    d = _hash(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x: float, y: float, seed: int = 7) -> float:
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for octave in range(4):
        total += amp * value_noise(x * freq, y * freq, seed + octave)
        norm += amp
        amp *= 0.5
        freq *= 2.1
    return total / norm


def concentration(col: int, row: int) -> float:
    """Ice concentration 0..1.

    A gentle latitudinal trend carries open water in the north to consolidated
    ice in the south, but the structure is mostly two-dimensional: floes drift
    north of the pack edge and leads open inside it. A purely row-wise gradient
    reads as a slab and says nothing about how this ice actually behaves.
    """
    v = row / (ROWS - 1)
    trend = 0.02 + 1.02 * v
    floes = (fbm(col / 15.0, row / 7.0, seed=7) - 0.5) * 1.15
    leads = (fbm(col / 6.0, row / 2.6, seed=19) - 0.5) * 0.38
    return min(1.0, max(0.0, trend + floes + leads))


ROUTE = [
    (0.10, 0.06, "learn"),
    (0.34, 0.16, None),
    (0.46, 0.34, "build"),
    (0.55, 0.52, None),
    (0.62, 0.68, None),
    (0.74, 0.83, "ship"),
]


def main() -> None:
    w = int(PAD_X * 2 + COLS * CELL_W)
    h = int(PAD_Y + ROWS * CELL_H + 40)
    parts = [svg_open(w, h, "A textured field with a path running through it",
                      extra_style=shade_style())]

    # Name and tagline sit above the field, left aligned to the grid.
    parts.append(
        f'<text x="{PAD_X}" y="17" class="fg" font-family="{MONO}" font-size="16" '
        f'font-weight="700" letter-spacing="3.5">{NAME}</text>'
    )

    # The field itself.
    for row in range(ROWS):
        y = PAD_Y + row * CELL_H + 11
        chars, shades = [], []
        for col in range(COLS):
            c = concentration(col, row)
            # Bias the quantisation so the heaviest glyph stays scarce; a wall
            # of solid ice carries no information.
            idx = min(len(RAMP) - 1, int((c ** 1.45) * len(RAMP)))
            chars.append(RAMP[idx])
            shades.append(idx)
        # Split the row into runs of equal shade so each run is one <text>.
        start = 0
        for i in range(1, COLS + 1):
            if i == COLS or shades[i] != shades[start]:
                idx = shades[start]
                if idx > 0:
                    parts.append(
                        glyph_row(chars[start:i], PAD_X + start * CELL_W, y,
                                  size=13, cls=f"s{idx}")
                    )
                start = i

    # The route: drawn over the field, the one thing in a non-ice colour.
    pts = [
        (PAD_X + fx * COLS * CELL_W, PAD_Y + fy * ROWS * CELL_H + 7)
        for fx, fy, _ in ROUTE
    ]
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(
        f"L {x:.1f} {y:.1f}" for x, y in pts[1:]
    )
    parts.append(
        f'<path d="{d}" fill="none" stroke="{AMBER}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-dasharray="3 4" opacity="0.9"/>'
    )

    # One orchestrated moment: a single marker running the route, slowly.
    parts.append(
        f'<circle r="3.2" fill="{AMBER}">'
        f'<animateMotion dur="14s" repeatCount="indefinite" path="{d}"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" dur="14s" '
        f'repeatCount="indefinite"/></circle>'
    )

    for (x, y), (_, _, label) in zip(pts, ROUTE):
        if not label:
            continue
        plate_w = len(label) * 6.3 + 8
        parts.append(
            f'<rect x="{x + 4:.1f}" y="{y - 7:.1f}" width="{plate_w:.1f}" '
            f'height="14" rx="2" class="bg" opacity="0.92"/>'
        )
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{AMBER}"/>')
        parts.append(
            f'<text x="{x + 8:.1f}" y="{y + 3.5:.1f}" fill="{AMBER}" '
            f'font-family="{MONO}" font-size="10.5">{esc(label)}</text>'
        )

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
