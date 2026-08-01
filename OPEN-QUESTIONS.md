# Open Questions

Dilemmas surfaced during autonomous sessions that need an owner call. Tracked
and linked from [README.md](README.md) per root Rule #18/CLAUDE.md.

## 2026-08-02 — Docs migration to MD-First 2.0 + enforcement layer

Autonomous overnight session (root MIGRATE-DOCS.md). Nothing here blocked
completion — everything below is FYI / a judgment call made in the session's
favor, surfaced for the owner to overturn if wrong.

### Real code bug found, NOT fixed (zero-behavior-change constraint)

`preview3d/light/view.py`, method `step_orientation` (around line 294) calls
`orientations.step_orientation(...)`, but `orientations` is never imported
anywhere in `view.py`. Calling `Preview3DLightWidget.step_orientation()` will
raise `NameError: name 'orientations' is not defined` — verified by reading
the file's import block, which pulls `switcher`, `directions.parse_direction`,
`resources.load_shared_spec`, `model_view`, `scene`, `animation`, `camera`,
`primitives.build_primitive`, `renderer`, and `scene.Node`, but not
`orientations`. `set_orientation()` (used for the "Upright" button and direct
orientation picks) does not go through this path and works fine — only the
step-by-one auto-advance path (the demo's `−` / `+` orientation buttons) is
broken. This is a pre-existing defect, unrelated to the docs migration; this
session's brief was zero behavior change, so it was documented rather than
fixed. **Needs an owner call**: fix directly (add the import), or treat as a
dedicated bug-fix session with its own regression test per Rule #25.

### Structure-law "smell" band files noticed, not acted on

Three files sit in the 500–1,000 line "Smell" band (root CODE.md's Structure
Law clause 2 — not a Violation, so the guard does not fail on them, but the
rule asks the question in writing): `demoapp/window.py` (600 lines),
`preview3d/light/view.py` (600 lines), `src/viewer.js` (912 lines). All three
were read in full during this session for doc-accuracy verification, and each
already reads as ONE cohesive responsibility (the window shell / the LIGHT
widget shell / the WEB viewer orchestrator) rather than an accretion of
unrelated concerns — so the working answer to "does this file hold more than
one responsibility?" is "no, but it is the single most complex file in its
folder." Splitting is out of scope for a docs-migration session (root
MIGRATE-DOCS.md Hard Constraint #1: zero code behavior change) and is a
separate task per REFACTOR-GODFILES.md if the owner wants it pursued.

### CONFIG_FILES seed left intentionally small

`tests/test_config_sections.py`'s `CONFIG_FILES` seeds 4 files
(`demoapp/theme.py`, `demoapp/window.py`, `preview3d/switcher.py`,
`src/switcher.js`) rather than every file with any module-level dict. Files
like `preview3d/light/primitives.py` / `src/primitives.js` and
`preview3d/light/animation.py` / `src/animation.js` have a few small
`*_DEFAULTS` tables but are otherwise Algorithmic files (parametric geometry
builders, timeline evaluation) — root CODE.md's own scope note warns against
forcing banner coverage across dozens of unrelated algorithm functions for
one small table. This is a judgment call, not a hard rule reading; the owner
may want a wider seed in a follow-up session as more tables prove out real
edit-time risk.
