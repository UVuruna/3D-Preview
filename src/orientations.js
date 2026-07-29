// The cube's twenty-four orientations, COMPUTED.
//
// A cube can be set down in exactly 24 ways, and they are the product of two
// choices, not a table of 24 matrices to copy: pick which face points up (6),
// then how far it is spun about that direction (4). Root Rule 19 in its
// plainest form — define how the piece moves and every position follows.
//
// Each orientation is named `<face>:<spin>`, e.g. '+y:0' (the identity) or
// '-z:2'. They enumerate in the shared face order, spins 0..3, so a "next
// orientation" step means the same thing in both renderers.
//
// Also here: `snapAngles`, which turns any direction into the azimuth and
// elevation a camera must stand at to look down it — the snap views, including
// the four body diagonals no preset covers.
//
// Mirror of preview3d/orientations.py.

import SHARED from '../shared/spec.json';
import { parseDirection } from './directions.js';

export const FACE_ORDER = SHARED.faceOrder;
export const SPINS = 4;
const POLE_LIMIT = 89.99;      // the camera's own clamp; snapping must not exceed it

const WORLD_UP = [0, 1, 0];
const WORLD_FORWARD = [0, 0, 1];

function cross(a, b) {
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ];
}

function normalise(v) {
    const length = Math.hypot(v[0], v[1], v[2]);
    return [v[0] / length, v[1] / length, v[2] / length];
}

function combine(a, b, wa, wb) {
    return [a[0] * wa + b[0] * wb, a[1] * wa + b[1] * wb, a[2] * wa + b[2] * wb];
}

// All 24 ids, in the order a stepped auto-advance walks them.
export function orientationIds() {
    const ids = [];
    for (const face of FACE_ORDER) {
        for (let spin = 0; spin < SPINS; spin++) ids.push(`${face}:${spin}`);
    }
    return ids;
}

// The rotation named by `<face>:<spin>`, as [right, up, forward] — where the
// cube's own +X, +Y and +Z end up. It takes the cube's +Y onto the world
// direction `face`, then spins by `spin` quarter turns about it, so '+y:0' is
// the identity and a freshly shown model starts unrotated without anyone
// saying so.
export function orientationAxes(identifier) {
    const [face, spinText] = String(identifier).split(':');
    const spin = Number(spinText);
    if (!FACE_ORDER.includes(face) || !Number.isInteger(spin) || spin < 0 || spin >= SPINS) {
        throw new Error(
            `Unknown orientation '${identifier}' — expected '<face>:<spin>' with face in `
            + `${FACE_ORDER.join(', ')} and spin 0..${SPINS - 1}`,
        );
    }
    const up = parseDirection(face);
    // The same degenerate-case rule the cameras use, so "which way is spin 0"
    // is one decision in this component rather than two.
    const reference = Math.abs(up[1]) > 0.999 ? WORLD_FORWARD : WORLD_UP;
    const right0 = normalise(cross(up, reference));
    const angle = (Math.PI / 2) * spin;
    const right = combine(right0, cross(up, right0), Math.cos(angle), Math.sin(angle));
    return [right, up, cross(right, up)];
}

export function stepOrientation(identifier, step) {
    const ids = orientationIds();
    const index = ids.indexOf(identifier);
    if (index === -1) return step > 0 ? ids[0] : ids[ids.length - 1];
    return ids[(index + step + ids.length) % ids.length];
}

// (azimuth, elevation) in degrees for a camera looking DOWN `direction`.
// `direction` points from the content toward the camera, matching the view
// presets, so snapAngles('+x+y+z') is the body-diagonal view the hexagram
// lives on.
export function snapAngles(direction) {
    const [x, y, z] = parseDirection(direction);
    const horizontal = Math.hypot(x, z);
    const azimuth = horizontal ? (Math.atan2(x, z) * 180) / Math.PI : 0;
    const elevation = horizontal
        ? (Math.atan2(y, horizontal) * 180) / Math.PI
        : (y > 0 ? POLE_LIMIT : -POLE_LIMIT);
    return { azimuth, elevation: Math.max(-POLE_LIMIT, Math.min(POLE_LIMIT, elevation)) };
}
