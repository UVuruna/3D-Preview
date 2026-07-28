// Parametric primitives — simple shapes COMPUTED from a spec (root Rule #19:
// no stored model files for anything a formula can build). Each builder takes
// a plain-JSON spec and returns a THREE.Group whose children are NAMED, so the
// parts API can address them one by one (see MODELS.md).

import * as THREE from 'three';
import { makeLabelSprite } from './labels.js';

const AXIS_DIRECTIONS = {
    '+x': [1, 0, 0], '-x': [-1, 0, 0],
    '+y': [0, 1, 0], '-y': [0, -1, 0],
    '+z': [0, 0, 1], '-z': [0, 0, -1],
};

// Values BOTH renderers must agree on come from one file, bundled in at build
// time here and read at run time by the Python LIGHT renderer. A colour or a
// face order therefore cannot drift between the two (root Rules 5 and 19).
import SHARED from '../shared/spec.json';

const FACE_ORDER = SHARED.faceOrder;   // also BoxGeometry's group order

// The owner's six pole hues (decree 2026-07-28). One table serves both the
// axes gizmo and the cube's faces — the pole colour is a property of the
// DIRECTION, not of the shape that happens to point that way.
export const POLE_COLORS = SHARED.poles;
const NEUTRAL = SHARED.neutral;

// Face colours in FACE_ORDER — the default dress of a coloured cube.
export const POLE_FACE_COLORS = FACE_ORDER.map((face) => POLE_COLORS[face]);

// Default specs double as the parameter reference — every field here is
// overridable through the spec object (root Rule #4).
export const AXES_DEFAULTS = {
    armLength: 1,
    armRadius: 0.03,
    // The owner's pole palette (2026-07-28) — the same six hues dress the
    // cube's faces, so an axis and the face it points at always agree.
    arms: [
        { axis: '+x', color: POLE_COLORS['+x'], label: 'X+' },
        { axis: '-x', color: POLE_COLORS['-x'], label: 'X−' },
        { axis: '+y', color: POLE_COLORS['+y'], label: 'Y+' },
        { axis: '-y', color: POLE_COLORS['-y'], label: 'Y−' },
        { axis: '+z', color: POLE_COLORS['+z'], label: 'Z+' },
        { axis: '-z', color: POLE_COLORS['-z'], label: 'Z−' },
    ],
};

export const CUBE_DEFAULTS = {
    size: 1,
    color: NEUTRAL.body,
    // Per-face colours: an array in FACE_ORDER, or the string 'poles' for the
    // pole palette above. A host asks for 'poles' by name instead of copying
    // six hex values it would then have to keep in sync (root Rule 19).
    colors: null,
    edges: true,
};

const BUILDERS = {
    axes: buildAxes,
    cube: buildCube,
};

// Universal spec fields, honoured for every primitive:
//   name      — the part name this group is addressed by
//   position  — [x, y, z] offset
//   scale     — uniform scale factor
//   children  — nested specs, so an assembly is one JSON tree
export function buildPrimitive(spec) {
    const build = BUILDERS[spec.type];
    if (!build) {
        throw new Error(`Unknown primitive type '${spec.type}' — available: ${Object.keys(BUILDERS).join(', ')}`);
    }
    const group = build(spec);
    if (spec.name) group.name = spec.name;
    if (spec.position) group.position.set(...spec.position);
    if (spec.scale) group.scale.setScalar(spec.scale);
    for (const child of spec.children ?? []) group.add(buildPrimitive(child));
    return group;
}

function standardMaterial(color) {
    return new THREE.MeshStandardMaterial({ color, roughness: 0.35, metalness: 0.15 });
}

function named(object, name) {
    object.name = name;
    return object;
}

