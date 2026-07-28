// Viewer — the 3D Preview container: renderer, cameras, orbit controls,
// lighting, content lifecycle, optional grid, part control.
// Renders on demand: the GPU is idle whenever the camera is still and the
// scene unchanged.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildPrimitive } from './primitives.js';
import { buildGrid, disposeGrid } from './grid.js';
import { attachKeyboard } from './keyboard.js';
import { collectParts, removePart, setPartOpacity, setPartVisible, showOnly } from './parts.js';
import { FREE_VIEW, stepView, viewDirection } from './views.js';

const WORLD_UP = new THREE.Vector3(0, 1, 0);
const WORLD_FORWARD = new THREE.Vector3(0, 0, 1);   // basis reference for a top/bottom view
const MIN_FIT_DISTANCE = 1e-3;                      // keeps near/far valid for zero-extent content
const POLE_EPSILON = 1e-4;                          // stops the orbit flipping over the poles

// All tunables live here (root Rule #4) — every value is overridable
// per instance through the `options` constructor argument.
export const VIEWER_DEFAULTS = {
    background: '#16161F',   // DESIGN.md dark surface; 'transparent' is also valid
    fov: 45,                 // vertical field of view, degrees (perspective only)
    fitMargin: 1.1,          // breathing room around the content when framing
    dampingFactor: 0.08,     // orbit-controls inertia
    view: 'iso',             // starting view preset — see views.js
    projection: 'perspective',
    grid: false,
    keyboard: true,
    stateInterval: 80,       // ms between camera-state notifications while moving
};

export class Viewer {
    constructor(container, options = {}) {
        this.options = { ...VIEWER_DEFAULTS, ...options };
        this.container = container;

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(this.renderer.domElement);

        this.scene = new THREE.Scene();
        this._aspect = 1;
        this.projection = this.options.projection;
        this.viewName = this.options.view;
        this._direction = new THREE.Vector3(...viewDirection(this.viewName));

        this.perspectiveCamera = new THREE.PerspectiveCamera(this.options.fov, 1, 0.01, 1000);
        this.orthographicCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 1000);
        this.camera = this._cameraFor(this.projection);
        this.camera.position.set(2, 1.5, 3);

        // Neutral studio lighting computed at runtime (no HDR asset — Rule #19):
        // an environment map for PBR materials plus one directional for definition.
        const pmrem = new THREE.PMREMGenerator(this.renderer);
        this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
        pmrem.dispose();
        const key = new THREE.DirectionalLight(0xffffff, 1.0);
        key.position.set(5, 8, 6);
        this.scene.add(key);

        this._content = new THREE.Group();
        this._content.name = 'content';
        this.scene.add(this._content);
        // Bumped on every content swap. A host watches it to know when to
        // re-read the part list — model loading is async, so "right after
        // calling show()" is not a reliable moment to ask.
        this._contentVersion = 0;

        this.gridEnabled = this.options.grid;
        this._grid = null;
        this.gridStep = 0;

        this._cameraListeners = new Set();
        this._statePending = false;
        this._lastStateAt = 0;
        // False while the framing is still the viewer's own, so a resize may
        // re-frame; true once the user has moved the camera themselves.
        this._userFramed = false;

        this._makeControls();
        this.setBackground(this.options.background);
        this._detachKeyboard = this.options.keyboard ? attachKeyboard(this, container) : null;

        this._observer = new ResizeObserver(() => this._resize());
        this._observer.observe(container);
        this._resize();

