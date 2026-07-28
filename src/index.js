// 3D Preview — public API.
// Bundled by esbuild as an IIFE with global name `Preview3D` (see package.json),
// so consumers use either `Preview3D.mount(el)` from a script tag or
// `import { mount } from './index.js'` when bundling themselves.

import { Viewer } from './viewer.js';
import SHARED_SCENES from '../shared/scenes.json';

export { Viewer, VIEWER_DEFAULTS } from './viewer.js';
export { buildPrimitive, AXES_DEFAULTS, CUBE_DEFAULTS, POLE_COLORS, POLE_FACE_COLORS } from './primitives.js';
export { makeLabelSprite } from './labels.js';
export { VIEW_PRESETS, VIEW_ORDER, FREE_VIEW } from './views.js';
export { KEYBOARD_DEFAULTS } from './keyboard.js';
export { GRID_DEFAULTS } from './grid.js';
export { Timeline, ANIMATION_DEFAULTS, CHANNELS, NO_ANIMATION, ease, sampleTrack } from './animation.js';

// The scene descriptors that ship with the component (SCENES.md). Read from
// shared/scenes.json, so the LIGHT renderer plays exactly the same ones.
export const SCENES = SHARED_SCENES.scenes;

export function mount(container, options) {
    return new Viewer(container, options);
}
