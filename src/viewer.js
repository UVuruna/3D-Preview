// Viewer — the 3D Preview container: renderer, camera, orbit controls,
// lighting, content lifecycle. Renders on demand: the GPU is idle whenever
// the camera is still and the scene unchanged.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildPrimitive } from './primitives.js';

// All tunables live here (root Rule #4) — every value is overridable
// per instance through the `options` constructor argument.
export const VIEWER_DEFAULTS = {
    background: '#16161F',   // DESIGN.md dark surface; 'transparent' is also valid
    fov: 45,                 // vertical field of view, degrees
    fitMargin: 1.05,         // bounding-sphere margin when framing content
    dampingFactor: 0.08,     // orbit-controls inertia
    viewDirection: [1, 0.55, 1],  // default camera direction when framing
};

export class Viewer {
    constructor(container, options = {}) {
        this.options = { ...VIEWER_DEFAULTS, ...options };
        this.container = container;

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(this.renderer.domElement);

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(this.options.fov, 1, 0.01, 1000);
        this.camera.position.set(2, 1.5, 3);

        // Neutral studio lighting computed at runtime (no HDR asset — Rule #19):
        // an environment map for PBR materials plus one directional for definition.
        const pmrem = new THREE.PMREMGenerator(this.renderer);
        this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
        pmrem.dispose();
        const key = new THREE.DirectionalLight(0xffffff, 1.0);
        key.position.set(5, 8, 6);
        this.scene.add(key);

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = this.options.dampingFactor;
        this.controls.addEventListener('change', () => this.requestRender());

        this._content = new THREE.Group();
        this.scene.add(this._content);

        this.setBackground(this.options.background);

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

    // ---- Camera -----------------------------------------------------------

    // Frame the content: camera pulled back along viewDirection far enough
    // for the content's bounding sphere to fit the field of view.
    fitView() {
        const box = new THREE.Box3().setFromObject(this._content);
        if (box.isEmpty()) return;
        const sphere = box.getBoundingSphere(new THREE.Sphere());
        const halfFov = THREE.MathUtils.degToRad(this.camera.fov / 2);
        const distance = (sphere.radius * this.options.fitMargin) / Math.sin(halfFov);
        const direction = new THREE.Vector3(...this.options.viewDirection).normalize();

        this.camera.position.copy(sphere.center).addScaledVector(direction, distance);
        this.camera.near = distance / 100;
        this.camera.far = distance * 100;
        this.camera.updateProjectionMatrix();
        this.controls.target.copy(sphere.center);
        this.controls.update();
        this.requestRender();
    }

    resetView() {
        this.fitView();
    }

    // ---- Appearance -------------------------------------------------------

    setBackground(color) {
        if (color === 'transparent') {
            this.renderer.setClearColor(0x000000, 0);
            this.container.style.background = 'transparent';
        } else {
            this.renderer.setClearColor(new THREE.Color(color), 1);
        }
        this.requestRender();
    }

    // ---- Render loop ------------------------------------------------------

    requestRender() {
        this._dirty = true;
    }

    _tick() {
        this._raf = requestAnimationFrame(this._tick);
        const moved = this.controls.update();   // true while orbiting / damping
        if (moved || this._dirty) {
            this._dirty = false;
            this.renderer.render(this.scene, this.camera);
        }
    }

    _resize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        if (!width || !height) return;
        this.renderer.setSize(width, height);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.requestRender();
    }

    // ---- Lifecycle --------------------------------------------------------

    dispose() {
        cancelAnimationFrame(this._raf);
        this._observer.disconnect();
        this._clear();
        this.controls.dispose();
        this.scene.environment.dispose();
        this.renderer.dispose();
        this.renderer.domElement.remove();
    }
}
