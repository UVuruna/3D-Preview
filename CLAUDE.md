# CLAUDE.md — 3D Preview

Inherits all rules from the root [CLAUDE.md](../../CLAUDE.md). Project-specific guidance below.

## What This Is

An embeddable 3D viewer **component** (library, not an installable app): a Three.js core bundled by esbuild, consumed by websites (script tag) and by Python GUIs (PySide6 `Preview3DWidget` over `QWebEngineView`). See [README](README.md) for the stack rationale (Rule #21).

**Because it is a library, the installable-app pipeline does not apply:** no `setup/` folder, no NSIS build, no Rule #23 self-update, no Rule #24 auto-release of installers. Consumers take the committed `web/preview3d.min.js` or `pip install git+` the repo.

## Open Decision — Stack Divergence from PLAN.md

[PLAN.md](PLAN.md) is DOMY Watch's commissioning spec, written before this project existed. It specifies a **different stack**: software 3D drawn with QPainter, explicitly rejecting Three.js + QWebEngineView over QtWebEngine's installer weight for DOMY's build.

What actually got built is the web core, chosen by the owner in the founding session because the named consumers include a **website** (Vaske Komarnici) alongside DOMY. PLAN.md's own text sets that as the condition to revisit its decision: *"Revisit only if a future consumer is a WEBSITE."*

The installer-weight concern is real and unresolved. **Do not silently rewrite the stack in either direction** — it is the owner's call, and it is recorded here so no session has to rediscover the conflict. Everything else in PLAN.md (the data model, the four owner models, the switcher, the cinematic scenes, the milestones) is renderer-neutral by its own design and stands.

## Ground Rules

- **One rendering implementation.** All display logic lives in `src/`. The Python wrapper only marshals calls (JSON specs, base64 model bytes) — never add rendering behaviour on the Python side.
- **Primitives are computed (root Rule #19).** New simple shapes are added as parametric builders in `src/primitives.js` — never as stored model files. `exportGLB()` exists for the rare case a real file is needed.
- **Every builder names its children.** An unnamed node cannot be addressed by the parts API and shows up as `Mesh#3` in a host's UI — see [MODELS.md](MODELS.md).
- **`web/preview3d.min.js` is a build artifact that IS committed** — consumers must not need Node. After ANY change in `src/`, run `npm run build` and commit the refreshed bundle together with the source change.
- **JS API and Python API move together.** A new JS Viewer method gets its snake_case mirror in `preview3d/widget.py` in the same session, and both docs are updated.
- **The pole palette lives once**, in `src/primitives.js`. A host asks for `colors: 'poles'` or omits an arm's colour; it never restates the six hex values.

## Commands

```bash
npm install        # once
npm run build      # src/ → web/preview3d.min.js
python main.py     # the demo app
```

## Verification Recipe

Rendering claims require screenshots or measurements (root Guideline #1):

- **Web:** Playwright headless — open `demo/index.html`, wait ~1.5 s, screenshot, assert no console errors.
- **Demo app:** import `demoapp.window`, build `DemoWindow`, then `QTimer.singleShot(4000, …)` and capture with `app.primaryScreen().grabWindow(0, *window.frameGeometry())`. Grab the **screen region**, not `widget.grab()` — a nested web view composites separately and a widget grab of the window comes back without the 3D content. An occasional all-white stage in a screen grab is a compositor transient right after a resize, not a bug; re-sample before chasing it.
- **Controls:** Playwright on the demo page — read `viewer.camera.position` and `viewer.controls.target`, drag/wheel, read again. Rotation must move the camera while leaving the orbit distance unchanged; the wheel must shrink it.
- **Model loading:** `viewer.exportGLB()` in the browser writes a real `.glb`; feed that file to `Preview3DWidget.load_model()` and screenshot — one test covers both file paths.
- **Framing / geometry:** measure the rendered silhouette from pixels rather than trusting the look. The regular-hexagon claim is pinned that way: render a plain cube at `iso` in both projections, find the silhouette's corner radii from the centroid, and check the spread (orthographic ≈ 1.00x, perspective ≈ 1.27x at fov 45).

JS console output is forwarded to Python `logging` by the widget, so JS errors surface in the host app's log (Rule #1).

## Known Traps

- **QtWebEngine drops JS arrays in `runJavaScript` results.** An array of three strings arrives in Python as an **empty string**, with no error anywhere — it looks exactly like "there was nothing to return". Every structured result therefore crosses as `JSON.stringify(...)` and is decoded in Python (`_run_json`). Do not "simplify" it away.
- **The page reports camera state before `loadFinished` reaches Python.** A host reacting to that first signal would call into a widget that still says it is not ready, so queued calls keep their callbacks and are answered late instead of refused.
- **Framing measures vertices, not bounds.** `fitView()` walks real geometry because a bounding box or sphere frames star-shaped content (the axes gizmo) at ~55% of the space it should fill, and because the aggregate `halfDepth + halfHeight/tan` formula assumes the widest point is the nearest — which for anything viewed corner-on it is not. Do not reduce it to `Box3`/`getBoundingSphere`.
- **QSS `QWidget { background: … }` leaks into every `QLabel`**, which then paints the window surface over whatever card it sits on. `demoapp/theme.py` neutralises it with an explicit `QLabel { background: transparent; }`.
- **A translucent part must stop writing depth**, or it hides what is inside it — handled in `parts.js`, and the reason cube faces are separate double-sided meshes rather than one box mesh.

## Consumers

- **DOMY Watch** — the Character Cube in its Encyclopedia; see [PLAN.md](PLAN.md) for the full brief.
- **Vaske Komarnici** (planned) — parametric window-screen preview; the `screen` primitive does not exist yet and should be designed against that site's product configurator when integration starts.
