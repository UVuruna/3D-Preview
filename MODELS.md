# Making Models for 3D Preview

How to build (or repair) a model so its elements can be **addressed** — shown, hidden, made translucent, swapped for one another, or dropped entirely. Written for the case where we author the models ourselves.

## Table of Contents

- [The One Rule](#the-one-rule)
- [Paths — How a Part Is Addressed](#paths)
- [Naming Conventions](#naming)
- [Switch Groups — One of Several, at a Time](#switch-groups)
- [Materials — The Sharing Trap](#materials)
- [Seeing Inside — Translucency That Works](#translucency)
- [Authoring in Blender](#blender)
- [Repairing a Model We Did Not Make](#repairing)
- [Parametric Models — No File at All](#parametric)
- [The API](#api)
- [Checklist](#checklist)

---

<a id="the-one-rule"></a>

## The One Rule

**A part that has no name cannot be addressed.**

Everything in this document follows from that. The viewer identifies elements by their names in the model's node tree; an unnamed node falls back to `Mesh#3`, which is not something anyone can write into code, and which silently changes the moment the model is re-exported.

So: **name every node you will ever want to touch, and group the ones that belong together.**

---

<a id="paths"></a>

## Paths — How a Part Is Addressed

A part's address is the chain of node names from the content root, joined with `/`:

```
axes/arm:+x/labels/label:1
│    │      │      └── the node itself
│    │      └───────── its group
│    └──────────────── the arm group
└───────────────────── the model root
```

Two consequences worth internalising:

- **Renaming a node changes its address.** Names are the public interface of a model; treat a rename like renaming a function, and update the host code that addresses it.
- **A group is addressable too.** Hiding a group hides everything under it, in one call — which is why grouping is not cosmetic.

`listParts()` returns every part with its `path`, `depth`, whether it is `drawable` (carries geometry) or a pure group, plus its current `visible` and `opacity`. That is what the demo app's PARTS panel is built from.

---

<a id="naming"></a>

## Naming Conventions

Names are free-form, but the house conventions below make models readable and predictable. **Never put `/` in a name** — it is the path separator.

| Pattern | Use for | Example |
|---------|---------|---------|
| `noun` | a single distinct element | `joint`, `body`, `edges`, `core` |
| `kind:key` | one of a family, keyed by what distinguishes it | `arm:+x`, `face:-z`, `station:3` |
| plural noun | a group holding a family | `arms`, `labels`, `faces` |
| `label:N` | numbered alternatives inside a switch group | `label:0`, `label:1` |

Rules of thumb:

- **Group by what you will manipulate together.** If the whole arm should dim at once, the shaft, tip and labels belong in one `arm:+x` group. If only the tip should dim, they must be siblings.
- **Keep the tree shallow but real.** Two or three levels is plenty; nesting every mesh in its own group makes long addresses and buys nothing.
- **Names carry no language.** They are identifiers, not display text (root Rule #12). Display text lives in the label sprite's content, which the host can swap.

---

<a id="switch-groups"></a>

## Switch Groups — One of Several, at a Time

The exact case that motivated this system: **three legend terms on one axis tip, only one shown, then the next.**

Model it as a group whose children are the alternatives:

```
axes/
  arm:+x/
    shaft
    tip
    labels/          ← the switch group
      label:0        ← "East"    (visible)
      label:1        ← "Istok"   (hidden)
      label:2        ← "E"       (hidden)
```

Then one call selects which one speaks:

```javascript
viewer.showOnly('axes/arm:+x/labels', 'label:1');   // now only "Istok" is shown
```

```python
widget.show_only("axes/arm:+x/labels", "label:1")
```

`showOnly` shows the named child and hides its siblings — no bookkeeping on the host side, no risk of two terms visible at once. The demo app's `solo` button next to a group is exactly this, cycling through the children and back to all.

**Author all alternatives in the same place, at the same size.** They are alternates, not a layout — the viewer swaps visibility and nothing else.

---

<a id="materials"></a>

## Materials — The Sharing Trap

The single most common reason "I dimmed one part and something else went transparent too."

**A material is a shared object.** In a real glTF file, one material typically dresses many meshes; a modelling tool assigns the same material to every part of the same colour. Changing its opacity would change every part wearing it.

The viewer handles this for you: the first time a part's opacity is changed, that part gets its **own copy** of the material, and only that copy is modified. Verified behaviour — dimming an arm's shaft to 0.25 leaves the neighbouring tip at 1.0 even though the two are the same colour.

What that means when authoring:

- You do **not** need a unique material per part just to make opacity work.
- You **do** need a unique material per part if the parts must have different **colours** — that part is ordinary modelling.
- Do not rely on editing a material to change many parts at once through the viewer; address the parts (or their common group) instead.

---

<a id="translucency"></a>

## Seeing Inside — Translucency That Works

Setting a part's opacity below 1 also turns off its **depth writing**. Without that, a translucent shell still writes into the depth buffer and hides whatever is inside it — the exact opposite of why anyone makes a shell translucent.

For a model meant to be looked into:

- **Model the outer shell as separate, individually addressable faces**, not as one closed mesh. A single mesh can only be dimmed as a whole; six named faces let you open the two facing the camera and keep the rest solid, which reads far better than a uniformly ghostly box.
- **Give shell faces double-sided materials.** Once you can see through the near face, you are looking at the *back* of the far ones; single-sided faces vanish and the object looks broken.
- **Put the inner content in its own group** so it can be revealed and hidden independently.

The `Cube + core` demo scene is exactly this shape: a `shell` of six named faces with a `core` inside it. Dim `shell/face:+z` and `shell/face:+y` and the core is plainly visible through them.

---

<a id="blender"></a>

## Authoring in Blender

The viewer reads **glTF 2.0** (`.glb` preferred — one self-contained file).

1. **Name every object in the Outliner.** Blender's object names become the glTF node names, which become the path segments. `Cube.001` is a bug waiting to happen.
2. **Parent by empties for grouping.** An Empty named `arm:+x` with the shaft, tip and labels parented under it becomes exactly the group structure above. Blender collections do **not** survive the export as groups — parenting does.
3. **Apply transforms** (Object → Apply → All Transforms) before export, unless a transform is meaningful. Unapplied scale is the usual cause of "it loaded ten times too big".
4. **Keep the model near the origin and roughly unit-sized.** The viewer frames whatever it gets, so absolute size does not break anything, but a model 5000 units from the origin makes grid and depth settings awkward.
5. **Y is up.** Use the glTF exporter's default `+Y up` conversion; the viewer's `top`/`bottom` views and the ground grid assume it.
6. **Export settings:** include Selected Objects only if that is what you mean; keep *Materials*; drop *Cameras* and *Lights* — the viewer supplies its own lighting, and an exported light will not be used.
7. **One material per intended colour**, not per object. Sharing is fine (see above).

**Verify before shipping the file:** load it in the demo app and read the PARTS list. Every element you plan to control must appear there with a name you recognise. If it says `Mesh#4`, the model is not finished.

---

<a id="repairing"></a>

## Repairing a Model We Did Not Make

Downloaded models are almost never addressable — flat hierarchies, `mesh_0_1` names, one giant merged mesh.

1. **Load it in the demo app and read the PARTS list first.** That tells you what you actually got.
2. **One merged mesh cannot be split by the viewer.** Separate it in Blender (Edit Mode → `P` → By Loose Parts, or by material), then name the pieces.
3. **Rename and re-parent** to the conventions above.
4. **Re-export as `.glb`** and check the PARTS list again.

Budget the work honestly: renaming is minutes, splitting a merged mesh is real modelling time.

---

<a id="parametric"></a>

## Parametric Models — No File at All

Before authoring a file, ask the derivation question (root Rule #19): **can this be computed from parameters?** If yes, it belongs in `src/primitives.js` as a builder, not on disk — every variant then comes free and nothing has to be re-exported when a colour or a size changes.

A parametric spec is plain JSON and nests:

```javascript
{
    type: 'cube', name: 'shell', colors: 'poles',
    children: [
        { type: 'cube', name: 'core', size: 0.45, color: '#F5F5F5' }
    ]
}
```

Every spec accepts `name`, `position`, `scale` and `children`, so an assembly is one JSON tree with the same addressable structure a file would give you. Builders name their own children (`axes/arm:+x/shaft`, `cube/face:+y`), so parts control works identically for computed and loaded content.

Adding a builder is documented in [Parametric Primitives](src/primitives.md).

---

<a id="api"></a>

## The API

Same operations on both sides; JS names are camelCase, Python snake_case.

| Operation | JavaScript | Python |
|-----------|-----------|--------|
| List parts | `viewer.listParts()` | `widget.list_parts(callback)` |
| Show / hide | `viewer.setPartVisible(path, on)` | `widget.set_part_visible(path, on)` |
| Opacity 0–1 | `viewer.setPartOpacity(path, a)` | `widget.set_part_opacity(path, a)` |
| One of a group | `viewer.showOnly(group, child)` | `widget.show_only(group, child)` |
| Remove for good | `viewer.removePart(path)` | `widget.remove_part(path)` |

The Python listing is asynchronous — the answer arrives in the callback, because the model may still be loading when you ask.

**Hiding is not removing.** `setPartVisible(path, false)` is the reversible one and is what toggling wants. `removePart` detaches the part and frees its geometry and materials; it is for content that must not stay in memory, and it cannot be undone without rebuilding the scene.

**A wrong path raises**, listing the paths that do exist. That is deliberate (root Rule #1): a typo must not look like a part that simply had nothing to change.

---

<a id="checklist"></a>

## Checklist

Before a model is considered done:

- [ ] Every element you intend to control has a **deliberate name**
- [ ] Elements manipulated together share a **group**
- [ ] Alternatives (labels, language variants, registers) sit in a **switch group** as siblings
- [ ] Shell faces meant to be seen through are **separate and double-sided**
- [ ] Transforms applied; model near the origin; **+Y up**
- [ ] The demo app's PARTS list shows the names **you expect**, with no `Mesh#N`
- [ ] Anything derivable from parameters was built as a **primitive**, not exported as a file (root Rule #19)
