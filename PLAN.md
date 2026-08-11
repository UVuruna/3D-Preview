# 3D Preview — Implementation Plan

**Status:** COMMISSIONING SPEC (owner-commissioned 2026-07-28).
**M1 and M2 are delivered** — see [Milestones](#milestones); M3 (the
cinematic scenes) and M4 (the DOMY integration) remain. A
Gadgets-category project whose purpose is to serve OTHER projects as a
reusable 3D PREVIEWER. First consumer: Watch Academy's Encyclopedia (the
Character Cube topics).

Where this document and the shipped code differ, the code's own docs
are current: the stack question below was settled by the owner on
2026-07-28 as **build both renderers** ([The Two Renderers](RENDERERS.md)),
and the model format the Data Model section sketches is specified in
full in [Making Models](MODELS.md).

**Ownership (owner decree 2026-07-28):** this gadget is built by
ITS OWN agent and sessions — DOMY's sessions never implement it.
DOMY owns only its half of the integration contract (DOMY WORKPLAN
Session 28) and THIS spec, which is therefore written to be
self-sufficient: everything the implementing agent needs is here.
**Visibility: Public** (owner verdict 2026-07-28). The color
proposal and ALL the extra views below are APPROVED ("može sve što
si zamislio").

## Table of Contents

- [Purpose & Scope](#purpose)
- [Stack Decision (root Rule 21)](#stack)
- [Architecture](#architecture)
- [The Data Model](#data-model)
- [The Four Owner Models](#four-models)
- [Colors for the New Axes](#colors)
- [The Switcher](#switcher)
- [Extra 3D Views (approved)](#extra-views)
- [The Cinematic Scenes — Self-Playing Instructions](#cinematic-scenes)
- [Integration Contract (DOMY first)](#integration)
- [Milestones](#milestones)
- [Testing](#testing)
- [Bootstrap Checklist](#bootstrap)
- [Open Owner Questions](#open-questions)

<a id="purpose"></a>

## Purpose & Scope

A small, reusable 3D viewing engine + a standalone previewer app.
Projects hand it a MODEL (data) and a VIEW CONFIG; it renders an
interactive 3D scene (orbit, zoom, hover, click) in their own UI.
The gadget itself stays content-agnostic: DOMY's Character Cube is
the first model, not the engine's knowledge.

Explicitly OUT of scope for v1: general mesh loading (OBJ/GLTF),
textures, lighting models, physics. The engine draws labeled
geometric scenes (points, lines, faces, billboarded labels/sprites)
— that is what every named use case needs.

<a id="stack"></a>

## Stack Decision (root Rule 21 — written before any code)

**Chosen: Python 3.13 + PySide6, software-projected 3D drawn with
QPainter** (a `preview3d` package exposing a `QWidget`).

Why this fits best:

- **The consumers are PySide6 apps.** Watch Academy embeds a QWidget
  directly — no new runtime, no bridge.
- **Installer weight.** The main alternative (three.js inside
  QWebEngineView) drags QtWebEngine (~100+ MB) into every consumer's
  installer for one dialog — unacceptable for DOMY's lean build.
- **The scenes are tiny.** A cube is 8 vertices / 12 edges / 6
  faces; even the full 125-lattice is a few hundred primitives.
  Rotate–project–sort–paint at 60 fps is trivial CPU work; a GPU
  engine is overkill (root Rule 19 spirit: the simple rule covers
  every case).
- **House idiom.** DOMY's Observatory already chose dark
  QPainter-drawn interactive charts over web tech (WORKPLAN Session
  17); DESIGN.md styling applies directly.

Alternative considered: **three.js + QWebEngineView** — richer 3D
ecosystem and browser reuse, rejected for the dependency weight and
a second tech stack inside Qt apps. Revisit only if a future
consumer is a WEBSITE (the engine's model JSON is renderer-neutral
by design, so a JS renderer could be added later without touching
the data).

<a id="architecture"></a>

## Architecture

```
📁 3D Preview/
  📝 PLAN.md            ← this file
  📝 README.md          ← bootstrap session writes (opening = GitHub About, Rule 22)
  📝 CLAUDE.md          ← project deltas
  📁 preview3d/         ← the LIBRARY other projects import
    🐍 engine.py        ← camera, quaternion orbit, project, depth sort
    🐍 scene.py         ← scene graph: axes, cells, labels, sprites
    🐍 model.py         ← model JSON load/validate (schema below)
    🐍 view.py          ← the QWidget: paint, orbit/zoom input, hover/click hit-test, snap views
    🐍 themes.py        ← palette + the Switcher state (register/reading)
  📁 app/               ← the STANDALONE previewer (owner's toy)
    🐍 main.py          ← open a model JSON, full controls
  📁 assets/            ← logo.svg (required), demo model
  📁 tests/             ← golden projections, schema, angle exactness
  📁 UV/                ← owner inbox (gitignored, Rule 18)
```

- One responsibility per file (root Rule 20); every folder/script
  gets its `.md` per Rule 3 when the bootstrap session creates it.
- The library has NO knowledge of DOMY: consumers pass model +
  callbacks (hover text, click action), so DOMY's hover-teaser law
  stays DOMY's business.

<a id="data-model"></a>

## The Data Model

One JSON schema, renderer-neutral. A model declares:

- **axes** — id, tier (primary/secondary/tertiary/sacred), the two
  END directions as unit vectors, axis name, per-end: luminous term,
  fallen term, color;
- **cells** — id, position, kind (face/edge/vertex/centre), colors,
  per-register names (canon / myth / historical / movie), luminous
  and fallen readings;
- **views** — named presets: which tiers visible, camera snap
  targets (e.g. the four diagonal views), opacity defaults.

DOMY EXPORTS its model from its own canon data (one source of
truth — the 65 terms live in DOMY, never copy-pasted here; root
Rule 19: computed, not duplicated). This gadget ships only a small
neutral demo model.

The radial law is representable: an axis end may carry BOTH a
luminous stop (nearer the centre) and a fallen stop (past it) —
the five-station display comes free from the data.

<a id="four-models"></a>

## The Four Owner Models (the v1 deliverable)

All four are VIEWS over one model — never four hand-built scenes:

1. **Primary Axes** — the 3 face-axes as in the owner's DEMO
   (reference needed — see Open Questions): six pole colors, axis
   names, extremity names, figures per register.
2. **Secondary Axes** — the 6 edge-axes at their TRUE cube angles
   (unit directions of edge midpoints). This is the previewer's
   whole point: the flat wheels cannot show these angles; 3D can.
3. **Tertiary Axes** — the 4 vertex diagonals at true angles, the
   Sacred Axis visually distinguished from the three human ones.
4. **The Cube** — everything at once with gentle face opacity, the
   26 cells + centre visible through the glass.

Per the owner: none of the four shows all text at once — the
SWITCHER selects what speaks (see below).

<a id="colors"></a>

## Colors for the New Axes (APPROVED 2026-07-28)

Computed from parents, never invented per-axis (root Rule 19), with
one collision rule learned from the canon:

- **Primary:** each semi-axis wears its pole hue (the sealed six).
- **Secondary:** blend of the two parent poles, then THINNED BY
  MOONLIGHT (the canon's own operation — the pink/cyan precedent) so
  no edge-axis ever equals a pole hue (naive blue+yellow = green
  would collide with the green pole; the moonlight thinning breaks
  the collision by construction).
- **Tertiary (human three):** three-pole blends, deepened (darker
  register) so they read as a heavier family than the secondaries.
- **The Sacred Axis:** outside the six entirely — **white-gold**,
  the seventh dress, so the one line through God never competes with
  the pole palette.

<a id="switcher"></a>

## The Switcher

Two independent controls, per the owner's spec:

- **Register:** canon / myth / historical / movie — swaps every
  visible label (and figure sprites when art exists). The sacred
  seats in the myth register read Jesus — The One — The Devil.
- **Reading:** Luminous / Fallen / Both — the canon register's
  cells each carry two names; Both shows the five-station radial
  layout on the axes.

Plus per-view toggles: axis lines on/off per tier, face opacity
slider (model 4), label density.

<a id="extra-views"></a>

## Extra 3D Views (ALL APPROVED 2026-07-28)

1. **The Hexagram X-ray (strongest).** The camera flies to a body
   diagonal and the cube visibly BECOMES the dial's hexagram —
   silhouette hexagon, the two triangles emerging from the six
   equatorial face-diagonals. Two snap buttons: the Offices view
   (Court ↔ Genesis) and the Being view (Christic ↔ Diabolic, all
   three sacred seats collapsing into the pivot). This animates the
   sealed epigraph — *the Cube is the world of character; the
   Hexagram is what it reveals along the Sacred Axis* — and is the
   single best teaching device the Encyclopedia could embed.
2. **The Blindness View.** First-person camera AT Jesus's or the
   Devil's vertex: 19 cells visible, the antipode's seven-cell court
   absent/greyed — the blindness law experienced, not narrated; a
   "centre" button then shows all 26 (only The One sees everything).
3. **The Five Stations.** The Sacred Axis alone as a line of beads —
   Purist · JESUS · THE ONE · Champion · DEVIL — measure nearer the
   centre, excess past it; generalizes to any axis on demand.
4. **(Later, after DOMY Session 26)** The 24-orientations clock —
   the cube stepping through its 24 orientations as the hours pass:
   the cube as an actual timepiece. Blocked on the rotation↔hour
   rule.

<a id="cinematic-scenes"></a>

## The Cinematic Scenes — Self-Playing Instructions (APPROVED 2026-07-28)

The owner's confirmation of intent, verbatim understanding: *the
scene plays itself — zooms, transforms into another object, etc.*
These are the binding instructions for the implementing agent.

### The framework rule that everything depends on

**Every render property must be a flat, tweenable parameter from
day one** (M1, not M3): camera position/target/up, the
perspective↔orthographic blend, per-group opacity, line stroke
progress, label-set selection, bead positions. A scene is then only
a DRIVER of parameters over time — the timeline never reaches into
engine internals. Scenes are DATA (named descriptors: keyframes +
easing + durations, living beside the model's `views`), never
hardcoded choreography — a new scene must be writable without an
engine change (root Rules 4 and 19).

Playback controls on every scene: play/pause, scrub slider,
restart, speed (0.5×/1×/2×), and **INSTANT mode** — jump straight
to the end state (accessibility / reduced motion; also what tests
drive). Host API: `play_scene(name)` + an end-of-scene callback, so
a consumer can open a dialog already mid-flight.

Determinism: fixed-timestep evaluation; golden tests pin projected
positions at t = 0, ½, 1 of each scene.

### Scene 1 — The Hexagram X-ray (two variants: Offices, Being)

1. Start at the standard three-quarter view, glass cube.
2. The target diagonal lights up (white-gold for the Being variant;
   the two corner trios glow for Offices).
3. The camera flies an arc until it looks EXACTLY down the diagonal
   (ease-in-out); during the approach the projection blends
   perspective → orthographic and the faces thin to glass.
4. At alignment the silhouette snaps to the regular hexagon; the
   six equatorial face-diagonals DRAW themselves (stroke animation)
   into the two triangles; the six polar-corner edges light as the
   spokes.
5. Labels cross-fade from 3D billboards to flat dial-style labels.
6. **Being variant:** the three sacred seats visibly slide along
   the axis and COLLAPSE into the single centre point — the
   owner's own image: all three become the central axis.
   **Offices variant:** the upward triangle tints with the Court
   trio, the downward with the Genesis trio.
7. End card: the sealed epigraph fades in (host supplies the text).
8. Exit plays the whole flight in reverse.

### Scene 2 — The Blindness (two variants: Christic, Diabolic)

1. From the standard view the chosen absolute vertex glows.
2. The camera flies INTO that vertex, looking toward the centre
   (first-person; the engine needs an inside-the-scene mode with
   near-culling).
3. The seven hidden cells — the antipode, its three edges, its
   three faces — pulse their outlines once, then fade to absence.
4. A HUD line counts: **19 of 26 visible**.
5. A swap control cross-fades to the opposite vertex's view.
6. **The Centre button:** the camera glides to (0,0,0) and all 26
   cells relight — only The One sees everything (host may caption
   with John 1:5 / 2 Chronicles 16:9).

### Scene 3 — The Five Stations

1. The cube fades until only the Sacred Axis line remains.
2. The camera settles side-on to the diagonal.
3. Five beads slide to their stations — and the radial law
   ANIMATES: the luminous stops pull INWARD from the geometric
   vertices, the fallen stops slide PAST them — Purist · JESUS ·
   THE ONE · Champion · DEVIL.
4. Labels reveal per the active register (the Switcher stays live
   inside the scene).
5. A generalize control replays the same choreography on ANY of the
   13 axes (its own luminous/fallen stops).

### Scene 4 — The 24-Orientations Clock (engine-ready now, data later)

Blocked on DOMY's rotation↔hour rule (DOMY WORKPLAN Session 26) —
but the ENGINE feature ships early: snap-to-orientation from a
quaternion table, plus a stepped auto-advance mode. When the rule
lands, the clock is a data drop, not an engine change.

<a id="integration"></a>

## Integration Contract (DOMY first)

- DOMY gains an exporter that builds the Character-Cube model JSON
  from its canon data, and embeds `preview3d.view` in an
  Encyclopedia dialog (seated by the owner's Encyclopedia rework —
  DOMY WORKPLAN Session 27/28; no collision: this gadget only
  provides the widget).
- Hover: the host passes a callback returning the hover card text —
  DOMY wires its teaser law (thesis + LEARN MORE) itself.
- Click: host callback — DOMY jumps to the cell's Encyclopedia page
  (the Spacebar contract's sibling).

<a id="milestones"></a>

## Milestones

- **M1 — Engine core — DONE 2026-07-28.** Camera/orbit/zoom, the
  project–sort–paint pipeline, parts by path, the flat tweenable
  parameter set, golden framing measurements. Delivered TWICE, by the
  owner's 2026-07-28 decision to build both renderers: a Three.js core
  and a QPainter one, held together by `shared/spec.json` and the
  parity tests. The model schema and loader the bullet also named
  landed with M2, where the schema's shape was actually decided.
- **M2 — The four models + Switcher — DONE 2026-07-29.** Arbitrary
  axis directions from one token grammar (the six edge axes and four
  vertex diagonals were previously inexpressible), the model schema as
  shared DATA with a validator in both languages, the thirteen-axis
  cube computed, the four owner models as four VIEWS over it, computed
  colours with the collision rule enforced, the glass cube, the
  register/reading Switcher as flat tweenable channels, snap views to
  any direction, and the 24-orientation table. Pinned by angle
  exactness, golden projections, schema validation, and cross-language
  plus cross-renderer parity.
  Not included, and proposed rather than assumed: the per-view **label
  density** toggle listed under §The Switcher's "plus per-view
  toggles".
- **M3 — The cinematic scenes — DONE 2026-07-30.** All five approved
  scenes shipped as data in `shared/scenes.json`: the Hexagram X-ray
  (Offices + Being), the Blindness (Christic + Diabolic), the Five
  Stations. Playback controls and INSTANT mode were already complete
  from the M2 session (`set_animation`/`play_animation`/…/`jump_to_end`,
  `tests/test_animation_parity.py`'s instant-mode pin) — this session
  verified them, closed no gaps. Two GENERIC engine channels closed the
  gap between what the storyboards needed and what M1/M2 had built:
  `part.position` (a part slides — a bead to its station, a seat
  collapsing into the centre) and `part.strokeProgress` (a line draws
  itself, toward its own end) — both flat, both vector/scalar-lerped by
  the SAME rule every other channel already used, never a hardcoded
  per-scene branch. One new parametric primitive, `hexagram` (the two
  triangles a cube's silhouette splits into down a body diagonal,
  computed from the diagonal per root Rule 19), and one geometry
  addition, `directions.hidden_from()` (the Blindness's 19-of-26 law,
  computed from a vertex's own antipode). One correctness fix that only
  the LIGHT renderer needed: near-plane culling, so the Blindness
  view's first-person dolly does not garble geometry the software
  painter was never asked to draw that close before (three.js already
  clips there in hardware). The Five Stations "generalizes to any axis"
  the extra-views spec promised via a GENERATOR
  (`preview3d/cinematics.py` / `src/cinematics.js`,
  `build_five_stations_scene(model, axis_id)`) rather than 13
  hand-authored scenes — the shipped instance is pinned against the
  generator's live output so the two cannot quietly drift.
  **PLAN.md's original M3 line named "hover/click host callbacks" —
  written BEFORE the owner's 2026-07-28 retraction in this file's own
  CLAUDE.md** ("the previewer is a container… do not build raycast
  picking for it"). The retraction wins: no picking was built, and
  none is owed. **Not shipped, and correctly so:** the 24-Orientations
  Clock (Extra View #4) stays DATA-BLOCKED on DOMY WORKPLAN Session
  26's rotation↔hour rule — the engine capability it needs
  (snap-to-orientation, stepped auto-advance) already exists from M2;
  only the DATA is missing, so nothing here should manufacture a
  placeholder for it.
- **M4 — DOMY integration:** exporter in DOMY, Encyclopedia embed,
  tests on both sides.

Model tiers (root Rule 15): the engine geometry sessions are
**Opus** (projection math, hit-testing in 3D — accuracy over
speed); model/JSON plumbing and the Switcher are **Sonnet**.

<a id="testing"></a>

## Testing

- Golden projections: known camera + known vertex → exact screen
  point (pins the math forever).
- Angle exactness: every axis direction's dot products pinned
  (secondary at edge-midpoint directions, tertiary at diagonals).
- Depth order: a fixed scene's paint order pinned.
- Schema: the demo model and DOMY's exported model both validate.
- The purity idea carries over from DOMY: `engine`/`scene`/`model`
  import no Qt — only `view` touches PySide6 (enforced by a small
  AST test, same pattern as DOMY's `test_purity.py`).

<a id="bootstrap"></a>

## Bootstrap Checklist (first implementation session)

1. Read the monorepo root `CLAUDE.md` + `NAMING.md` + `DESIGN.md`.
2. `git init` (each project its own repo), `.gitignore` with `UV/`.
3. README.md whose opening paragraph is the GitHub About (Rule 22),
   containing THIS plan's stack answer; project CLAUDE.md.
4. `assets/logo.svg` + copy to root `logos/` (Rule: every project).
5. Register in PROJECTS.md + README compact list (after the owner's
   visibility verdict — see Open Questions).
6. Then M1.

Not an installable end-user app initially — a library + dev
previewer, so the build/installer/self-update pipeline (root Rules
23–24) does NOT apply until the owner declares it installable.

<a id="open-questions"></a>

## Open Owner Questions

Answered 2026-07-28: visibility = **Public**; colors = **approved**;
extra views = **all approved** (the Cinematic Scenes section above
is their binding spec). One item remains:

1. **The DEMO reference:** "za glavne OSE — kao iz DEMO" — drop the
   demo file/screenshot into this project's `UV/` (or DOMY's) so M1
   matches the look the owner means. Until it lands, M1 builds the
   axis-cross view from this spec alone and the owner corrects on
   sight.
