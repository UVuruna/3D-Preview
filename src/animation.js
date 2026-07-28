// Timeline — the animation driver. Scenes are DATA: keyframes and easing over
// flat parameters, never hardcoded choreography, so a new scene is written in
// JSON without touching either renderer.
//
// This module knows nothing about the renderer. `sample()` resolves every track
// to a plain {channel, path, value} entry and the Viewer applies them, which is
// what lets the LIGHT renderer run the identical scene through its own
// applier. The mirror implementation is preview3d/light/animation.py; the
// values both read — fps, easing names, the channel table — live in
// shared/spec.json, and tests/test_animation_parity.py pins that they agree.

import SHARED from '../shared/spec.json';

export const ANIMATION_DEFAULTS = SHARED.animation;
export const CHANNELS = ANIMATION_DEFAULTS.channels;

// Cubic curves — the standard set. `step` holds the outgoing value until the
// next key, which is also what any non-numeric value does automatically.
const EASINGS = {
    'linear': (t) => t,
    'ease-in': (t) => t * t * t,
    'ease-out': (t) => 1 - (1 - t) ** 3,
    'ease-in-out': (t) => (t < 0.5 ? 4 * t ** 3 : 1 - ((-2 * t + 2) ** 3) / 2),
    'step': () => 0,
};

// The shared spec advertises the curve names to scene authors; disagreeing with
// what is actually implemented would be a silent authoring trap (Rule #1).
for (const name of ANIMATION_DEFAULTS.easings) {
    if (!EASINGS[name]) throw new Error(`shared/spec.json lists easing '${name}', which animation.js does not implement`);
}

// Reported when no scene is loaded, so a host's readout never special-cases null.
export const NO_ANIMATION = Object.freeze({
    scene: null,
    label: '',
    playing: false,
    time: 0,
    duration: 0,
    progress: 0,
    speed: ANIMATION_DEFAULTS.defaultSpeed,
    frame: 0,
    frames: 0,
    loop: false,
});

export function ease(name, t) {
    const curve = EASINGS[name];
    if (!curve) {
        throw new Error(`Unknown easing '${name}' — available: ${Object.keys(EASINGS).join(', ')}`);
    }
    return curve(t);
}

const clamp = (value, low, high) => Math.min(high, Math.max(low, value));

// Validate once, at load: a typo in a scene must fail where the scene is named,
// not silently animate nothing halfway through playback.
function prepareTrack(track, scene) {
    const spec = CHANNELS[track.channel];
    if (!spec) {
        throw new Error(
            `Scene '${scene}': unknown channel '${track.channel}' — available: ${Object.keys(CHANNELS).join(', ')}`,
        );
    }
    if (spec.path && !track.path) {
        throw new Error(`Scene '${scene}': channel '${track.channel}' needs a 'path' to the part it drives`);
    }
    const keys = [...(track.keys ?? [])].sort((a, b) => a.t - b.t);
    if (!keys.length) throw new Error(`Scene '${scene}': channel '${track.channel}' has no keys`);
    for (const key of keys) {
        if (key.ease && !EASINGS[key.ease]) {
            throw new Error(`Scene '${scene}': channel '${track.channel}' uses unknown easing '${key.ease}'`);
        }
    }
    return { channel: track.channel, path: track.path ?? null, keys };
}

// A key's easing governs the segment that STARTS at it. Values that are not
// both numbers cannot be interpolated, so they step — which is exactly what a
// projection name, a visibility flag or a switch-group child needs.
export function sampleTrack(track, progress) {
    const keys = track.keys;
    const last = keys[keys.length - 1];
    if (progress <= keys[0].t) return keys[0].value;
    if (progress >= last.t) return last.value;

    let index = 0;
    while (index < keys.length - 1 && keys[index + 1].t <= progress) index += 1;
    const from = keys[index];
    const to = keys[index + 1];
    const span = to.t - from.t;
    if (span <= 0) return to.value;
    if (typeof from.value !== 'number' || typeof to.value !== 'number') return from.value;

    const eased = ease(from.ease ?? ANIMATION_DEFAULTS.defaultEasing, (progress - from.t) / span);
    return from.value + (to.value - from.value) * eased;
}

export class Timeline {
    constructor(descriptor) {
        this.name = descriptor.name ?? 'scene';
        this.label = descriptor.label ?? this.name;
        this.duration = Number(descriptor.duration ?? ANIMATION_DEFAULTS.defaultDuration);
        if (!(this.duration > 0)) throw new Error(`Scene '${this.name}' needs a positive duration`);
        this.loop = Boolean(descriptor.loop);
        this.fps = ANIMATION_DEFAULTS.fps;
        this.frames = Math.max(1, Math.round(this.duration * this.fps));
        this.tracks = (descriptor.tracks ?? []).map((track) => prepareTrack(track, this.name));

        this.time = 0;
        this.speed = ANIMATION_DEFAULTS.defaultSpeed;
        this.playing = false;
        this._carry = 0;      // leftover wall time not yet spent on a fixed step
    }

    get progress() { return this.time / this.duration; }

    get frame() { return Math.round(this.progress * this.frames); }

    sample(progress) {
        return this.tracks.map((track) => ({
            channel: track.channel,
            path: track.path,
            value: sampleTrack(track, progress),
        }));
    }

    values() { return this.sample(this.progress); }

    // ---- Transport --------------------------------------------------------

    play() {
        if (!this.loop && this.time >= this.duration) this.time = 0;   // replay rather than sit at the end
        this.playing = true;
        this._carry = 0;
    }

    pause() {
        this.playing = false;
        this._carry = 0;
    }

    toggle() { this.playing ? this.pause() : this.play(); }

    stop() {
        this.pause();
        this.time = 0;
    }

    seek(progress) {
        this.time = clamp(progress, 0, 1) * this.duration;
        this._carry = 0;
    }

    // INSTANT mode: the end state without the flight — reduced motion, and what
    // a test drives to assert where a scene lands.
    jumpToEnd() {
        this.pause();
        this.time = this.duration;
    }

    setSpeed(speed) {
        if (!(speed > 0)) throw new Error(`Playback speed must be positive, got ${speed}`);
        this.speed = speed;
    }

    stepFrame(delta) {
        this.pause();
        let next = this.frame + delta;
        if (this.loop) next = ((next % this.frames) + this.frames) % this.frames;
        else next = clamp(next, 0, this.frames);
        this.time = (next / this.frames) * this.duration;
    }

    // ---- Clock ------------------------------------------------------------

    // Fixed timestep: wall time accumulates and is spent in whole 1/fps steps,
    // so the same scene evaluates at the same instants in both renderers no
    // matter what the host's frame rate is. Returns true if the time moved.
    tick(elapsed) {
        if (!this.playing) return false;
        this._carry = Math.min(this._carry + elapsed, ANIMATION_DEFAULTS.maxStep);
        const step = 1 / this.fps;
        let advanced = false;
        while (this.playing && this._carry >= step) {
            this._carry -= step;
            this._advance(step * this.speed);
            advanced = true;
        }
        return advanced;
    }

    state() {
        return {
            scene: this.name,
            label: this.label,
            playing: this.playing,
            time: this.time,
            duration: this.duration,
            progress: this.progress,
            speed: this.speed,
            frame: this.frame,
            frames: this.frames,
            loop: this.loop,
        };
    }

    _advance(dt) {
        this.time += dt;
        if (this.time < this.duration) return;
        if (this.loop) {
            this.time %= this.duration;
        } else {
            this.time = this.duration;
            this.playing = false;     // the state emitted next carries playing:false — that IS the end-of-scene signal
        }
    }
}
