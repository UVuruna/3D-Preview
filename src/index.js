// 3D Preview — public API.
// Bundled by esbuild as an IIFE with global name `Preview3D` (see package.json),
// so consumers use either `Preview3D.mount(el)` from a script tag or
// `import { mount } from './index.js'` when bundling themselves.

import { Viewer } from './viewer.js';

export { Viewer } from './viewer.js';
export { buildPrimitive } from './primitives.js';
export { makeLabelSprite } from './labels.js';

export function mount(container, options) {
    return new Viewer(container, options);
}
