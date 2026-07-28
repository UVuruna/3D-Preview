# Preview3D Widget

**Script:** [Preview3D Widget (script)](widget.py)

## Purpose

`Preview3DWidget` — a drop-in PySide6 widget: any Qt layout gets a 3D preview with orbit controls by constructing one object and calling one method. Internally a `QWebEngineView` loading the bundled host page; every public method runs the mirrored JS Viewer call, and camera movement travels back the other way over a Qt web channel.

## Connections

### Uses
- [Web (folder)](../web/___web.md) — host page (`index.html`) + bundle
- [Viewer](../src/viewer.md) — the JS object every method drives

### Used by
- [Demo Window](../demoapp/window.md) — the demo application
- Host applications (DOMY Watch first) — plain Qt widget, no special integration

## Classes

### _Bridge
The `QObject` JS calls into, one slot per message the page can send. `reportCamera` re-emits as the widget's `camera_changed` signal, `reportAnimation` as `animation_changed`.

### _ConsolePage
`QWebEnginePage` subclass forwarding the JS console into Python `logging` (`preview3d.widget` logger) — a JS error inside the viewer lands in the host app's log (root Rule #1).

### Preview3DWidget

#### Signals
- `camera_changed(dict)`: `{azimuth, elevation, distance, view, projection, grid, gridStep, contentVersion}` — degrees; emitted while the camera moves, rate-limited by the viewer. Watch `contentVersion` to know when newly loaded content is actually in place.
- `animation_changed(dict)`: `{scene, label, playing, time, duration, progress, speed, frame, frames, loop}` — likewise rate-limited. A non-looping scene reaching its end reports `playing: False` at `progress: 1`; that report **is** the end-of-scene signal.

#### Content
- `show_scene(spec)`: any parametric spec, passed through as JSON — see [Parametric Primitives](../src/primitives.md)
- `show_axes(arms=None, arm_length=1.0)`: convenience for the axes gizmo; each arm `{"axis": "+x".."-z", "color": hex (optional), "label": str | list}`
- `load_model(path)`: local glTF/GLB — bytes are read in Python and handed to JS as base64, because Chromium refuses `fetch()` on `file://` URLs

#### Parts
`list_parts(callback)` (asynchronous), `set_part_visible`, `set_part_opacity`, `show_only`, `remove_part` — see [Making Models](../MODELS.md).

#### Camera
`set_view(name)`, `step_view(±1)`, `set_projection(kind)`, `orbit_by(az, el)` (relative), `set_orbit(az, el)` (absolute), `pan_by(dx, dy)`, `zoom_by(factor)`, `reset_view()`.

#### Animation
`set_animation(descriptor)`, `play_animation()`, `pause_animation()`, `toggle_animation()`, `stop_animation()`, `seek_animation(0…1)`, `step_frame(±1)`, `set_speed(x)`, `jump_to_end()`, `animation_state(callback)` — see [Animation Scenes](../SCENES.md).

Playback runs **inside the page**, on its own animation frames; these calls only start and steer it, and the state comes back over the web channel. `show_scene` / `load_model` clear any loaded scene, so content is loaded first and the scene second.

#### Appearance
`set_background(color)` (CSS hex or `"transparent"`), `set_grid(enabled)`. The Qt page surface follows automatically — the viewer reports the colour it clears to and `_sync_background` applies it, so the colour is never restated on the Python side.

## Design Decisions

- **The page surface is painted, never left at its default.** `QWebEnginePage` defaults to **opaque white**, and the host page's `html`, `body` and container are all transparent — so that white sheet sat behind everything and showed in any frame the canvas was not painted, which a resize guarantees. Pinned by `tests/test_background_flash.py`.
- **Structured results cross as JSON strings.** QtWebEngine's direct value conversion does not survive JS arrays — an array of three strings arrives in Python as an **empty string**, with no error anywhere. Numbers and strings convert fine, so `_run_json` wraps every result-returning call in `JSON.stringify` and decodes it in Python. This cost a real debugging session; do not "simplify" it away.
- **Queued calls keep their callback.** The page starts reporting camera state as soon as its web channel is up, which is *before* `loadFinished` reaches Python — so a host reacting to that first signal would be calling into a widget that says it is not ready. Early requests are answered late rather than refused or silently dropped.
- **`qwebchannel.js` is injected as source**, read from the Qt resource system, rather than referenced by URL: a local `file://` page cannot reliably fetch a `qrc://` script, and the host page must behave identically from a checkout and from a wheel.
- **The page works without Qt.** The channel setup is guarded by `window.qt`, so the same `web/index.html` serves a plain browser unchanged.
- **Bundle resolution, two documented locations:** installed wheel → `preview3d/web/`; repo checkout → `../web/`. Anything else raises `FileNotFoundError` with the fix (`npm run build`) — no silent blank widget.
