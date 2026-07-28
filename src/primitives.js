// Parametric primitives — simple shapes COMPUTED from a spec (root Rule #19:
// no stored model files for anything a formula can build). Each builder takes
// a plain-JSON spec and returns a THREE.Group ready for the scene.

import * as THREE from 'three';
import { makeLabelSprite } from './labels.js';

const AXIS_DIRECTIONS = {
    '+x': [1, 0, 0], '-x': [-1, 0, 0],
    '+y': [0, 1, 0], '-y': [0, -1, 0],
    '+z': [0, 0, 1], '-z': [0, 0, -1],
};

// Default specs double as the parameter reference — every field here is
// overridable through the spec object (root Rule #4).
export const AXES_DEFAULTS = {
    armLength: 1,
    armRadius: 0.03,
    arms: [
        { axis: '+x', color: '#EF4444', label: 'X+' },
        { axis: '-x', color: '#F97316', label: 'X−' },
        { axis: '+y', color: '#22C55E', label: 'Y+' },
        { axis: '-y', color: '#EAB308', label: 'Y−' },
        { axis: '+z', color: '#3B82F6', label: 'Z+' },
        { axis: '-z', color: '#A855F7', label: 'Z−' },
    ],
};

export const CUBE_DEFAULTS = {
    size: 1,
    color: '#818CF8',
    colors: null,   // optional per-face array [+x, -x, +y, -y, +z, -z]
    edges: true,
};

const BUILDERS = {
    axes: buildAxes,
    cube: buildCube,
};

export function buildPrimitive(spec) {
    const build = BUILDERS[spec.type];
    if (!build) {
        throw new Error(`Unknown primitive type '${spec.type}' — available: ${Object.keys(BUILDERS).join(', ')}`);
    }
    return build(spec);
}

function standardMaterial(color) {
    return new THREE.MeshStandardMaterial({ color, roughness: 0.35, metalness: 0.15 });
}

// Axes gizmo: up to 6 arms from the origin, each its own color and label.
// One arm = cylinder shaft (80% of length) + cone tip (20%), oriented by the
// quaternion that maps +Y (cylinder's native axis) onto the arm direction.
function buildAxes(spec) {
    const { armLength, armRadius, arms } = { ...AXES_DEFAULTS, ...spec };
    const group = new THREE.Group();
    const shaftLength = armLength * 0.8;
    const tipLength = armLength * 0.2;
    const up = new THREE.Vector3(0, 1, 0);

    const joint = new THREE.Mesh(
        new THREE.SphereGeometry(armRadius * 2, 24, 16),
        new THREE.MeshStandardMaterial({ color: '#B3B3B3', roughness: 0.4, metalness: 0.3 }),
    );
    group.add(joint);

    for (const arm of arms) {
        const axis = AXIS_DIRECTIONS[arm.axis];
        if (!axis) {
            throw new Error(`Unknown arm axis '${arm.axis}' — expected one of: ${Object.keys(AXIS_DIRECTIONS).join(', ')}`);
        }
        const direction = new THREE.Vector3(...axis);
        const orient = new THREE.Quaternion().setFromUnitVectors(up, direction);
        const material = standardMaterial(arm.color);

        const shaft = new THREE.Mesh(
            new THREE.CylinderGeometry(armRadius, armRadius, shaftLength, 20),
            material,
        );
        shaft.quaternion.copy(orient);
        shaft.position.copy(direction).multiplyScalar(shaftLength / 2);
        group.add(shaft);

        const tip = new THREE.Mesh(
            new THREE.ConeGeometry(armRadius * 2.4, tipLength, 24),
            material,
        );
        tip.quaternion.copy(orient);
        tip.position.copy(direction).multiplyScalar(shaftLength + tipLength / 2);
        group.add(tip);

        if (arm.label) {
            const sprite = makeLabelSprite(arm.label, {
                color: arm.color,
                worldHeight: armLength * 0.16,
            });
            sprite.position.copy(direction).multiplyScalar(armLength * 1.16);
            group.add(sprite);
        }
    }
    return group;
}

// Cube: single color, or six per-face colors in BoxGeometry group order
// [+x, -x, +y, -y, +z, -z]; optional soft edge lines.
function buildCube(spec) {
    const { size, color, colors, edges } = { ...CUBE_DEFAULTS, ...spec };
    const group = new THREE.Group();
    const geometry = new THREE.BoxGeometry(size, size, size);
    const material = colors
        ? colors.map(standardMaterial)
        : standardMaterial(color);
    group.add(new THREE.Mesh(geometry, material));

    if (edges) {
        group.add(new THREE.LineSegments(
            new THREE.EdgesGeometry(geometry),
            new THREE.LineBasicMaterial({ color: '#F5F5F5', transparent: true, opacity: 0.35 }),
        ));
    }
    return group;
}
