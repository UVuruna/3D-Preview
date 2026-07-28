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

Unnamed nodes fall back to `Type#index` (`Mesh#3`), which is why naming is the whole contract. `collectParts()` returns the flat list in tree order, each entry carrying `path`, `name`, `type`, `depth` (for indenting a UI), `drawable` (has geometry, as opposed to being a pure group), `visible` and `opacity`.

## Functions

- `collectParts(root)`: the part list described above
- `findPart(root, path)`: the object, or `null`
- `setPartVisible(root, path, visible)`: hiding a group hides its whole subtree
- `showOnly(root, groupPath, childName)`: show one child, hide its siblings — a switch group in one call
- `setPartOpacity(root, path, alpha)`: applies to the whole subtree
- `removePart(root, path)`: detach and dispose geometry and materials; irreversible

## Design Decisions

- **A wrong path throws, listing the paths that exist** (root Rule #1). A typo must never look like a part that simply had nothing to change — that failure is invisible and expensive.
- **Materials are cloned on first opacity change.** A material is routinely shared — between an arm's shaft and its tip here, across whole meshes in a real glTF — so dimming one part would otherwise dim its neighbours. The clone is marked in `userData` so repeated changes reuse it instead of cloning on every slider step.
- **Translucency turns depth writing off.** A shell that still writes depth hides whatever is inside it, which is the opposite of why anyone makes a shell translucent; opacity back at 1 restores it.
- **Hiding and removing are separate operations.** Toggling wants `setPartVisible`; `removePart` exists for content that must not stay in memory and is documented as irreversible.
