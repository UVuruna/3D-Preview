// View presets — the standard directions a technical previewer offers, plus
// the ordering used when cycling through them with a key or a button.

// `direction` points FROM the content TOWARD the camera.
export const VIEW_PRESETS = {
    iso: { label: 'Isometric', direction: [1, 1, 1] },
    front: { label: 'Front', direction: [0, 0, 1] },
    right: { label: 'Right', direction: [1, 0, 0] },
    back: { label: 'Back', direction: [0, 0, -1] },
    left: { label: 'Left', direction: [-1, 0, 0] },
    top: { label: 'Top', direction: [0, 1, 0] },
    bottom: { label: 'Bottom', direction: [0, -1, 0] },
};

export const VIEW_ORDER = Object.keys(VIEW_PRESETS);

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
