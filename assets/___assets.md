# assets/

Static files that travel with the project.

## Files

### `logo.svg` — Project Logo
The project mark: a three-armed axes gizmo (red / green / blue) on an orbit ring — the component's own subject matter. Also copied to the monorepo `logos/3DPreview.svg` for README and PROJECTS listings (root CLAUDE.md).

### `fonts/Inter.ttf` — Bundled UI Typeface
Inter variable font (weights 100–900), used by both faces of the project: the [Demo Application](../main.md) registers it with `QFontDatabase.addApplicationFont`, and the [Demo (folder)](../demo/___demo.md) page declares it through `@font-face`.

Bundled rather than assumed: DESIGN.md names Inter as the default UI typeface and forbids falling back to the system default (Segoe), and a stock Windows machine has none of the DESIGN.md typefaces installed.

### `fonts/OFL.txt` — Font License
SIL Open Font License 1.1 for Inter — required to accompany the font in any distribution.

## Connections

### Used by
- [Demo Application](../main.md) — loads the font at startup
- [Demo (folder)](../demo/___demo.md) — `@font-face` in the demo page
