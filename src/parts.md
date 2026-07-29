# Parts

**Script:** [Parts (script)](parts.js)

## Purpose

Addressing the individual elements of whatever is being shown, so a host can show, hide, dim, solo or drop them one at a time. This is the module behind the demo apps' PARTS panel and behind the "three legend terms on one axis tip, one shown at a time" case.

The authoring side of the contract — how a model must be built for any of this to work — is [Making Models for 3D Preview](../MODELS.md).

## Connections

### Used by
- [Viewer](viewer.md) — every function here is exposed as a Viewer method; hosts never import this module directly

## Paths

A part is addressed by its **path**: the slash-joined chain of object names from the content root.

```
axes/arm:+x/labels/label:1
```

Unnamed nodes fall back to `Type#index` (`Mesh#3`), which is why naming is the whole contract. `collectParts()` returns the flat list in tree order, each entry carrying `path`, `name`, `type`, `depth` (for indenting a UI), `drawable` (has geometry, as opposed to being a pure group), `visible`, `opacity` and `color`.

`color` is `#RRGGBB`, or `null` for a pure group. It is reported because a host needs it for a legend — and because it is the only way a test can check that a COMPUTED palette ([Axis Colours](../preview3d/axis_colors.md)) came out the same in both renderers: the pictures deliberately cannot be compared, the values can. A label sprite's colour is baked into its texture, so the builder records what it actually drew in `userData.preview3dColor` rather than letting every label report white.

## Functions

- `collectParts(root)`: the part list described above
- `findPart(root, path)`: the object, or `null`
- `setPartVisible(root, path, visible)`: hiding a group hides its whole subtree
- `showOnly(root, groupPath, childName)`: show one child, hide its siblings — a switch group in one call
- `setPartOpacity(root, path, alpha)`: sets the part's OWN opacity, which multiplies down its subtree
- `removePart(root, path)`: detach and dispose geometry and materials; irreversible

## Design Decisions

- **A wrong path throws, listing the paths that exist** (root Rule #1). A typo must never look like a part that simply had nothing to change — that failure is invisible and expensive.
- **Opacity multiplies down; a part reports its OWN.** Dimming a group dims everything under it without changing what its children say about themselves — which is the LIGHT renderer's model too, and it has to be, or `listParts` reports two different numbers for the same part. Pushing the value straight onto every descendant's material (what this did before the model pins caught it) makes a child claim its parent's dimming as its own, and lets re-lighting one child silently escape the group. The value is recorded in `userData.preview3dOpacity` and the whole content's effective opacities are recomputed from the root on every change — a few hundred cheap visits, against a bug that is invisible until someone reads the numbers.
- **A built-in faintness is the part's own opacity too.** The cube's wireframe is recorded in `userData` at build time, not left implicit in its material, so dimming the cube around it multiplies from the right starting value.
- **Materials are cloned on first opacity change.** A material is routinely shared — between an arm's shaft and its tip here, across whole meshes in a real glTF — so dimming one part would otherwise dim its neighbours. The clone is marked in `userData` so repeated changes reuse it instead of cloning on every slider step.
- **Translucency turns depth writing off.** A shell that still writes depth hides whatever is inside it, which is the opposite of why anyone makes a shell translucent; opacity back at 1 restores it.
- **Hiding and removing are separate operations.** Toggling wants `setPartVisible`; `removePart` exists for content that must not stay in memory and is documented as irreversible.
