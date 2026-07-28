// Text labels as sprites — text is drawn onto a 2D canvas at runtime and
// mounted as a camera-facing sprite (computed, never an image asset — Rule #19).

import * as THREE from 'three';

export const LABEL_DEFAULTS = {
    color: '#F5F5F5',
    fontSize: 96,        // canvas px — rendered large, scaled down for crispness
    fontWeight: 600,
    fontFamily: 'Inter, "Segoe UI", system-ui, sans-serif',
    padding: 24,         // canvas px around the text
    worldHeight: 0.15,   // sprite height in scene units
};

export function makeLabelSprite(text, options = {}) {
    const opts = { ...LABEL_DEFAULTS, ...options };
    const font = `${opts.fontWeight} ${opts.fontSize}px ${opts.fontFamily}`;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.font = font;
    canvas.width = Math.ceil(ctx.measureText(text).width) + opts.padding * 2;
    canvas.height = Math.ceil(opts.fontSize * 1.25) + opts.padding * 2;

    ctx.font = font;   // canvas resize resets context state
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = opts.color;
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.anisotropy = 4;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true }));
    sprite.scale.set(opts.worldHeight * (canvas.width / canvas.height), opts.worldHeight, 1);
    return sprite;
}
