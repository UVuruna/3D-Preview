// View presets — the standard directions a technical previewer offers, plus
// the ordering used when cycling through them with a key or a button.
//
// Read from shared/spec.json so the LIGHT renderer offers exactly the same
// presets in the same order (root Rules 5 and 19).

import SHARED from '../shared/spec.json';

// `direction` points FROM the content TOWARD the camera.
export const VIEW_PRESETS = SHARED.views;
export const VIEW_ORDER = SHARED.viewOrder;

// The name reported once the user has orbited away from any preset.
export const FREE_VIEW = 'free';

export function viewDirection(name) {
    const preset = VIEW_PRESETS[name];
    if (!preset) {
        throw new Error(`Unknown view '${name}' — available: ${VIEW_ORDER.join(', ')}`);
    }
    return preset.direction;
}

// Next preset in cycle order. From a free view, stepping forward lands on the
// first preset rather than jumping somewhere arbitrary.
export function stepView(current, step) {
    const index = VIEW_ORDER.indexOf(current);
    if (index === -1) return VIEW_ORDER[step > 0 ? 0 : VIEW_ORDER.length - 1];
    return VIEW_ORDER[(index + step + VIEW_ORDER.length) % VIEW_ORDER.length];
}
