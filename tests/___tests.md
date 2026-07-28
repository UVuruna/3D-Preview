# tests/

Regression tests. Each file pins a specific defect so no future change can silently reintroduce it (root Rule #25).

Run them all:

```bash
python -m pytest tests/ -q
```

## Files

### `test_background_flash.py` — White Flash on Resize
Pins the fix for the resize white-flash reported 2026-07-28.

**Root cause:** `QWebEnginePage`'s background defaults to **opaque white**, while the host page's `html`, `body` and container are all transparent. That white sheet therefore sat behind everything, and a resize clears the WebGL canvas backing store for at least one frame — so every resize showed it.

**Fix:** the viewer paints its container and reports the colour it clears to; the widget paints the Qt page surface to match (`_sync_background`). Transparent mode still yields a genuinely transparent surface.

**Why these assertions:** the tests check the **colour behind the canvas**, not a captured flash. The flash is a consequence of the colour, and a screen-grab race would be flaky — a programmatic resize does not reliably reproduce what an interactive drag does. Verified as a real pin: 3 of the 4 tests fail against the pre-fix code.

## Connections

### Uses
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — the widget under test

## Design Decisions

- **Deterministic assertions over timing races.** A test that must catch a one-frame artifact on camera fails at random and gets deleted; a test that asserts the cause holds forever.
- **A test is only a pin once it has been seen to fail.** Every regression test here is checked against the broken code before being committed, and the result is recorded above.
