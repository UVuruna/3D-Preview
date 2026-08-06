# CLAUDE.md — 3D Preview

Inherits all rules from the root `CLAUDE.md` constitution — read it and the
`Router` table there first to load only the rulebooks (`rules/CODE.md`,
`rules/DOCS.md`, `rules/GUI.md`, `rules/SHIP.md`, `rules/PLAN.md`,
`rules/START.md`) your job this session actually needs. Project-specific
guidance below — no root rule is restated here.

## What This Is

An embeddable 3D viewer **component** (library, not an installable app) with **two interchangeable renderers** — see [RENDERERS.md](RENDERERS.md):

- **WEB** — a Three.js core bundled by esbuild, used by websites via a script tag and by Qt apps through `Preview3DWidget` (QWebEngineView).
- **LIGHT** — `Preview3DLightWidget`, software 3D drawn with QPainter: no browser engine, no GPU, no file loading.

**Because it is a library, the installable-app pipeline does not apply:** no `setup/` folder, no NSIS build, no Rule #23 self-update, no Rule #24 auto-release of installers. Consumers take the committed `web/preview3d.min.js` or `pip install git+` the repo.

The stack question raised by [PLAN.md](PLAN.md) — which commissioned QPainter software 3D and rejected QWebEngine on installer weight — was **settled by the owner on 2026-07-28: build both.** Neither renderer supersedes the other; a consumer picks by what it needs.

## Ground Rules

