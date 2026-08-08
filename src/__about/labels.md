# Text Label Sprites

**Script:** [Text Label Sprites (script)](../labels.js)

## Purpose

Draws text onto a 2D canvas at runtime and mounts it as a camera-facing sprite — no image assets, ever (Compute, Don't Generate (rules/CODE.md): a label is computed from a string and a colour, not shipped as a picture).

## Connections

### Used by
- [Parametric Primitives](primitives.md) — every arm label and radial-stop label is one of these sprites
- [Source (folder)](../___src.md) — `makeLabelSprite` re-exported through the public API

## Exports

- `LABEL_DEFAULTS` — `color`, `fontSize` (canvas px, rendered large and scaled down for crispness), `fontWeight`, `fontFamily`, `padding`, `worldHeight` (sprite height in scene units)
- `makeLabelSprite(text, options)` — the builder

## How It Builds

```
measure text width with the chosen font
size canvas ← text width + padding×2, font height×1.25 + padding×2
draw the text centred onto the canvas
texture  ← CanvasTexture(canvas)
sprite   ← Sprite(SpriteMaterial{map: texture, transparent: true})
sprite scale ← worldHeight × (canvas width / canvas height), worldHeight
```

## Design Decisions

- **The colour is BAKED into the texture**, so the material cannot report it back. `sprite.userData.preview3dColor` records what was actually drawn — without it, [Parts](parts.md)' colour report would tell a host every label is white, which breaks a legend and the cross-renderer palette check both.
- **Rendered large, scaled down** (`fontSize: 96` canvas px against a `worldHeight` of scene units): text drawn small onto a small canvas looks visibly aliased once it fills real screen space; oversampling and shrinking the sprite is cheaper than a proper SDF font pipeline for a component that never shows more than a few dozen labels at once.
