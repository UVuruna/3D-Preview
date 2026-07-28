# 3D Preview

Embeddable 3D previewer with two interchangeable renderers — a Three.js core for websites and rich models, and a QPainter one for Qt apps that cannot carry a browser engine. Both give free orbit, view presets, per-element visibility and opacity, and self-playing animation scenes with play, pause, single-frame stepping and scrubbing.

## Table of Contents

- [Run the Demo](#run-the-demo)
- [Why This Stack](#why-this-stack)
- [Structure](#structure)
- [Embedding](#embedding)
- [Controls](#controls)
- [Documentation](#documentation)

---

<a id="run-the-demo"></a>

## Run the Demo

```bash
pip install PySide6
python main.py
```

A window with the viewer and a control panel: a **RENDERER** switch between the two back ends, the built-in demo scenes, loading a `.glb`/`.gltf` file from disk, **animation playback** (five scenes, with restart / single-frame stepping / play-pause / jump-to-end, a scrub slider and 0.5×–2× speed), the seven view presets, perspective ↔ orthographic, the reference grid, background modes (dark / light / transparent), a live camera readout, and a parts list where every element can be hidden, dimmed or soloed.

The renderer switch carries the animation across mid-flight, which is the quickest way to see how the two compare on the same moving scene.

The same thing in a browser, with GLB export as well: open `demo/index.html`.

---

<a id="why-this-stack"></a>

## Why This Stack

*Answer required by root Rule #21 — which language/stack fits this task best, and why?*

**Both, deliberately** — because the consumers genuinely differ and neither stack covers all of them.

A browser WebGL core (**Three.js**, bundled by esbuild) is the only stack that serves websites and Qt apps from one implementation: a page loads the bundle directly, and PySide6 embeds the same bundle through `QWebEngineView`. It also brings glTF/GLB loading and real materials for free. Its cost is Qt WebEngine — **343 MB on disk** in a PySide6 install, and the largest single thing in an otherwise lean desktop app.

So there is a second renderer: **software 3D drawn with QPainter**, pure Python, no browser engine and no GPU. For parametric labelled scenes — the kind the first consumer needs — it gives the same free orbit, the same views and projections, and crisper text; what it gives up is file loading, real materials, large meshes and browsers.

Two implementations of one component invite drift (root Rule #5), so the mitigation is built in rather than promised: everything both must agree on lives in `shared/spec.json`, and `tests/test_renderer_parity.py` drives both from the same specs and compares what a host can observe. See [The Two Renderers](RENDERERS.md).

---

<a id="structure"></a>

## Structure

```
📁 3D Preview/
  📝 README.md          ← You are here
  📝 CLAUDE.md          ← AI guidance for this project
  📝 RENDERERS.md       ← The two renderers: which to use and why
  📝 MODELS.md          ← How to author models whose parts can be controlled
  📝 SCENES.md          ← How to write animation scenes (keyframes as data)
  📝 PLAN.md            ← Commissioning spec (DOMY Watch's brief for this gadget)
  🐍 main.py            ← Demo application (run this)
  ⚙️ package.json       ← JS build config (esbuild)
  ⚙️ pyproject.toml     ← Python package config (hatchling)
  📁 shared/            ← Data BOTH renderers read
    ⚙️ spec.json        palette, face order, view presets, camera and animation defaults
    ⚙️ scenes.json      the shipped animation scenes
  📁 src/               ← WEB renderer sources (JS)
    🔧 index.js  viewer.js  primitives.js  parts.js  animation.js
    🔧 views.js  grid.js  keyboard.js  labels.js
  📁 web/               ← Shipped artifact: host page + built bundle
    📄 index.html  preview3d.min.js
  📁 demo/              ← Standalone browser demo
    📄 index.html
  📁 preview3d/         ← Python package — both widgets
    🐍 __init__.py  widget.py  resources.py
    📁 light/           ← LIGHT renderer (QPainter software 3D)
      🐍 view.py  renderer.py  camera.py  scene.py  primitives.py  vectors.py  animation.py
  📁 demoapp/           ← Demo application window
    🐍 window.py  parts_panel.py  theme.py  flow_layout.py
  📁 tests/             ← Regression pins (pytest)
  📁 assets/
    🖼️ logo.svg
    📁 fonts/           ← Bundled Inter (OFL)
```

---

<a id="embedding"></a>

## Embedding

### Website

Copy `web/preview3d.min.js` next to your page:

```html
<div id="stage" style="width: 640px; height: 480px"></div>
<script src="preview3d.min.js"></script>
<script>
    const viewer = Preview3D.mount(document.getElementById('stage'));
    viewer.show({ type: 'axes' });           // or {type: 'cube', colors: 'poles'}
    viewer.setProjection('orthographic');    // exact isometric
    viewer.setPartOpacity('cube/face:+z', 0.2);

    viewer.setAnimation(Preview3D.SCENES[0]);   // a shipped scene, or your own descriptor
    viewer.playAnimation();
</script>
```

### Python (PySide6)

```python
from preview3d import Preview3DWidget        # web core: files, materials, browsers
from preview3d import Preview3DLightWidget   # QPainter: no browser engine at all

widget = Preview3DWidget(parent)              # ← swap the class, nothing else changes
widget.camera_changed.connect(lambda s: print(s["azimuth"], s["elevation"]))
widget.show_axes(arms=[
    {"axis": "+x", "label": ["East", "Istok", "E"]},
    {"axis": "+y", "label": "Zenith"},
    {"axis": "+z", "label": "North"},
])
widget.show_only("axes/arm:+x/labels", "label:1")   # now the arm reads "Istok"

from preview3d import load_shared_scenes                    # scenes are DATA — SCENES.md
widget.set_animation(load_shared_scenes()[0])               # content first, scene second
widget.play_animation()                                     # play / pause / step / scrub / instant
```

From a repo checkout the package resolves the web bundle automatically; as a dependency install it with `pip install git+<repo-url>` (the bundle ships inside the wheel).

### Rebuilding the bundle

```bash
npm install
npm run build      # src/ → web/preview3d.min.js
```

Node is needed only to rebuild the bundle — never to use the component; `web/preview3d.min.js` is committed.

---

<a id="controls"></a>

## Controls

| Input | Action |
|-------|--------|
| Left-drag | Rotate (orbit) |
| Scroll wheel / pinch | Zoom |
| Right-drag | Pan |
| Arrow keys | Move around the model in steps |
| Ctrl + arrows | Pan — move the point being looked at |
| Shift + ← / → | Previous / next view preset |
| Shift + ↑ / ↓ | Top / bottom view |
| `+` / `−` | Zoom |
| `P` · `G` · `R` | Projection · grid · reset view |

Keys act on the viewer once it has focus (click it, or call `focus()` on its container).

---

<a id="documentation"></a>

## Documentation

- [The Two Renderers](RENDERERS.md) — which renderer to use, what each can do, how drift is prevented
- [Making Models for 3D Preview](MODELS.md) — how to author or repair a model so its parts can be controlled
- [Animation Scenes](SCENES.md) — the scene descriptor format, the channels, and the playback API
- [Demo Application](main.md) — the runnable showcase and integration example
- [Source (folder)](src/___src.md) — viewer core, primitives, parts, views, grid, keyboard, labels
- [Web (folder)](web/___web.md) — host page and the built bundle
- [Demo (folder)](demo/___demo.md) — standalone browser demo
- [Preview3d Package (folder)](preview3d/___preview3d.md) — PySide6 widget wrapper
- [Demo App (folder)](demoapp/___demoapp.md) — demo window, parts panel, theme
- [Tests (folder)](tests/___tests.md) — regression pins and what each one guards
- [Assets (folder)](assets/___assets.md) — logo and the bundled Inter typeface
- [CLAUDE.md](CLAUDE.md) — AI guidance
