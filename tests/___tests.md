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

### `test_window_minimum_size.py` — Demo Window Could Not Be Made Small
Pins the fix for the oversized window minimum reported 2026-07-28: the window refused to go below **1649 × 767**, wider than half of a 3072 px display.

**Root causes, both structural:** the keyboard legend was a `QHBoxLayout`, whose minimum is the **sum** of its items, so eight unwrappable chips demanded ~1250 px on their own; and the panel's sections were stacked unscrolled, setting a ~770 px floor on the height.

**Fix:** a wrapping [FlowLayout](../demoapp/___demoapp.md), the legend moved into the panel so it never competes with the 3D view for height, and one scroll area for the whole panel. Minimum is now 560 × 420.

**Verified as a real pin:** the width test fails against the pre-fix code with *"layout demands 1340 px of width"*. The stage-height test guards a second failure found while fixing the first (a wrapped legend under the stage squeezing the view to a thumbnail) and passes against the original code, which simply refused to get small at all — recorded in the test's own docstring rather than claimed as a pin for the reported bug.

### `test_renderer_parity.py` — The Two Renderers Must Agree
Not a bug pin but a **drift guard**: two rendering implementations of one component is a standing invitation to diverge (root Rule #5). The same scene specs go into both widgets and everything a host can observe is compared — part paths, initial visibility, `show_only`, opacity isolation, framing and camera state — plus an assertion that neither source restates a pole colour instead of reading `shared/spec.json`.

It deliberately does **not** compare pixels. The renderers are meant to look different (real materials versus flat shading), and pinning appearance would forbid either from improving. See [The Two Renderers](../RENDERERS.md).

### `test_animation_parity.py` — A Scene Must Play the Same in Both
The timeline is the one piece of the component that genuinely exists **twice, in two languages** — `src/animation.js` and `preview3d/light/animation.py`. Everything else either reads `shared/spec.json` or is renderer-specific by design, so this is where drift would actually happen: an easing curve rounded differently, a key boundary resolved on the other side, a bool interpolating in one language and stepping in the other.

These are PLAN.md's golden tests made concrete. Every shipped scene is driven to **t = 0, ½ and 1** in both renderers and the observable result compared: camera angles, projection, framing, per-part visibility and opacity, the frame counter. Plus: the easing curves are sampled through both implementations and compared numerically; both must read the frame rate, speeds and channel table from `shared/spec.json`; instant mode must equal seeking to the end; and the transport must be inert rather than raise when no scene is loaded.

**It found a real one on its first run:** the cube's wireframe was drawn at 0.35 opacity by the web core (hardcoded in the line material) and at 1.0 by the LIGHT one, which then applied a separate ×0.45 at paint time — two renderers reporting different opacity for the same part. The value now lives in `shared/spec.json` as `neutral.edgeOpacity` and both read it.

## Connections

### Uses
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — the widget under test

## Design Decisions

- **Deterministic assertions over timing races.** A test that must catch a one-frame artifact on camera fails at random and gets deleted; a test that asserts the cause holds forever.
- **A test is only a pin once it has been seen to fail.** Every regression test here is checked against the broken code before being committed, and the result is recorded above.
