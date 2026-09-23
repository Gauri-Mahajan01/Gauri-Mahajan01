"""Draw the README's section headings as SVGs.

GitHub strips CSS from READMEs, so an image is the only way to put the
page's own typeface and palette on a heading.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from theme import AMBER, CELL_W, MELT, RAMP, SLATE, SVG_CLOSE, glyph_row, svg_open  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent

# Section names, in README order. Keep them lowercase and plain — the
# decoration carries the personality, the words carry the meaning.
HEADINGS = [
    ("about", "about"),
    ("stack", "stack"),
    ("projects", "projects"),
    ("stats", "stats"),
]

H = 34
PAD_X = 2


def heading(label: str, title: str) -> str:
    text_w = len(label) * CELL_W
    # A short ice-ramp rule trailing the label: dense next to the word,
    # thinning out to open water. Same ramp as the hero field.
    tail = list(reversed(RAMP.strip()))
    tail_x = PAD_X + text_w + CELL_W * 1.5
    width = int(tail_x + len(tail) * CELL_W + 8)

    parts = [svg_open(width, H, title)]
    parts.append(
        f'<text x="{PAD_X}" y="22" class="fg" font-family="'
        f'ui-monospace, \'JetBrains Mono\', Menlo, Consolas, monospace" '
        f'font-size="15" font-weight="700" letter-spacing="0.5">{label}</text>'
    )
    for i, ch in enumerate(tail):
        parts.append(
            glyph_row([ch], tail_x + i * CELL_W, 22, MELT, size=13,
                      opacity=round(0.85 - i * 0.11, 2))
        )
    parts.append(SVG_CLOSE)
    return "".join(parts)


def main() -> None:
    for name, title in HEADINGS:
        path = OUT / f"hd-{name}.svg"
        path.write_text(heading(name.replace("-", " "), title), encoding="utf-8")
        print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
