// The colour of an axis end, COMPUTED from the poles it lies between.
//
// Owner decree 2026-07-28, and a direct application of root Rule 19: a colour
// per axis would be twenty-six invented values to keep in sync, where four
// rules cover every direction the cube has.
//
//     primary    the sealed pole hue itself
//     secondary  the blend of its two poles, THINNED BY MOONLIGHT
//     tertiary   the blend of its three poles, DEEPENED toward ink
//     sacred     none of the six — white-gold, the seventh dress
//
// The moonlight thinning is not decoration. A naive two-pole blend can land on
// a hue the palette already spends (the blue+yellow case the canon names), and
// two seats wearing one colour is a lie about the structure. Thinning the whole
// edge family toward a pale moonlight moves it off the saturated pole ring, so
// the collision cannot happen by construction rather than by luck —
// `verifyPalette` fails loudly if it ever does anyway (Rule 1).
//
// Mirror of preview3d/axis_colors.py. Both read `poles` and `axisColors` from
// shared/spec.json, so neither can restate a value; the two arrive at the same
// hex because they round the same way (Math.round, matched in Python).

import SHARED from '../shared/spec.json';
import { cubeTokens, tierOf, tokenLetters } from './directions.js';

const POLE_COLORS = SHARED.poles;
const COLORS = SHARED.axisColors;

export const MOONLIGHT = COLORS.moonlight;
export const THIN = COLORS.thin;
export const INK = COLORS.ink;
export const DEEPEN = COLORS.deepen;
export const SACRED = COLORS.sacred;
export const MIN_POLE_DISTANCE = COLORS.minPoleDistance;
export const MIN_SEAT_DISTANCE = COLORS.minSeatDistance;

export function hexToRgb(color) {
    if (typeof color !== 'string' || color.length !== 7 || color[0] !== '#') {
        throw new Error(`Unusable colour '${color}' — expected '#rrggbb'`);
    }
    const value = Number.parseInt(color.slice(1), 16);
    if (Number.isNaN(value)) throw new Error(`Unusable colour '${color}' — expected '#rrggbb'`);
    return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

export function rgbToHex(rgb) {
    return `#${rgb.map((c) => Math.max(0, Math.min(255, Math.trunc(c)))
        .toString(16).padStart(2, '0')).join('').toUpperCase()}`;
}

// Move `t` of the way from colour `a` to colour `b`, per channel.
export function mix(a, b, t) {
    const left = hexToRgb(a);
    const right = hexToRgb(b);
    return rgbToHex(left.map((channel, i) => Math.round(channel + (right[i] - channel) * t)));
}

// The per-channel mean. One colour blends to itself, which is what makes the
// primary case the same rule as the others rather than an exception.
export function blend(colors) {
    if (!colors.length) throw new Error('Cannot blend an empty list of colours');
    const channels = colors.map(hexToRgb);
    return rgbToHex([0, 1, 2].map(
        (i) => Math.round(channels.reduce((sum, channel) => sum + channel[i], 0) / channels.length),
    ));
}

// The pole hues a direction token lies between, in the token's own order.
export function polesOf(token) {
    return tokenLetters(token).map(([letter, sign]) => POLE_COLORS[(sign > 0 ? '+' : '-') + letter]);
}

// The colour of the axis end (or the cell) that `token` points at.
export function colorFor(token, tier) {
    if (tier === 'sacred') return SACRED;
    const poles = polesOf(token);
    const base = blend(poles);
    if (poles.length === 1) return base;
    if (poles.length === 2) return mix(base, MOONLIGHT, THIN);
    return mix(base, INK, DEEPEN);
}

// Straight-line distance in RGB — good enough to prove two colours are not the
// same colour, which is all the collision rule asks.
export function distance(a, b) {
    const left = hexToRgb(a);
    const right = hexToRgb(b);
    return Math.hypot(left[0] - right[0], left[1] - right[1], left[2] - right[2]);
}

// The collision rule, enforced: no derived colour may sit on a pole hue, and no
// two seats may collapse into one colour.
export function verifyPalette(colors) {
    const collisions = [];
    for (const [token, color] of Object.entries(colors)) {
        if (tokenLetters(token).length === 1) continue;      // a pole IS its pole hue
        for (const [pole, poleColor] of Object.entries(POLE_COLORS)) {
            if (distance(color, poleColor) < MIN_POLE_DISTANCE) {
                collisions.push(`${token} (${color}) collides with the ${pole} pole (${poleColor})`);
            }
        }
    }
    const tokens = Object.keys(colors).sort();
    for (let i = 0; i < tokens.length; i++) {
        for (let j = i + 1; j < tokens.length; j++) {
            const apart = distance(colors[tokens[i]], colors[tokens[j]]);
            if (apart < MIN_SEAT_DISTANCE) {
                collisions.push(
                    `${tokens[i]} (${colors[tokens[i]]}) and ${tokens[j]} `
                    + `(${colors[tokens[j]]}) are only ${apart.toFixed(1)} apart`,
                );
            }
        }
    }
    if (collisions.length) {
        throw new Error(
            'The computed axis palette collides — shared/spec.json axisColors needs '
            + `adjusting: ${collisions.sort().join('; ')}`,
        );
    }
}

// Every one of the cube's 26 directions dressed by its GEOMETRY alone. The
// sacred dress is deliberately not applied here: which body diagonal is sacred
// is a model's statement about meaning, not something the cube knows.
export function deriveAll() {
    const colors = {};
    for (const letters of [1, 2, 3]) {
        for (const token of cubeTokens(letters)) colors[token] = colorFor(token, tierOf(token));
    }
    verifyPalette(colors);
    return colors;
}
