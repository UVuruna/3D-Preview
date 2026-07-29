// 3D Preview — public API.
// Bundled by esbuild as an IIFE with global name `Preview3D` (see package.json),
// so consumers use either `Preview3D.mount(el)` from a script tag or
// `import { mount } from './index.js'` when bundling themselves.

import { Viewer } from './viewer.js';
import SHARED_SCENES from '../shared/scenes.json';

export { Viewer, VIEWER_DEFAULTS } from './viewer.js';
export { buildPrimitive, armName, AXES_DEFAULTS, CUBE_DEFAULTS, MARKER_DEFAULTS, POLE_COLORS, POLE_FACE_COLORS } from './primitives.js';
export { makeLabelSprite } from './labels.js';
export { VIEW_PRESETS, VIEW_ORDER, FREE_VIEW } from './views.js';
export { KEYBOARD_DEFAULTS } from './keyboard.js';
export { GRID_DEFAULTS } from './grid.js';
export { Timeline, ANIMATION_DEFAULTS, CHANNELS, NO_ANIMATION, ease, sampleTrack } from './animation.js';

// The model layer: the direction grammar, the computed palette, the cube's
// orientations, the schema, the model-to-scene translation and the Switcher.
// Exported because a consumer builds and validates its own model (MODELS.md).
export {
    AXIS_TIERS, LETTERS, TIER_ORDER, canonicalToken, cubeAxes, cubeTokens,
    oppositeToken, parseDirection, tierOf, tokenOf, tokenVector,
} from './directions.js';
export { SACRED, blend, colorFor, deriveAll, distance, mix, verifyPalette } from './axiscolors.js';
export { FACE_ORDER, orientationAxes, orientationIds, snapAngles, stepOrientation } from './orientations.js';
export { TYPES as MODEL_TYPES, validate as validateModel } from './model.js';
export { GROUP_PATHS, buildSpec, findView, viewOpacities } from './modelscene.js';
export { DEMO_VOCABULARY, DEFAULT_VIEWS, buildCubeModel } from './cubemodel.js';
export {
    READINGS, REGISTERS, STOPS, DEFAULT_STATE as SWITCHER_DEFAULT,
    litStops, normalise as normaliseSwitcher, operations as switcherOperations,
} from './switcher.js';

// The scene descriptors that ship with the component (SCENES.md). Read from
// shared/scenes.json, so the LIGHT renderer plays exactly the same ones.
export const SCENES = SHARED_SCENES.scenes;

export function mount(container, options) {
    return new Viewer(container, options);
}
