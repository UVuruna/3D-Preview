# tests/

Regression tests. Each file pins a specific defect so no future change can silently reintroduce it (FIXED = VERIFIED (root CLAUDE.md Law #5)).

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
Not a bug pin but a **drift guard**: two rendering implementations of one component is a standing invitation to diverge (No Duplicate Code (rules/CODE.md)). The same scene specs go into both widgets and everything a host can observe is compared — part paths, initial visibility, `show_only`, opacity isolation, framing and camera state — plus an assertion that neither source restates a pole colour instead of reading `shared/spec.json`.

It deliberately does **not** compare pixels. The renderers are meant to look different (real materials versus flat shading), and pinning appearance would forbid either from improving. See [The Two Renderers](../RENDERERS.md).

### `test_animation_parity.py` — A Scene Must Play the Same in Both
The timeline is the one piece of the component that genuinely exists **twice, in two languages** — `src/animation.js` and `preview3d/light/animation.py`. Everything else either reads `shared/spec.json` or is renderer-specific by design, so this is where drift would actually happen: an easing curve rounded differently, a key boundary resolved on the other side, a bool interpolating in one language and stepping in the other.

These are PLAN.md's golden tests made concrete. Every shipped scene is driven to **t = 0, ½ and 1** in both renderers and the observable result compared: camera angles, projection, framing, per-part visibility and opacity, the frame counter. Plus: the easing curves are sampled through both implementations and compared numerically; both must read the frame rate, speeds and channel table from `shared/spec.json`; instant mode must equal seeking to the end; and the transport must be inert rather than raise when no scene is loaded.

**It found a real one on its first run:** the cube's wireframe was drawn at 0.35 opacity by the web core (hardcoded in the line material) and at 1.0 by the LIGHT one, which then applied a separate ×0.45 at paint time — two renderers reporting different opacity for the same part. The value now lives in `shared/spec.json` as `neutral.edgeOpacity` and both read it.

### `test_axis_geometry.py` — ANGLE EXACTNESS

The reason this component exists: a flat wheel cannot show an edge axis at its real angle, and an axis drawn at an approximated angle would look plausible and teach the wrong thing. Every direction's dot products are pinned — edge axes at exactly 45° to each of their two parent poles and 90° to the third, body diagonals at exactly `acos(1/√3)` to all three of theirs — together with the token grammar's refusals and **golden screen projections**: under the isometric orthographic camera the six primary arms land exactly 30° apart at one radius, and `+x+y+z` projects to the exact centre.

Guards the gap that made M2 necessary: the direction table used to be six hardcoded entries in each renderer, so the cube's six edge axes and four vertex diagonals could not be expressed at all.

### `test_axis_colors.py` — The Computed Palette and the Collision Rule

Colours are derived from the pole hues by four rules, never enumerated (owner decree 2026-07-28). These pin the arithmetic, the golden hexes, and the collision rule with teeth: **the plain blends really do collide** (the worst, `+x+y-z`, lands 15 units from the orange pole) and the dressed ones clear the threshold by more than four times. The verifier itself is checked by being made to fail. A test also fails the build if either language hardcodes a derived hex instead of computing it.

### `test_orientations.py` — Snap Views and the 24 Orientations

The 24 orientations are computed from 6 up-faces × 4 spins. The thing that would silently go wrong is a **reflection passing for a rotation** — the cube comes back mirrored and a screenshot looks perfectly fine — so every one is checked for orthonormality and determinant +1, all 24 for distinctness, and each for putting the named face where it says. Plus the snap views, including the perpendicular-to-the-sacred-axis direction the tertiary view uses.

### `test_model_schema.py` — What a Consumer's Exporter Is Held To

PLAN.md promised one renderer-neutral schema and that "the demo model and DOMY's exported model both validate". DOMY generates its model from its canon, so the failure guarded here is a field that is quietly wrong in generated data and surfaces three screens later as a missing label. Twelve kinds of breakage are each required to fail **with the path of the offending field**, and a model carrying fewer registers is held to exactly those.

### `test_model_parity.py` — The Model Layer, in Two Languages and Two Renderers

The model layer exists twice for the reason the timeline does. Two levels of pin:

1. **Data parity** — the JS model layer is run head to head with the Python one and their OUTPUT compared exactly: the computed palette, the whole model, the scene spec it becomes, and the 24 orientations. The strongest check the component has, because the answer here is a value rather than a picture. Needs Node only to run the JS at all, and skips without it.
2. **Renderer parity** — the same model goes into both widgets: part paths, per-part **colour**, the Switcher's effect, each owner view's opacities, and that other content drops the model in both.

**It found a real one on its first run:** a group's opacity was reported as 1 by the web core and as the set value by the LIGHT one, because the web core pushed the value straight onto every descendant's material. Opacity now multiplies down in both, and a part reports its OWN — which also means re-lighting one child can no longer escape its group's dimming.

### `test_structure_law.py` — The God-File Ratchet

Root `CLAUDE.md` Priority S / `rules/CODE.md`'s THE STRUCTURE LAW. Fails the build when any `.py` or `.js` source crosses ~1,000 lines outside a named ratchet allowlist that may only shrink. The ratchet carries exactly ONE entry — `web/preview3d.min.js`, the esbuild bundle of `src/`, counted (not directory-excluded) and ratcheted with remedy "none — regenerated by `npm run build`". Both languages are counted.

### `test_config_sections.py` — THE CONFIG SECTION LAW

Fails the build when a file listed in its `CONFIG_FILES` seed (`demoapp/theme.py`, `demoapp/window.py`, `preview3d/switcher.py`, `src/switcher.js`) has a top-level definition before its first section banner, a duplicate dict/object key, or a module-level statement that patches an earlier-defined table (`TABLE[...] = ...`, `.update()`, `.push()`, …) instead of editing the table's own definition in place. Python files are checked exactly via `ast`; JS files via a narrower, honestly-documented regex/brace heuristic (see the test's own module docstring for the exact ceiling).

### `test_docs_coverage.py` — MD-First 2.0 Tier Coverage

Fails the build when a source file lacks the docs its TIER requires (root `rules/DOCS.md`'s Tiers table: Trivial → none, Standard → `__about/`, Algorithmic → `__about/` **and** `__flow/`), when a Standard-tier file has an unearned `__flow/` doc, when any `.py`/`.js` file has no tier entry, when a `TIERS` entry is stale, or when an `__about/`/`__flow/` doc is orphaned (its source file renamed or deleted). `TIERS` is this project's single source of truth for every file's tier — changing a tier means editing this test in the same commit.

### `test_doc_links.py` — The Navigation Chain

Fails the build when any project `.md` is unreachable from `README.md` by following links, or when any relative link inside a project `.md` resolves to a file that does not exist. Links that escape the project root (monorepo-root references, written as plain backtick text per `rules/DOCS.md`) are outside this guard's jurisdiction and are skipped rather than asserted.

### `run_guards.py` — The Hook Wrapper

Not a test module — a small runner `.claude/settings.json`'s hooks call. `python tests/run_guards.py --fast` (PostToolUse: structure law + config sections only, fast-exits before importing `pytest` for a non-`.py`/`.js` edit) and `python tests/run_guards.py` (Stop: all four guards) both exit **2** on failure, which is what makes a hook BLOCKING.

## Connections

### Uses
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — the widget under test
- [Demo App (folder)](../demoapp/___demoapp.md) — `theme.py` / `window.py`, seeded in `test_config_sections.py`
- [Source (folder)](../src/___src.md) — `switcher.js`, seeded in `test_config_sections.py`
- Every project `.md` and every project `.py`/`.js` file — walked by the four guards

## Design Decisions

- **Deterministic assertions over timing races.** A test that must catch a one-frame artifact on camera fails at random and gets deleted; a test that asserts the cause holds forever.
- **A test is only a pin once it has been seen to fail.** Every regression test here is checked against the broken code before being committed, and the result is recorded above. The four guard tests follow the same discipline via the "guard self-test rule" (root `rules/CODE.md`): each was shown failing on a planted violation, then passing, before being trusted.
