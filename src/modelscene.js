// Model data to a scene SPEC — the one translation, in plain data.
//
// A model says what exists (axes, seats, words); a scene spec says what to draw
// (primitives, names, colours). This module is the whole bridge, and it
// produces nothing but the same JSON specs a host could have written by hand —
// so both renderers build a model through the primitive builders they already
// have, rather than each growing its own model renderer.
//
// The tree it builds is fixed, and every group in it exists whether or not it
// has anything in it:
//
//     <root>/
//       axes/    primary/ secondary/ tertiary/ sacred/   ← a tier group each
//       cells/   faces/ edges/ vertices/ centre/         ← a kind group each
//       glass                                            ← the shell
//
// That skeleton is a contract, not a convenience: a VIEW addresses those paths
// to say which family speaks, so a missing group would be a view that fails
// halfway through instead of one that dims nothing.
//
// Mirror of preview3d/model_scene.py, pinned against it through the renderers
// by tests/test_model_parity.py.

import SHARED from '../shared/spec.json';
import { parseDirection } from './directions.js';

const TIERS = Object.fromEntries(
    Object.entries(SHARED.axisTiers).filter(([name]) => !name.startsWith('_')),
);
export const TIER_ORDER = SHARED.tierOrder;
const KINDS = Object.fromEntries(
    Object.entries(SHARED.cellKinds).filter(([name]) => !name.startsWith('_')),
);
export const KIND_ORDER = SHARED.cellKindOrder;
const SCENE = SHARED.modelScene;
const RADIAL = SHARED.switcher.radial;
export const STOPS = SHARED.switcher.stops;

export const AXES_GROUP = 'axes';
export const CELLS_GROUP = 'cells';
export const GLASS_GROUP = 'glass';

// Short group name -> the path a view addresses it by. A view speaks in
// families ('secondary', 'glass'); the tree speaks in paths.
export const GROUP_PATHS = {
    ...Object.fromEntries(TIER_ORDER.map((tier) => [tier, `${AXES_GROUP}/${tier}`])),
    ...Object.fromEntries(KIND_ORDER.map((kind) => [kind, `${CELLS_GROUP}/${KINDS[kind].group}`])),
    [GLASS_GROUP]: GLASS_GROUP,
};

export function rootName(model) {
    return model.root || 'model';
}

export function findView(model, viewName) {
    const view = model.views.find((candidate) => candidate.name === viewName);
    if (!view) {
        throw new Error(
            `Model '${model.name}' has no view '${viewName}' — available: `
            + model.views.map((candidate) => candidate.name).join(', '),
        );
    }
    return view;
}

// A view's opacity map, keyed by FULL part path.
export function viewOpacities(model, viewName) {
    const prefix = rootName(model);
    return Object.fromEntries(
        Object.entries(findView(model, viewName).opacity)
            .map(([path, alpha]) => [`${prefix}/${path}`, Number(alpha)]),
    );
}

// The whole model as one nested primitive spec.
export function buildSpec(model) {
    const size = Number(model.size ?? 1);
    const registers = [...model.registers];
    return {
        type: 'group',
        name: rootName(model),
        children: [axesGroup(model, size, registers), cellsGroup(model, size, registers), glass(model, size)],
    };
}

// ---- Axes -------------------------------------------------------------------

function axesGroup(model, size, registers) {
    const byTier = Object.fromEntries(TIER_ORDER.map((tier) => [tier, []]));
    for (const axis of model.axes) byTier[axis.tier].push(buildAxis(axis, size, registers));
    return {
        type: 'group',
        name: AXES_GROUP,
        children: TIER_ORDER.map((tier) => ({ type: 'group', name: tier, children: byTier[tier] })),
    };
}

function buildAxis(axis, size, registers) {
    const tier = TIERS[axis.tier];
    const length = Number(tier.length) * size;
    return {
        type: 'axes',
        name: `axis:${axis.id}`,
        armLength: length,
        armRadius: Number(tier.radius) * size,
        // One joint per axis would put thirteen spheres in the same spot; the
        // centre seat is the crossing point the model actually names.
        joint: false,
        arms: axis.ends.map((end) => buildArm(end, length, registers)),
    };
}

// One half-axis, with its two radial stops. The radial law is geometry here,
// not a caption: the luminous stop sits INSIDE the geometric end and the fallen
// stop PAST it, so a reading of 'both' draws the five stations by itself.
function buildArm(end, length, registers) {
    const direction = parseDirection(end.direction);
    return {
        axis: typeof end.direction === 'string' ? end.direction : [...direction],
        color: end.color,
        stopHeight: Number(SCENE.armLabelHeight) * length,
        stops: STOPS.map((stop) => ({
            name: stop,
            anchor: direction.map((component) => component * length * Number(RADIAL[stop])),
            labels: Object.fromEntries(registers.map((register) => [register, end.names[register][stop]])),
        })),
    };
}

// ---- Cells ------------------------------------------------------------------

function cellsGroup(model, size, registers) {
    const byKind = Object.fromEntries(KIND_ORDER.map((kind) => [kind, []]));
    for (const cell of model.cells ?? []) byKind[cell.kind].push(buildCell(cell, size, registers));
    return {
        type: 'group',
        name: CELLS_GROUP,
        children: KIND_ORDER.map((kind) => ({
            type: 'group', name: KINDS[kind].group, children: byKind[kind],
        })),
    };
}

// A seat: a small marker plus its two readings, stacked around it. Seats do not
// carry the axes' radial law — a seat IS a station — so its two readings simply
// sit above and below the marker, which keeps them legible when twenty-seven of
// them are on screen at once.
function buildCell(cell, size, registers) {
    const gap = Number(SCENE.cellLabelGap) * size;
    return {
        type: 'marker',
        name: `cell:${cell.id}`,
        position: [...cell.position],
        radius: Number(KINDS[cell.kind].radius) * size,
        color: cell.color,
        stopHeight: Number(SCENE.labelHeight) * size,
        stops: STOPS.map((stop) => ({
            name: stop,
            anchor: [0, stop === STOPS[0] ? gap : -gap, 0],
            labels: Object.fromEntries(registers.map((register) => [register, cell.names[register][stop]])),
        })),
    };
}

// ---- Glass ------------------------------------------------------------------

// The shell the seats are seen through — an empty group when there is none, so
// a view can always address the path.
function glass(model, size) {
    if (!model.glass) return { type: 'group', name: GLASS_GROUP, children: [] };
    return {
        type: 'cube',
        name: GLASS_GROUP,
        size,
        colors: model.glass.colors ? [...model.glass.colors] : 'poles',
    };
}
