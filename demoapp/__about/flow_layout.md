# Flow Layout

**Script:** [Flow Layout (script)](../flow_layout.py) ·
**Flow:** [diagram](../__flow/flow_layout.md)

## Purpose

A Qt layout that wraps its items onto as many rows as it needs. Qt ships no
wrapping layout, and a `QHBoxLayout` reports the **sum** of its items' widths
as its minimum — which is how a single row of eight legend chips came to
dictate a 1649 px minimum window width (pinned by
[`tests/test_window_minimum_size.py`](../../tests/___tests.md)). `FlowLayout`'s
minimum is the widest **single** item, so a strip built on it can collapse to
one item per row instead of forcing the window wide.

## Connections

### Uses
- none (pure Qt `QLayout` subclass, no project imports)

### Used by
- [Demo Window](window.md) — the keyboard-legend strip under CONTROLS

## Classes

### FlowLayout
`QLayout` subclass. Places items left to right, wrapping at the right edge.

- `addItem` / `count` / `itemAt` / `takeAt` / `expandingDirections` — the
  minimum `QLayout` plumbing Qt requires
- `hasHeightForWidth` / `heightForWidth(width)` — reports that this layout's
  height depends on its width (how many rows wrapping produces)
- `setGeometry(rect)` — lay out the real items into `rect`
- `sizeHint()` / `minimumSize()` — the widest single item, not the sum
- `_arrange(rect, apply)` — the wrapping algorithm itself; see [flow](../__flow/flow_layout.md)

### `flow_size_policy()`
Module-level helper (not a class): returns the `QSizePolicy` a hosting widget
needs for `FlowLayout`'s height-for-width to be honoured — without it Qt asks
for the height once, at the wrong width, and the wrap never happens correctly.