- **A capability lands in BOTH renderers, or its absence is documented.** Two implementations of one component is a standing drift risk (Rule #5). When you add something to one, either add it to the other or record it in RENDERERS.md's "only" lists — an undocumented difference is a bug.
- **Values both renderers must agree on live in `shared/spec.json`** — palette, face order, view presets, camera defaults. The JS core imports it at build time, Python reads it at run time. Never restate one of those values in either source; a parity test fails if you do.
- **The WEB renderer's display logic lives in `src/`.** `preview3d/widget.py` only marshals calls (JSON specs, base64 model bytes) — never add rendering behaviour to it.
- **The LIGHT renderer keeps its geometry Qt-free.** `vectors`, `scene`, `primitives` and `camera` import no Qt, so they can be tested without a GUI; only `renderer.py` and `view.py` touch it.
- **Primitives are computed (root Rule #19).** New simple shapes are added as parametric builders in `src/primitives.js` — never as stored model files. `exportGLB()` exists for the rare case a real file is needed.
- **Animation scenes are DATA, and only ever drive flat parameters.** A scene is a JSON descriptor in `shared/scenes.json` (or a consumer's own data) — keyframes over the channels in `shared/spec.json`. If a scene needs an engine change, the missing piece is a CHANNEL, added to both renderers; never hardcode choreography in either. See [SCENES.md](SCENES.md).
- **Every builder names its children.** An unnamed node cannot be addressed by the parts API and shows up as `Mesh#3` in a host's UI — see [MODELS.md](MODELS.md).
- **`web/preview3d.min.js` is a build artifact that IS committed** — consumers must not need Node. After ANY change in `src/`, run `npm run build` and commit the refreshed bundle together with the source change.
- **JS API and Python API move together.** A new JS Viewer method gets its snake_case mirror in `preview3d/widget.py` AND in `preview3d/light/view.py` in the same session, and all three docs are updated.
- **Content first, scene second.** `show_scene` / `show_axes` / `load_model` CLEAR any loaded animation in both renderers, because a scene addresses the parts of specific content. Do not "helpfully" keep the scene across a content swap — that is how a timeline ends up driving a path that no longer exists, and failing from inside `show_scene` where the host can do nothing about it.

## Commands

```bash
npm install               # once
npm run build             # src/ → web/preview3d.min.js
python main.py            # the demo app
python -m pytest tests/   # regression pins
```

## Verification Recipe

Rendering claims require screenshots or measurements (root Guideline #1):

- **Web:** Playwright headless — open `demo/index.html`, wait ~1.5 s, screenshot, assert no console errors.
- **Demo app:** import `demoapp.window`, build `DemoWindow`, then `QTimer.singleShot(4000, …)` and capture with `app.primaryScreen().grabWindow(0, *window.frameGeometry())`. Grab the **screen region**, not `widget.grab()` — a nested web view composites separately and a widget grab of the window comes back without the 3D content. An occasional all-white stage in a screen grab is a compositor transient right after a resize, not a bug; re-sample before chasing it.
- **Controls:** Playwright on the demo page — read `viewer.camera.position` and `viewer.controls.target`, drag/wheel, read again. Rotation must move the camera while leaving the orbit distance unchanged; the wheel must shrink it.
- **Model loading:** `viewer.exportGLB()` in the browser writes a real `.glb`; feed that file to `Preview3DWidget.load_model()` and screenshot — one test covers both file paths.
- **Framing / geometry:** measure the rendered silhouette from pixels rather than trusting the look. The regular-hexagon claim is pinned that way: render a plain cube at `iso` in both projections, find the silhouette's corner radii from the centroid, and check the spread (orthographic ≈ 1.00x, perspective ≈ 1.27x at fov 45).
- **Animation:** never claim "it plays" from a screenshot — a still frame cannot show motion. Connect `camera_changed`, sample the reported azimuth ~1 s apart while a scene runs (it must move), then press pause and sample again (it must not), and step one frame (the frame counter must go up by exactly 1). Do it in BOTH renderers. `tests/test_animation_parity.py` covers the evaluated instants; this covers the clock actually running.

JS console output is forwarded to Python `logging` by the widget, so JS errors surface in the host app's log (Rule #1).

## Known Traps

- **QtWebEngine drops JS arrays in `runJavaScript` results.** An array of three strings arrives in Python as an **empty string**, with no error anywhere — it looks exactly like "there was nothing to return". Every structured result therefore crosses as `JSON.stringify(...)` and is decoded in Python (`_run_json`). Do not "simplify" it away.
- **The page reports camera state before `loadFinished` reaches Python.** A host reacting to that first signal would call into a widget that still says it is not ready, so queued calls keep their callbacks and are answered late instead of refused.
- **Framing measures vertices, not bounds.** `fitView()` walks real geometry because a bounding box or sphere frames star-shaped content (the axes gizmo) at ~55% of the space it should fill, and because the aggregate `halfDepth + halfHeight/tan` formula assumes the widest point is the nearest — which for anything viewed corner-on it is not. Do not reduce it to `Box3`/`getBoundingSphere`.
- **A `QHBoxLayout` reports the SUM of its items as its minimum width.** One unwrappable row of eight legend chips set a 1649 px minimum on the demo window — wider than half the owner's screen. Anything strip-like uses `demoapp/flow_layout.py`, and nothing inside the window may dictate a large floor; pinned by `tests/test_window_minimum_size.py`.
- **Use OrbitControls' `start` event, not `change`, to detect that the USER moved the camera.** Damping raises `change` for a frame or two after a programmatic move, so `change` marks the view as the user's the instant the viewer frames it itself — which then suppresses re-framing on resize.
- **QSS `QWidget { background: … }` leaks into every `QLabel`**, which then paints the window surface over whatever card it sits on. `demoapp/theme.py` neutralises it with an explicit `QLabel { background: transparent; }`.
- **A translucent part must stop writing depth**, or it hides what is inside it — handled in `parts.js`, and the reason cube faces are separate double-sided meshes rather than one box mesh.
- **`QWebEnginePage`'s background defaults to OPAQUE WHITE.** With the host page's `html`, `body` and container all transparent, that white sheet sits behind everything and shows in any frame the canvas is not painted — which a resize guarantees. The viewer reports the colour it clears to and the widget paints the page surface to match; pinned by `tests/test_background_flash.py`. Do not "simplify" the container background away either — it is the in-page half of the same fix.
- **A vertex behind the eye is not "off screen" without a near-plane guard.** The LIGHT renderer's perspective divide is a plain `x / depth`; for a negative or near-zero `depth` that produces a **mirrored, garbled polygon** rather than nothing, because nothing before M3 (the Blindness view's first-person dolly) ever placed the camera near its own content. Three.js clips at its camera's near plane in hardware, so only the LIGHT side needed `NEAR_CULL` in `renderer.py` (cull the WHOLE face/line if ANY point is at or behind it, not only when all are) — this is not a capability the web renderer lacks, just one it already had for free.

## Consumers

- **DOMY Watch** — the Character Cube in its Encyclopedia. See [PLAN.md](PLAN.md) for the full brief, with one owner correction (2026-07-28): the previewer is **a container dropped in where the topic's image used to sit**, and nothing more. PLAN.md's hover-card and click-to-navigate contract is **not** wanted — do not build raycast picking for it. The viewer reports which page it is on by being on that page.
- **Vaske Komarnici** (planned) — parametric window-screen preview; the `screen` primitive does not exist yet and should be designed against that site's product configurator when integration starts.

## Layout Teeth — pending migration (2026-08-06)

This project has a GUI and has NOT yet run the layout migration. Any GUI
work here follows [MIGRATE-LAYOUT.md](../../MIGRATE-LAYOUT.md) +
[GUI Rules](../../rules/GUI.md): the machine-wide layout guard already
bites in every session; what this project still owes is the per-project
audit — window registry, computed minimums fitting 1280x720, screenshots
opened and graded >= 8/10. Reference implementations: Remote User
(tests/test_layout_audit_qt.py) and DOMY Watch (tests/test_layout_audit.py).
