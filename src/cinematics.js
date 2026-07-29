// Cinematic scene GENERATORS — a master rule for a whole family of scenes,
// never one hand-authored descriptor per case (root Rule 19).
//
// The Five Stations (PLAN.md, Extra 3D Views) "generalizes to any axis on
// demand" — the cube has 13 of them, and hand-authoring 13 near-identical JSON
// descriptors would be exactly the enumeration root Rule 19 forbids. This
// module computes the scene descriptor for ANY axis of a model instead: the
// geometry (vertex positions, the side-on camera angle, which OTHER parts to
// fade) is all derived from the model's own data, so a new axis is a function
// argument, not a new file.
//
// Mirror of preview3d/cinematics.py. Pure data — no three.js import, matching
// the rest of the model layer (directions.js, modelscene.js, switcher.js).

import SHARED from '../shared/spec.json';
import { canonicalToken, oppositeToken, parseDirection } from './directions.js';
import { GROUP_PATHS, KIND_ORDER, TIER_ORDER } from './modelscene.js';

const TIERS = SHARED.axisTiers;
const RADIAL = SHARED.switcher.radial;
export const STOPS = SHARED.switcher.stops;

const FADE_END = 0.35;     // the cube is gone by here
const SLIDE_END = 0.75;    // the beads have reached their stations by here
const EASE = 'ease-in-out';

// A gentle three-quarter opening pose — any axis starts here and eases to its
// own side-on angle, so no axis begins already looking straight down its line.
const OPENING = { azimuth: 35.0, elevation: 22.0 };

function findAxis(model, axisId) {
    const wanted = canonicalToken(axisId);
    const axis = model.axes.find((candidate) => candidate.id === wanted || oppositeToken(candidate.id) === wanted);
    if (!axis) {
        throw new Error(`Model '${model.name}' has no axis '${axisId}' — available: ${model.axes.map((a) => a.id).join(', ')}`);
    }
    return axis;
}

function cross(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function normalize(v) {
    const length = Math.hypot(...v);
    return v.map((c) => c / length);
}

function scale(v, k) {
    return v.map((c) => c * k);
}

// Azimuth/elevation of a camera looking ACROSS `direction` rather than down
// it — the tertiary view's own trick (cubemodel.js's DEFAULT_VIEWS),
// generalised to any axis instead of the one hardcoded perpendicular. A unit
// vector's asin(y) and atan2(y, hypot(x,z)) are the same angle exactly, which
// is what lets this use the shorter form while Python's Camera.look_along uses
// atan2 (it also accepts non-unit vectors) — one identity, not two formulas.
function sideOnAngles(direction) {
    const reference = Math.abs(direction[1]) > 0.999 ? [0, 0, 1] : [0, 1, 0];
    const right = normalize(cross(reference, direction));
    const [x, y, z] = right;
    const horizontal = Math.hypot(x, z);
    const azimuth = horizontal ? (Math.atan2(x, z) * 180) / Math.PI : 0;
    const elevation = horizontal ? (Math.asin(y) * 180) / Math.PI : (y > 0 ? 89.99 : -89.99);
    return [azimuth, elevation];
}

function cameraTrack(channel, start, end) {
    return { channel, keys: [{ t: 0.0, value: start, ease: EASE }, { t: FADE_END, value: end }] };
}

function opacityTrack(path, start, end) {
    return { channel: 'part.opacity', path, keys: [{ t: 0.0, value: start, ease: EASE }, { t: SLIDE_END, value: end }] };
}

// Every group that is NOT this axis or the centre, faded to nothing by
// FADE_END — "the cube fades until only the Sacred Axis line remains".
function fadeEverythingElse(model, root, tier, axisId) {
    const paths = [`${root}/${GROUP_PATHS.glass}`];
    for (const otherTier of TIER_ORDER) {
        if (otherTier !== tier) paths.push(`${root}/${GROUP_PATHS[otherTier]}`);
    }
    for (const sibling of model.axes) {
        if (sibling.tier === tier && sibling.id !== axisId) {
            paths.push(`${root}/${GROUP_PATHS[tier]}/axis:${sibling.id}`);
        }
    }
    for (const kind of KIND_ORDER) {
        if (kind !== 'centre') paths.push(`${root}/${GROUP_PATHS[kind]}`);
    }
    return paths.map((path) => opacityTrack(path, 1.0, 0.0));
}

// The Five Stations, played on ONE axis of `model`: the cube fades to a single
// line, the camera settles side-on, and the luminous/fallen beads slide from
// the geometric vertex to their radial stations (SCENES.md).
export function buildFiveStationsScene(model, axisId, duration = 8.0) {
    const axis = findAxis(model, axisId);
    const tier = axis.tier;
    const root = model.root || 'model';
    const size = Number(model.size ?? 1.0);
    const length = Number(TIERS[tier].length) * size;
    const axisPath = `${root}/${GROUP_PATHS[tier]}/axis:${axis.id}`;
    const centrePath = `${root}/${GROUP_PATHS.centre}`;

    const [positive, negative] = axis.ends;
    const [azimuth, elevation] = sideOnAngles(parseDirection(positive.direction));

    const tracks = [
        cameraTrack('camera.azimuth', OPENING.azimuth, azimuth),
        cameraTrack('camera.elevation', OPENING.elevation, elevation),
        ...fadeEverythingElse(model, root, tier, axis.id),
        // Forced to 1 regardless of the view the content happened to open on —
        // this axis's own TIER group might have started dimmed (e.g. the
        // "cube" view leaves "secondary" at 0.5), and opacity multiplies down.
        opacityTrack(`${root}/${GROUP_PATHS[tier]}`, 1.0, 1.0),
        opacityTrack(axisPath, 1.0, 1.0),
        opacityTrack(centrePath, 1.0, 1.0),
    ];
    for (const end of [positive, negative]) {
        const armPath = `${axisPath}/arm:${end.direction}`;
        const direction = parseDirection(end.direction);
        for (const stop of STOPS) {
            const stopPath = `${armPath}/${stop}`;
            const vertexPoint = scale(direction, length);
            const stationPoint = scale(direction, length * Number(RADIAL[stop]));
            tracks.push({
                channel: 'part.position', path: stopPath,
                keys: [
                    { t: 0.0, value: vertexPoint },
                    { t: FADE_END, value: vertexPoint, ease: EASE },
                    { t: SLIDE_END, value: stationPoint },
                ],
            });
            tracks.push(opacityTrack(stopPath, 0.0, 1.0));
        }
    }

    return {
        name: `five_stations:${axis.id}`,
        label: `Five Stations — ${axis.id}`,
        duration,
        loop: false,
        content: { type: 'model', view: 'cube' },
        tracks,
    };
}
