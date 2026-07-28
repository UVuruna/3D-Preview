// Ground grid — an optional reference plane under the content, sized to it.
// Computed from the content's bounds every time the content changes (Rule #19),
// never a fixed 10x10 helper that is wrong for anything but a unit cube.

import * as THREE from 'three';

export const GRID_DEFAULTS = {
    lineColor: '#8A8AA0',      // minor lines
    centerColor: '#B4B4C8',    // the two axis lines through the origin
    opacity: 0.28,
    spanFactor: 2.5,           // grid width relative to the content's footprint
    targetCells: 12,           // aim for ~this many cells across; step is rounded
};

// Round a raw step up to the nearest 1/2/5 x 10^n, so cell size is a number a
// human can read off the grid ("one cell = 0.5") instead of 0.3874.
function niceStep(raw) {
    const magnitude = 10 ** Math.floor(Math.log10(raw));
    const normalized = raw / magnitude;
    const rounded = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
    return rounded * magnitude;
}

// Returns {grid, step} — the helper sits on the content's floor, centred under
// it. Returns null when there is nothing to measure.
export function buildGrid(content, options = {}) {
    const opts = { ...GRID_DEFAULTS, ...options };
    const box = new THREE.Box3().setFromObject(content);
    if (box.isEmpty()) return null;

    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const footprint = Math.max(size.x, size.z, size.y * 0.5) || 1;
    const span = footprint * opts.spanFactor;
    const step = niceStep(span / opts.targetCells);
    const divisions = Math.max(2, Math.round(span / step));
    const extent = divisions * step;

    const grid = new THREE.GridHelper(extent, divisions, opts.centerColor, opts.lineColor);
    grid.material.transparent = true;
    grid.material.opacity = opts.opacity;
    grid.material.depthWrite = false;   // the grid never occludes the model
    grid.position.set(center.x, box.min.y, center.z);
    grid.name = 'grid';
    return { grid, step };
}

export function disposeGrid(grid) {
    grid.geometry.dispose();
    grid.material.dispose();
    grid.removeFromParent();
}
