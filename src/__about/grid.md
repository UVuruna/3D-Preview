# Ground Grid

**Script:** [Ground Grid (script)](../grid.js)

## Purpose

An optional reference plane under the content, sized to it — computed from the content's bounds every time the content changes (root Rule #19), never a fixed 10×10 helper that is wrong for anything but a unit cube.

## Connections

### Used by
- [Viewer](viewer.md) — rebuilds the grid on every content swap and orientation change, when `gridEnabled`
- [Source (folder)](../___src.md) — `GRID_DEFAULTS` re-exported through the public API

## Exports

- `GRID_DEFAULTS` — `lineColor`, `centerColor`, `opacity`, `spanFactor` (grid width relative to the content's footprint), `targetCells` (aim for this many cells across; the step is rounded)
- `buildGrid(content, options)` — returns `{grid, step}`, or `null` when there is nothing to measure
- `disposeGrid(grid)` — geometry, material, detach

## How the Step Is Chosen

```
box       ← THREE.Box3 of the content
footprint ← max(width, depth, height / 2)
span      ← footprint × spanFactor
step      ← round span / targetCells UP to the nearest 1, 2 or 5 × 10ⁿ
divisions ← round(span / step), at least 2
grid      ← GridHelper(divisions × step, divisions), centred under the content,
            sitting on its floor, depth-write off so it never occludes the model
```

The rounded step is why a camera readout can honestly say "0.5 per cell" instead of "0.3874 per cell".

## Design Decisions

- **The grid lives outside the content group.** Building it as a sibling in the scene, not a child of `_content`, means enabling it never changes how the content is framed (`fitView()` only walks `_content`).
- **`depthWrite = false`.** The grid is a reference plane, not geometry the model could hide behind or be hidden by.
- **Rounds UP, never down**, so the grid always covers at least the requested span — a grid narrower than the content it sits under would be a worse reference than none.