// Axes gizmo: up to 6 arms from the origin, each its own group, color and
// label(s). One arm = cylinder shaft (80% of length) + cone tip (20%),
// oriented by the quaternion that maps +Y (the cylinder's native axis) onto
// the arm direction.
//
// `label` may be a string or an ARRAY of strings. An array builds a switch
// group `labels` holding `label:0`, `label:1`, … with only the first visible —
// the "three legend terms for one arm tip, one shown at a time" case.
function buildAxes(spec) {
    const { armLength, armRadius, arms } = { ...AXES_DEFAULTS, ...spec };
    const group = named(new THREE.Group(), 'axes');
    const shaftLength = armLength * 0.8;
    const tipLength = armLength * 0.2;
    const up = new THREE.Vector3(0, 1, 0);

    group.add(named(new THREE.Mesh(
        new THREE.SphereGeometry(armRadius * 2, 24, 16),
        new THREE.MeshStandardMaterial({ color: NEUTRAL.joint, roughness: 0.4, metalness: 0.3 }),
    ), 'joint'));

    for (const arm of arms) {
        const axis = AXIS_DIRECTIONS[arm.axis];
        if (!axis) {
            throw new Error(`Unknown arm axis '${arm.axis}' — expected one of: ${Object.keys(AXIS_DIRECTIONS).join(', ')}`);
        }
        const direction = new THREE.Vector3(...axis);
        const orient = new THREE.Quaternion().setFromUnitVectors(up, direction);
        const armGroup = named(new THREE.Group(), `arm:${arm.axis}`);
        // An arm's colour defaults to its pole hue, so a host that only cares
        // about the LABELS never has to restate the palette.
        const color = arm.color ?? POLE_COLORS[arm.axis];

        // Shaft and tip get their OWN material each: sharing one would make any
        // later opacity change on the shaft silently dim the tip as well.
        const shaft = named(new THREE.Mesh(
            new THREE.CylinderGeometry(armRadius, armRadius, shaftLength, 20),
            standardMaterial(color),
        ), 'shaft');
        shaft.quaternion.copy(orient);
        shaft.position.copy(direction).multiplyScalar(shaftLength / 2);
        armGroup.add(shaft);

        const tip = named(new THREE.Mesh(
            new THREE.ConeGeometry(armRadius * 2.4, tipLength, 24),
            standardMaterial(color),
        ), 'tip');
        tip.quaternion.copy(orient);
        tip.position.copy(direction).multiplyScalar(shaftLength + tipLength / 2);
        armGroup.add(tip);

        if (arm.label) armGroup.add(buildArmLabels(arm, color, direction, armLength));
        group.add(armGroup);
    }
    return group;
}

function buildArmLabels(arm, color, direction, armLength) {
    const texts = Array.isArray(arm.label) ? arm.label : [arm.label];
    const holder = named(new THREE.Group(), 'labels');
    texts.forEach((text, index) => {
        const sprite = named(makeLabelSprite(text, {
            color,
            worldHeight: armLength * 0.16,
        }), `label:${index}`);
        sprite.position.copy(direction).multiplyScalar(armLength * 1.16);
        sprite.visible = index === 0;   // a switch group: exactly one child shown
        holder.add(sprite);
    });
    return holder;
}

// Cube. A single `color` builds one `body` mesh; per-face `colors` build six
// separately named face meshes (`face:+x` …) instead of one mesh with six
// material slots — a material slot cannot be hidden or dimmed on its own,
// and a face nobody can address is a face nobody can look through.
function buildCube(spec) {
    const { size, color, colors, edges } = { ...CUBE_DEFAULTS, ...spec };
    const group = named(new THREE.Group(), 'cube');
    const faceColors = colors === 'poles' ? POLE_FACE_COLORS : colors;

    if (faceColors) {
        if (faceColors.length !== FACE_ORDER.length) {
            throw new Error(`cube 'colors' needs ${FACE_ORDER.length} entries in order ${FACE_ORDER.join(', ')}, or the string 'poles'`);
        }
        FACE_ORDER.forEach((face, index) => {
            group.add(named(buildFace(face, size, faceColors[index]), `face:${face}`));
        });
    } else {
        group.add(named(new THREE.Mesh(new THREE.BoxGeometry(size, size, size), standardMaterial(color)), 'body'));
    }

    if (edges) {
        group.add(named(new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(size, size, size)),
            new THREE.LineBasicMaterial({ color: NEUTRAL.edges, transparent: true, opacity: 0.35 }),
        ), 'edges'));
    }
    return group;
}

// One face: a plane pushed out to the cube's surface and turned to face
// outward. DoubleSide so the inside of a dimmed cube still reads as a solid.
function buildFace(face, size, color) {
    const direction = new THREE.Vector3(...AXIS_DIRECTIONS[face]);
    const material = standardMaterial(color);
    material.side = THREE.DoubleSide;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(size, size), material);
    mesh.position.copy(direction).multiplyScalar(size / 2);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), direction);
    return mesh;
}
