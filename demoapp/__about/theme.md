# Theme

**Script:** [Theme (script)](../theme.py)

## Purpose

Single source for every colour, radius and spacing value the demo app uses
(root Rule #4 — no component elsewhere hardcodes a literal), plus the
function that turns those tokens into the application's QSS stylesheet.
DESIGN.md dark surfaces with one indigo accent.

## Connections

### Uses
- [Assets (folder)](../../assets/___assets.md) — `FONT_FILE` points at the bundled Inter font

### Used by
- the demo entry point (`main.py`) — registers `FONT_FILE`, applies `build_qss(THEME)` as the application stylesheet
- [Demo Window](window.md), [Model Panel](model_panel.md), [Parts Panel](parts_panel.md) — read `THEME` tokens directly for spacing and colours

## Module Contents

- `FONT_FILE` — path to the bundled `assets/fonts/Inter.ttf`
- `THEME: dict` — surfaces, borders, text colours, the accent pair, radii and spacing units
- `build_qss(theme: dict) -> str` — formats `THEME` into the full QSS stylesheet string (widget backgrounds, labels, cards, buttons, checkboxes, sliders, scroll areas)

One non-obvious rule inside the generated QSS: `QLabel { background: transparent; }`. A bare `QWidget { background: … }` rule is inherited by every `QLabel`, which then paints the window surface over whatever card it sits on — this line neutralises that (see [CLAUDE.md](../../CLAUDE.md) "Known Traps").

## Design Decisions

- **Inter is bundled, not assumed.** DESIGN.md forbids shipping the system default (Segoe) as the primary typeface, and none of the DESIGN.md typefaces are installed on a stock Windows machine — the font file travels with the project and `main.py` registers it at startup, with a logged error if that fails (root Rule #1).