        this._dirty = true;
        this._tick = this._tick.bind(this);
        this._raf = requestAnimationFrame(this._tick);
    }

    // ---- Content ----------------------------------------------------------

    // spec: {type: 'axes' | 'cube', ...params} — computed geometry, see primitives.js.
    // {type: 'model', url} delegates to loadModel().
    show(spec) {
        if (spec.type === 'model') {
            if (!spec.url) throw new Error("spec type 'model' requires a url — for raw bytes use loadModelData()");
            return this.loadModel(spec.url);
        }
        this._setContent(buildPrimitive(spec));
    }

    // Load a glTF/GLB model over HTTP(S) or a relative URL.
    async loadModel(url) {
        const gltf = await new GLTFLoader().loadAsync(url);
        this._setContent(gltf.scene);
    }

    // Load a glTF/GLB model from base64-encoded bytes. This is the path the
    // PySide6 widget uses: Chromium refuses fetch() on file:// URLs, so the
    // Python side reads the file and hands the bytes over instead.
    async loadModelData(base64) {
        const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
        const gltf = await new GLTFLoader().parseAsync(bytes.buffer, '');
        this._setContent(gltf.scene);
    }

    // Export the current content as a binary glTF Blob — the "make a simple
    // 3D file" path (Rule #19: shapes are computed; a file exists only when
    // one is actually needed). Label sprites are viewer-side and not exported.
    async exportGLB() {
        const buffer = await new GLTFExporter().parseAsync(this._content, { binary: true });
        return new Blob([buffer], { type: 'model/gltf-binary' });
    }

    _setContent(object) {
        this._clear();
        this._content.add(object);
        this._contentVersion += 1;
        this._rebuildGrid();
        this.fitView();
    }

    _clear() {
        this._content.traverse((obj) => {
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) {
                for (const m of Array.isArray(obj.material) ? obj.material : [obj.material]) {
                    if (m.map) m.map.dispose();
                    m.dispose();
                }
            }
        });
        this._content.clear();
    }

    // ---- Parts ------------------------------------------------------------
    // Thin delegations to parts.js so a host drives everything through the
    // Viewer; paths are documented in MODELS.md.

    listParts() {
        return collectParts(this._content);
    }

    setPartVisible(path, visible) {
        setPartVisible(this._content, path, visible);
        this.requestRender();
    }

    setPartOpacity(path, alpha) {
        setPartOpacity(this._content, path, alpha);
        this.requestRender();
    }

    // Show one child of a switch group and hide its siblings.
    showOnly(groupPath, childName) {
        showOnly(this._content, groupPath, childName);
        this.requestRender();
    }

    removePart(path) {
        removePart(this._content, path);
        this._rebuildGrid();
        this.requestRender();
    }

    // ---- Camera: presets, projection, movement ----------------------------

    setView(name) {
        this._direction.set(...viewDirection(name));
        this.viewName = name;
        this.fitView();
    }

    // Cycle the preset list; step +1 forward, -1 back.
    stepView(step) {
        this.setView(stepView(this.viewName, step));
    }

    setProjection(kind) {
        if (kind !== 'perspective' && kind !== 'orthographic') {
            throw new Error(`Unknown projection '${kind}' — expected 'perspective' or 'orthographic'`);
        }
        if (kind === this.projection) return;

        const target = this.controls.target.clone();
        const height = this._visibleHeight();     // keep the content the same size on screen
        const previous = this.camera;

        this.projection = kind;
        this.camera = this._cameraFor(kind);
        this.camera.position.copy(previous.position);
        this.camera.up.copy(previous.up);

        if (this.camera.isOrthographicCamera) {
            this._setOrthoHeight(height);
        } else {
            // Perspective has no zoom-out knob: apparent size is distance.
            const distance = height / (2 * Math.tan(THREE.MathUtils.degToRad(this.options.fov / 2)));
            const direction = this.camera.position.clone().sub(target).normalize();
            this.camera.position.copy(target).addScaledVector(direction, distance);
            this.camera.zoom = 1;
        }
        this._updateCameraAspect();
        this._makeControls(target);
        this._notifyCamera(true);
        this.requestRender();
    }

    // Move around the content: the point you look FROM changes, the point you
    // look AT stays put. Degrees.
    orbitBy(deltaAzimuth, deltaElevation) {
        const offset = this.camera.position.clone().sub(this.controls.target);
        const spherical = new THREE.Spherical().setFromVector3(offset);
        spherical.theta += THREE.MathUtils.degToRad(deltaAzimuth);
        spherical.phi = THREE.MathUtils.clamp(
            spherical.phi - THREE.MathUtils.degToRad(deltaElevation),
            POLE_EPSILON,
            Math.PI - POLE_EPSILON,
        );
        this.camera.position.copy(this.controls.target).add(offset.setFromSpherical(spherical));
        this._markUserFramed();
        this._afterCameraMove();
    }

    // Slide the view sideways/up: the point you look AT moves with the camera.
    // Steps are fractions of the visible height, so they feel the same at any zoom.
    panBy(deltaX, deltaY) {
        const height = this._visibleHeight();
        const right = new THREE.Vector3().setFromMatrixColumn(this.camera.matrix, 0);
        const up = new THREE.Vector3().setFromMatrixColumn(this.camera.matrix, 1);
        const move = right.multiplyScalar(deltaX * height * this._aspect)
            .addScaledVector(up, deltaY * height);
        this.camera.position.add(move);
        this.controls.target.add(move);
        this._markUserFramed();
        this._afterCameraMove();
    }

    // factor > 1 zooms in.
    zoomBy(factor) {
        if (this.camera.isOrthographicCamera) {
            this.camera.zoom *= factor;
            this.camera.updateProjectionMatrix();
        } else {
            const target = this.controls.target;
            const offset = this.camera.position.clone().sub(target).divideScalar(factor);
            this.camera.position.copy(target).add(offset);
        }
        this._userFramed = true;   // a zoom keeps the view direction, so not FREE
        this._afterCameraMove();
    }

    // Frame the content: measure its real silhouette as seen from the current
    // view direction, then pull the camera back just far enough for that
    // silhouette to fill the frustum — horizontally AND vertically, so a wide
    // container is actually used.
    //
    // Measuring the bounding BOX (or sphere) instead is far shorter but pads
    // star-shaped content badly: the axes gizmo's box corners stick out at
    // (±L, ±L, ±L) where the gizmo itself has nothing, framing it at ~55% of
    // the space it should occupy.
    fitView() {
        const measure = this._measureContent();
        if (!measure) return;
        const { forward, right, up } = this._viewBasis();
        const extent = measure;

        const target = new THREE.Vector3()
            .addScaledVector(right, extent.center.x)
            .addScaledVector(up, extent.center.y)
            .addScaledVector(forward, extent.center.z);
        const distance = Math.max(measure.distance, MIN_FIT_DISTANCE);

        this.camera.position.copy(target).addScaledVector(forward, distance);
        this.camera.up.copy(Math.abs(forward.y) > 0.999 ? WORLD_FORWARD : WORLD_UP);
        this.camera.zoom = 1;
        if (this.camera.isOrthographicCamera) {
            // Same silhouette, no perspective divide: the frustum IS the content.
            this._setOrthoHeight(2 * Math.max(extent.half.y, extent.half.x / this._aspect) * this.options.fitMargin);
        }
        this.camera.near = distance / 100;
        this.camera.far = distance * 100;
        this.camera.updateProjectionMatrix();
        this.controls.target.copy(target);
        this.controls.update();
        this._userFramed = false;
        this._notifyCamera(true);
        this.requestRender();
    }

    // The camera is now the user's, not ours: stop re-framing it on resize and
    // report the view as free rather than as whichever preset it started from.
    _markUserFramed() {
        this._userFramed = true;
        this.viewName = FREE_VIEW;
    }

    resetView() {
        this.setView(this.viewName === FREE_VIEW ? this.options.view : this.viewName);
    }

    // Azimuth/elevation in degrees, plus distance and the active modes —
    // everything a host needs for a "you are looking from…" readout.
    cameraState() {
        const offset = this.camera.position.clone().sub(this.controls.target);
        const distance = offset.length();
        return {
            azimuth: THREE.MathUtils.radToDeg(Math.atan2(offset.x, offset.z)),
            elevation: distance > 0 ? THREE.MathUtils.radToDeg(Math.asin(offset.y / distance)) : 0,
            distance,
            view: this.viewName,
            projection: this.projection,
            grid: this.gridEnabled,
            gridStep: this.gridStep,
            background: this.background,
            contentVersion: this._contentVersion,
        };
    }

    // Register a callback for camera movement; returns an unsubscribe function.
    onCameraChange(callback) {
        this._cameraListeners.add(callback);
        callback(this.cameraState());
        return () => this._cameraListeners.delete(callback);
    }

    // ---- Appearance -------------------------------------------------------

    // Sets the clear colour AND paints the container behind the canvas.
    //
    // The container matters more than it looks: resizing clears the canvas
    // backing store for at least one frame, and whatever sits behind it is
    // what the user sees in that gap. A transparent container over a white
    // host surface is a white flash on every resize — structural, not a race.
    // The reported state carries the colour so an embedding host (the Qt
    // widget) can paint its own surface to match, without restating it.
    setBackground(color) {
        this.background = color;
        if (color === 'transparent') {
            this.renderer.setClearColor(0x000000, 0);
            this.container.style.background = 'transparent';
        } else {
            this.renderer.setClearColor(new THREE.Color(color), 1);
            this.container.style.background = color;
        }
        this._notifyCamera(true);
        this.requestRender();
    }

    setGrid(enabled) {
        this.gridEnabled = enabled;
        this._rebuildGrid();
        this._notifyCamera(true);
        this.requestRender();
    }

    // ---- Render loop ------------------------------------------------------

    requestRender() {
        this._dirty = true;
    }

    _tick() {
        this._raf = requestAnimationFrame(this._tick);
        const moved = this.controls.update();   // true while orbiting / damping
        if (moved) this._statePending = true;
        if (moved || this._dirty) {
            this._dirty = false;
            this.renderer.render(this.scene, this.camera);
        }
        // Notify at a readable rate rather than every frame — a 60 Hz stream
        // over the Qt bridge buys nothing a readout can show.
        if (this._statePending) {
            const now = performance.now();
            if (!moved || now - this._lastStateAt >= this.options.stateInterval) {
                this._lastStateAt = now;
                this._statePending = moved;
                this._emitCameraState();
            }
        }
    }

    _resize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        if (!width || !height) return;
        this.renderer.setSize(width, height);
        this._aspect = width / height;
        this._updateCameraAspect();
        // Framing is aspect-dependent, so a narrower container clips content
        // that used to fit. Re-frame — but only while the framing is still
        // ours: once the user has orbited, panned or zoomed, their view is
        // theirs and a resize must not throw it away.
        if (this._userFramed) this.requestRender();
        else this.fitView();
    }

    // ---- Lifecycle --------------------------------------------------------

    dispose() {
        cancelAnimationFrame(this._raf);
        this._observer.disconnect();
        this._detachKeyboard?.();
        this._cameraListeners.clear();
        if (this._grid) disposeGrid(this._grid);
        this._clear();
        this.controls.dispose();
        this.scene.environment.dispose();
        this.renderer.dispose();
        this.renderer.domElement.remove();
    }

    // ---- Internals --------------------------------------------------------

    _cameraFor(projection) {
        return projection === 'orthographic' ? this.orthographicCamera : this.perspectiveCamera;
    }

    // OrbitControls binds to one camera at construction and reads projection
    // type for its zoom behaviour, so a projection switch gets fresh controls.
    _makeControls(target) {
        const previous = this.controls;
        if (previous) previous.dispose();
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = this.options.dampingFactor;
        if (target) this.controls.target.copy(target);
        this.controls.addEventListener('change', () => this.requestRender());
        // 'start' fires on a real interaction, unlike 'change', which damping
        // also raises for a frame or two after a programmatic camera move.
        this.controls.addEventListener('start', () => this._markUserFramed());
        this.controls.update();
    }

    _updateCameraAspect() {
        this.perspectiveCamera.aspect = this._aspect;
        this.perspectiveCamera.updateProjectionMatrix();
        const halfHeight = (this.orthographicCamera.top - this.orthographicCamera.bottom) / 2;
        this._setOrthoHeight(halfHeight * 2);
    }

    _setOrthoHeight(height) {
        const camera = this.orthographicCamera;
        camera.top = height / 2;
        camera.bottom = -height / 2;
        camera.right = (height / 2) * this._aspect;
        camera.left = -camera.right;
        camera.updateProjectionMatrix();
    }

    // World height covered by the viewport at the orbit target.
    _visibleHeight() {
        if (this.camera.isOrthographicCamera) {
            return (this.camera.top - this.camera.bottom) / this.camera.zoom;
        }
        const distance = this.camera.position.distanceTo(this.controls.target);
        return 2 * Math.tan(THREE.MathUtils.degToRad(this.options.fov / 2)) * distance;
    }

    _afterCameraMove() {
        this.camera.updateProjectionMatrix();
        this.controls.update();
        this._notifyCamera(true);
        this.requestRender();
    }

    _notifyCamera(immediate) {
        this._statePending = true;
        if (immediate) {
            this._lastStateAt = performance.now();
            this._statePending = false;
            this._emitCameraState();
        }
    }

    _emitCameraState() {
        const state = this.cameraState();
        for (const listener of this._cameraListeners) listener(state);
    }

    _rebuildGrid() {
        if (this._grid) {
            disposeGrid(this._grid);
            this._grid = null;
            this.gridStep = 0;
        }
        if (!this.gridEnabled) return;
        const built = buildGrid(this._content);
        if (!built) return;
        this._grid = built.grid;
        this.gridStep = built.step;
        this.scene.add(this._grid);   // outside _content, so it never affects framing
    }

    // Orthonormal camera basis for the current view direction. `forward`
    // points from the content toward the camera.
    _viewBasis() {
        const forward = this._direction.clone().normalize();
        const reference = Math.abs(forward.y) > 0.999 ? WORLD_FORWARD : WORLD_UP;
        const right = new THREE.Vector3().crossVectors(reference, forward).normalize();
        const up = new THREE.Vector3().crossVectors(forward, right);
        return { forward, right, up };
    }

    // Walk every point of the content in view-basis coordinates
    // (x = right, y = up, z = depth toward the camera), calling emit(x, y, z).
    // Billboards contribute their four screen-parallel corners, since they turn
    // to face the camera and their world geometry says nothing about their size.
    _walkPoints(emit) {
        const { forward, right, up } = this._viewBasis();
        const point = new THREE.Vector3();

        this._content.updateWorldMatrix(true, true);
        this._content.traverse((object) => {
            if (object.isSprite) {
                object.getWorldPosition(point);
                const x = point.dot(right), y = point.dot(up), z = point.dot(forward);
                const padX = object.scale.x / 2, padY = object.scale.y / 2;
                emit(x - padX, y - padY, z);
                emit(x + padX, y - padY, z);
                emit(x - padX, y + padY, z);
                emit(x + padX, y + padY, z);
                return;
            }
            const position = object.geometry?.getAttribute('position');
            if (!position) return;
            for (let i = 0; i < position.count; i++) {
                point.fromBufferAttribute(position, i).applyMatrix4(object.matrixWorld);
                emit(point.dot(right), point.dot(up), point.dot(forward));
            }
        });
    }

    // Content extent plus the camera distance that frames it.
    // Returns null when there is nothing to frame.
    //
    // The distance is the per-point requirement `depth + offset / tan(fov/2)`
    // maximised over the content, NOT the aggregate `halfDepth + halfHeight /
    // tan(fov/2)`. The aggregate assumes the widest point is also the nearest,
    // which for anything viewed corner-on it is not — that assumption alone
    // costs about a third of the frame.
    _measureContent() {
        const min = new THREE.Vector3(Infinity, Infinity, Infinity);
        const max = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
        this._walkPoints((x, y, z) => {
            min.set(Math.min(min.x, x), Math.min(min.y, y), Math.min(min.z, z));
            max.set(Math.max(max.x, x), Math.max(max.y, y), Math.max(max.z, z));
        });
        if (min.x > max.x) return null;

        const center = min.clone().add(max).multiplyScalar(0.5);
        const half = max.clone().sub(min).multiplyScalar(0.5);
        const tanY = Math.tan(THREE.MathUtils.degToRad(this.options.fov / 2));
        const tanX = tanY * this._aspect;
        const margin = this.options.fitMargin;

        let distance = 0;
        this._walkPoints((x, y, z) => {
            const need = (z - center.z)
                + Math.max(Math.abs(y - center.y) / tanY, Math.abs(x - center.x) / tanX) * margin;
            if (need > distance) distance = need;
        });

        return { center, half, distance };
    }
}
