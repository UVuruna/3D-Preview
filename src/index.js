// 3D Preview — public API.
// Bundled by esbuild as an IIFE with global name `Preview3D` (see package.json),
// so consumers use either `Preview3D.mount(el)` from a script tag or
// `import { mount } from './index.js'` when bundling themselves.

import { Viewer } from './viewer.js';

export { Viewer, VIEWER_DEFAULTS } from './viewer.js';
export { buildPrimitive, AXES_DEFAULTS, CUBE_DEFAULTS, POLE_COLORS, POLE_FACE_COLORS } from './primitives.js';
export { makeLabelSprite } from './labels.js';
export { VIEW_PRESETS, VIEW_ORDER, FREE_VIEW } from './views.js';
export { KEYBOARD_DEFAULTS } from './keyboard.js';
export { GRID_DEFAULTS } from './grid.js';

export function mount(container, options) {
    return new Viewer(container, options);
}
