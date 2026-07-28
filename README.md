# 3D Preview

Embeddable 3D previewer — one Three.js core with orbit controls, view presets and a perspective/orthographic switch, used by Python GUIs as a PySide6 widget or by websites with one script tag. Scene elements are shown, hidden or dimmed by name; simple shapes are computed from JSON specs, and glTF/GLB models load and export.

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

A window with the viewer and a control panel: the built-in demo scenes, loading a `.glb`/`.gltf` file from disk, the seven view presets, perspective ↔ orthographic, the reference grid, background modes (dark / light / transparent), a live camera readout, and a parts list where every element can be hidden, dimmed or soloed.

The same thing in a browser, with GLB export as well: open `demo/index.html`.

---

<a id="why-this-stack"></a>

## Why This Stack

*Answer required by root Rule #21 — which language/stack fits this task best, and why?*

The viewer must render **identically** inside Python desktop apps and websites. A browser WebGL core (**Three.js**, bundled by esbuild) is the only stack both targets share natively — websites load the bundle directly, and PySide6 embeds the same bundle through `QWebEngineView` (Chromium). One rendering implementation serves every consumer (root Rule #5).

**Alternative considered:** a native Python viewer (software projection with QPainter, or pyqtgraph/VTK) plus a separate web viewer — rejected because it means two implementations of identical behaviour, double maintenance and guaranteed feature drift, and because it cannot serve the website consumers at all. The cost of the chosen stack is the Qt WebEngine dependency on the Python side, which PySide6 already ships but which adds weight to a consumer's installer.

---

<a id="structure"></a>

## Structure

```
📁 3D Preview/
  📝 README.md          ← You are here
  📝 CLAUDE.md          ← AI guidance for this project
  📝 MODELS.md          ← How to author models whose parts can be controlled
  📝 PLAN.md            ← Commissioning spec (DOMY Watch's brief for this gadget)
  🐍 main.py            ← Demo application (run this)
  ⚙️ package.json       ← JS build config (esbuild)
  ⚙️ pyproject.toml     ← Python package config (hatchling)
  📁 src/               ← JS core sources
    🔧 index.js  viewer.js  primitives.js  parts.js
    🔧 views.js  grid.js  keyboard.js  labels.js
  📁 web/               ← Shipped artifact: host page + built bundle
    📄 index.html  preview3d.min.js
  📁 demo/              ← Standalone browser demo
    📄 index.html
  📁 preview3d/         ← Python package (PySide6 widget)
    🐍 __init__.py  widget.py
  📁 demoapp/           ← Demo application window
    🐍 window.py  parts_panel.py  theme.py
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
</script>
```

### Python (PySide6)

```python
from preview3d import Preview3DWidget

widget = Preview3DWidget(parent)
widget.camera_changed.connect(lambda s: print(s["azimuth"], s["elevation"]))
widget.show_axes(arms=[
    {"axis": "+x", "label": ["East", "Istok", "E"]},
    {"axis": "+y", "label": "Zenith"},
    {"axis": "+z", "label": "North"},
])
widget.show_only("axes/arm:+x/labels", "label:1")   # now the arm reads "Istok"
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

- [Making Models for 3D Preview](MODELS.md) — how to author or repair a model so its parts can be controlled
- [Demo Application](main.md) — the runnable showcase and integration example
- [Source (folder)](src/___src.md) — viewer core, primitives, parts, views, grid, keyboard, labels
- [Web (folder)](web/___web.md) — host page and the built bundle
- [Demo (folder)](demo/___demo.md) — standalone browser demo
- [Preview3d Package (folder)](preview3d/___preview3d.md) — PySide6 widget wrapper
- [Demo App (folder)](demoapp/___demoapp.md) — demo window, parts panel, theme
- [Tests (folder)](tests/___tests.md) — regression pins and what each one guards
- [Assets (folder)](assets/___assets.md) — logo and the bundled Inter typeface
- [CLAUDE.md](CLAUDE.md) — AI guidance
