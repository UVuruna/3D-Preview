// The Switcher — which vocabulary speaks, and which readings are lit.
//
// Two independent controls, per the owner's spec:
//
//     register   canon / myth / historical / movie — swaps every visible label
//     reading    Luminous / Fallen / Both — 'both' draws the five-station
//                radial layout, because the two stops are already at their
//                two radii (see modelscene.js)
//
// Both are FLAT parameters. Nothing here is a mode with its own code path: a
// switcher position resolves to a list of ordinary part operations — the same
// showOnly and setPartVisible a host could call by hand — so a timeline can
// drive `switcher.register` exactly like any other channel, and no renderer
// needs a second way of doing it.
//
// The convention it works by is stated in MODELS.md: a seat carries one group
// per STOP ('luminous', 'fallen'), each holding one `label:<register>` per
// register. Anything built that way is switchable.
//
// Mirror of preview3d/switcher.py.

import SHARED from '../shared/spec.json';

// ═══════════════════════════ SWITCHER STATE ═══════════════════════════

const CONFIG = SHARED.switcher;

export const REGISTERS = CONFIG.registers;
export const READINGS = CONFIG.readings;
export const STOPS = CONFIG.stops;
export const DEFAULT_REGISTER = CONFIG.defaultRegister;
export const DEFAULT_READING = CONFIG.defaultReading;
export const LABEL_PREFIX = 'label:';

export const DEFAULT_STATE = Object.freeze({
    register: DEFAULT_REGISTER,
    reading: DEFAULT_READING,
});

// ═══════════════════════════ STATE OPERATIONS ═══════════════════════════

// A complete, checked switcher state — unknown values fail loudly.
export function normalise(state, register, reading) {
    const result = { ...DEFAULT_STATE, ...(state ?? {}) };
    if (register != null) result.register = register;
    if (reading != null) result.reading = reading;
    if (!REGISTERS.includes(result.register)) {
        throw new Error(`Unknown register '${result.register}' — available: ${REGISTERS.join(', ')}`);
    }
    if (!READINGS.includes(result.reading)) {
        throw new Error(`Unknown reading '${result.reading}' — available: ${READINGS.join(', ')}`);
    }
    return result;
}

// Which radial stops a reading lights. Anything that is not one stop lights all
// of them, which is what 'both' means.
export function litStops(reading) {
    return STOPS.includes(reading) ? [reading] : [...STOPS];
}

// The part operations that put `parts` into this switcher position. `parts` is
// a part list as either renderer reports it; the result is ['visible', path,
// on] and ['show_only', path, child] in a fixed order, so both renderers apply
// exactly the same sequence.
export function operations(parts, state) {
    const checked = normalise(state);
    const lit = litStops(checked.reading);
    const child = LABEL_PREFIX + checked.register;
    const result = [];
    for (const part of parts) {
        const stop = part.path.split('/').pop();
        if (!STOPS.includes(stop)) continue;
        result.push(['visible', part.path, lit.includes(stop)]);
        result.push(['show_only', part.path, child]);
    }
    return result;
}
