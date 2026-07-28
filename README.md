# 3D Preview

Embeddable 3D previewer — one Three.js core with orbit controls (rotate, zoom, pan), embedded by Python desktop GUIs as a PySide6 widget or by websites with a single script tag. Simple shapes (axes gizmo, cube) are computed from parametric JSON specs instead of stored model files; glTF/GLB load and export included.

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

A small window with the viewer and a control panel: switch between the built-in demo scenes, load a `.glb`/`.gltf` file from disk, cycle the background (dark / light / transparent), reset the view — and try the controls listed [below](#controls).

The same thing in a browser, with GLB export as well: open `demo/index.html`.

---

<a id="why-this-stack"></a>

## Why This Stack

*Answer required by root Rule #21 — which language/stack fits this task best, and why?*

The viewer must render **identically** inside Python desktop apps and websites. A browser WebGL core (**Three.js**, bundled by esbuild) is the only stack both targets share natively — websites load the bundle directly, and PySide6 embeds the same bundle through `QWebEngineView` (Chromium). One rendering implementation serves every consumer (root Rule #5).

**Alternative considered:** a native Python OpenGL viewer (pyqtgraph/VTK) for GUIs plus a separate web viewer — rejected: two implementations of identical behavior, double maintenance, guaranteed feature drift. The only cost of the chosen stack is the Qt WebEngine dependency on the Python side, which PySide6 already ships.

---

<a id="structure"></a>

## Structure

```
📁 3D Preview/
  📝 README.md          ← You are here
  📝 CLAUDE.md          ← AI guidance for this project
  🐍 main.py            ← Demo application (run this)
  ⚙️ package.json       ← JS build config (esbuild)
  ⚙️ pyproject.toml     ← Python package config (hatchling)
  📁 src/               ← JS core sources
    🔧 index.js  viewer.js  primitives.js  labels.js
  📁 web/               ← Shipped artifact: host page + built bundle
    📄 index.html  preview3d.min.js
  📁 demo/              ← Standalone browser demo
    📄 index.html
  📁 preview3d/         ← Python package (PySide6 widget)
    🐍 __init__.py  widget.py
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
    viewer.show({ type: 'axes' });          // or {type: 'cube'}, or viewer.loadModel('model.glb')
</script>
```

### Python (PySide6)

```python
from preview3d import Preview3DWidget

widget = Preview3DWidget(parent)
widget.show_axes(arms=[
    {"axis": "+x", "color": "#EF4444", "label": "East"},
    {"axis": "-x", "color": "#F97316", "label": "West"},
    {"axis": "+y", "color": "#22C55E", "label": "Zenith"},
    {"axis": "-y", "color": "#EAB308", "label": "Nadir"},
    {"axis": "+z", "color": "#3B82F6", "label": "North"},
    {"axis": "-z", "color": "#A855F7", "label": "South"},
])
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

---

<a id="documentation"></a>

## Documentation

- [Demo Application](main.md) — the runnable showcase and integration example
- [Source (folder)](src/___src.md) — viewer core, parametric primitives, labels
- [Assets (folder)](assets/___assets.md) — logo and the bundled Inter typeface
- [Web (folder)](web/___web.md) — host page and the built bundle
- [Demo (folder)](demo/___demo.md) — standalone browser demo
- [Preview3d Package (folder)](preview3d/___preview3d.md) — PySide6 widget wrapper
- [CLAUDE.md](CLAUDE.md) — AI guidance
