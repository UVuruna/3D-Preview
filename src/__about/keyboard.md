# Keyboard Control

**Script:** [Keyboard Control (script)](../keyboard.js)

## Purpose

Arrow keys move the viewpoint, Shift+arrows switch view presets, single letters toggle modes. Every binding is a thin call into [Viewer](viewer.md)'s public API, so the same action is available to a GUI button as to a key press — nothing here has behaviour of its own.

## Connections

### Used by
- [Viewer](viewer.md) — attached in the constructor when `options.keyboard` is true
- [Source (folder)](../___src.md) — `KEYBOARD_DEFAULTS` re-exported through the public API

## Exports

- `KEYBOARD_DEFAULTS` — `orbitStep` (15°/press), `panStep` (0.06 of visible height/press), `zoomStep` (1.15×/press)
- `attachKeyboard(viewer, container, options)` — wires the listeners, returns a detach function

## Bindings

| Key | Action |
|-----|--------|
| Arrows | Orbit in steps |
| Ctrl + Arrows | Pan |
| Shift + ← / → | Previous / next view preset |
| Shift + ↑ / ↓ | Top / bottom view |
| `+` / `−` | Zoom |
| `P` · `G` · `R` | Projection · grid · reset |

## Design Decisions

- **Bound to the CONTAINER, not to `window`.** A viewer embedded in someone else's page must not swallow that page's arrow keys. Clicking the viewer focuses it (`pointerdown` → `container.focus()`); a host that wants keys live immediately calls `container.focus()` itself.
- **Ctrl turns the arrows into a pan, not a second set of keys.** One `orbit(event, dx, dy)` handler branches on `event.ctrlKey` rather than doubling the binding table.
- **`event.preventDefault()` on every handled key.** Unhandled arrows would otherwise scroll the host page while the viewer is focused.
- **Returns a detach function** rather than expecting the caller to remember both listeners it added (`keydown`, `pointerdown`) — `Viewer.dispose()` calls it once.
