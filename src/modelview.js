// The model layer's viewer-side operations.
//
// Split out of viewer.js for the reason parts.js was: showing a MODEL is its
// own responsibility (validate it, turn it into content, dress it per view, set
// the Switcher, turn it to an orientation), and the Viewer's job is to be a
// container. Everything here takes what it needs and RETURNS what it decided;
// none of it reaches into a viewer, so it is testable and mirrors the Python
// side (preview3d/light/model_view.py) function for function.

import * as THREE from 'three';
import { buildPrimitive } from './primitives.js';
import { validate } from './model.js';
import { buildSpec, findView, viewOpacities } from './modelscene.js';
import { orientationAxes } from './orientations.js';

// A validated model as ready-to-mount content. Validation happens HERE rather
// than at the call site so both renderers reject the same models: a model is
// generated data, and a field that is quietly wrong would surface as a missing
// label three screens later (Rule 1).
export function buildModelContent(model) {
    const checked = validate(model);
    return { model: checked, content: buildPrimitive(buildSpec(checked)) };
}

// What a view asks for: the per-part opacities, and where the camera stands.
// A view is nothing more than that, which is what lets a scene TWEEN from one
// owner model into another instead of cutting between two built scenes.
export function viewSettings(model, name) {
    return { opacity: viewOpacities(model, name), camera: findView(model, name).camera ?? null };
}

export function modelViewList(model) {
    return model.views.map((view) => ({ name: view.name, label: view.label ?? view.name }));
}

// The rotation for one of the cube's 24 orientations, or null for upright.
export function orientationQuaternion(identifier) {
    if (!identifier) return null;
    const [right, up, forward] = orientationAxes(identifier);
    return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(
        new THREE.Vector3(...right), new THREE.Vector3(...up), new THREE.Vector3(...forward),
    ));
}

// A model may carry fewer registers than the component offers, and asking one of
// its seats for a vocabulary it does not have would fail deep inside a switch
// group. Refuse where the register was chosen instead.
export function checkRegister(model, register) {
    if (model && !model.registers.includes(register)) {
        throw new Error(
            `Model '${model.name}' has no register '${register}' — it carries: `
            + model.registers.join(', '),
        );
    }
}

export function requireModel(model, what) {
    if (!model) {
        throw new Error(`${what}() needs a model — call showModel() first (content first, view second)`);
    }
}
