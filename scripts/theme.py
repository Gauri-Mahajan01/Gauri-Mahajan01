"""Shared palette and SVG primitives.

Every graphic on the profile is drawn here rather than fetched from a
third-party badge service, so nothing can rate-limit or disappear.

Glyphs are positioned one at a time with an explicit x coordinate. That
removes the dependency on the viewer's default monospace advance width:
the grid holds even if the fallback font is narrower than JetBrains Mono.
"""

# Dusk palette: plum grounds, lavender accent, rose reserved for highlights.
ABYSS = "#1A1423"  # dark-mode ground
OCEAN = "#3D2C4E"  # deep plum
MELT = "#9B72D0"  # lavender, primary accent
ICE = "#D4B8F0"  # pale lilac
RIME = "#F7F2FA"  # light-mode ground
AMBER = "#E8637F"  # rose, highlights only
SLATE = "#8C7A9B"  # muted metadata

MONO = "ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace"

# Character ramp, quiet to loud. Reused by the hero field and the year strip
# so the two read as the same visual language.
RAMP = " .:+*#@"

CELL_W = 8.4
CELL_H = 15.0


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def glyph_row(chars, x0, y, fill=None, size=13.0, cell=CELL_W, opacity=None,
              cls=None):
    """Render one row of monospaced text as individually positioned glyphs."""
    xs = " ".join(f"{x0 + i * cell:.2f}" for i in range(len(chars)))
    op = f' opacity="{opacity}"' if opacity is not None else ""
    paint = f' class="{cls}"' if cls else f' fill="{fill}"'
    return (
        f'<text x="{xs}" y="{y:.2f}"{paint} font-family="{MONO}" '
        f'font-size="{size}"{op} xml:space="preserve">{esc("".join(chars))}</text>'
    )


# Concentration ramp, quiet to loud, in both schemes. GitHub serves the README
# on a light or a dark ground depending on the viewer, so a fixed fill would
# make one end of the ramp invisible. Index 0 is never drawn (open water).
SHADES_LIGHT = ["", "#E6DAF2", "#CDB6E6", "#AE8FD6", "#8C69BF", "#6A4A9E", "#4A2F75"]
SHADES_DARK = ["", "#3D2C4E", "#55406C", "#74599A", "#9A7BC4", "#C3A6E8", "#F0E6FA"]


def shade_style() -> str:
    light = "".join(f".s{i}{{fill:{c}}}" for i, c in enumerate(SHADES_LIGHT) if c)
    dark = "".join(f".s{i}{{fill:{c}}}" for i, c in enumerate(SHADES_DARK) if c)
    return light + "@media (prefers-color-scheme: dark){" + dark + "}"


def svg_open(w, h, title, extra_style=""):
    """Root element. The <style> block inside an SVG loaded as an <img> still
    honours prefers-color-scheme, which is the only theming lever left once
    GitHub has stripped CSS from the README itself."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title>"
        "<style>"
        f".bg{{fill:{RIME}}}.fg{{fill:{ABYSS}}}.mut{{fill:{SLATE}}}"
        "@media (prefers-color-scheme: dark){"
        f".bg{{fill:{ABYSS}}}.fg{{fill:{RIME}}}}}"
        f"{extra_style}"
        "</style>"
    )


SVG_CLOSE = "</svg>"
