// The thirteen-axis cube model, COMPUTED.
//
// The four owner models — primary axes, secondary axes, tertiary axes, the
// glass cube — are four VIEWS over ONE model, never four hand-built scenes.
// This module builds that model: 13 axes (3 face + 6 edge + 4 vertex), 27 seats
// (6 + 12 + 8 + the centre), every colour derived, every position derived, and
// the four views.
//
// Nothing here is a stored file (root Rule 19). The geometry follows from the
// cube, the colours follow from the poles, and the words follow from a small
// seed vocabulary of the SIX poles: a two-letter seat says what its two poles
// say, a three-letter seat what its three say. Twelve words per register become
// fifty-four seats.
//
// A consumer supplies the WORDS, never the geometry — Watch Academy's exporter
// calls this with its own canon, so its terms stay in DOMY and this gadget
// stays content-agnostic. What ships here is a neutral demo vocabulary that
// shows the structure and claims nothing.
//
// Mirror of preview3d/cube_model.py.

import SHARED from '../shared/spec.json';
import { SACRED, deriveAll } from './axiscolors.js';
import { canonicalToken, cubeAxes, cubeTokens, oppositeToken, tierOf, tokenLetters, tokenVector } from './directions.js';
import { validate } from './model.js';
import { GROUP_PATHS } from './modelscene.js';

export const REGISTERS = SHARED.switcher.registers;

// How a derived seat says what its poles say. One separator, so a reader can
// always see that a compound term IS its parents.
export const JOIN = ' · ';
export const CENTRE = 'centre';
export const ROOT_NAME = 'model';
export const GLASS_OPACITY = 0.12;

// The seed vocabulary: six poles plus the centre, per register, each as
// [luminous, fallen]. Deliberately generic English — this is a DEMO of the
// structure, not anybody's canon.
export const DEMO_VOCABULARY = {
    canon: {
        '+x': ['Warmth', 'Scorching'], '-x': ['Calm', 'Coldness'],
        '+y': ['Clarity', 'Glare'], '-y': ['Depth', 'Murk'],
        '+z': ['Growth', 'Rankness'], '-z': ['Force', 'Violence'],
        [CENTRE]: ['Centre', 'Dispersion'],
    },
    myth: {
        '+x': ['Hearth', 'Wildfire'], '-x': ['Ocean', 'Abyss'],
        '+y': ['Sun', 'Drought'], '-y': ['Night', 'Delirium'],
        '+z': ['Forest', 'Thicket'], '-z': ['Forge', 'Ruin'],
        [CENTRE]: ['The Axis', 'The Void'],
    },
    historical: {
        '+x': ['Trade', 'Plunder'], '-x': ['Council', 'Stagnation'],
        '+y': ['Reason', 'Dogma'], '-y': ['Mystery', 'Superstition'],
        '+z': ['Harvest', 'Excess'], '-z': ['Defence', 'Conquest'],
        [CENTRE]: ['The Capital', 'The Interregnum'],
    },
    movie: {
        '+x': ['Hero', 'Zealot'], '-x': ['Mentor', 'Recluse'],
        '+y': ['Sage', 'Pedant'], '-y': ['Seer', 'Charlatan'],
        '+z': ['Guardian', 'Hoarder'], '-z': ['Champion', 'Tyrant'],
        [CENTRE]: ['The Protagonist', 'The Extra'],
    },
};

// The four owner models. Each is a view: which groups speak, how loudly, and
// where the camera stands. Values are plain opacities, so a scene can TWEEN
// from one owner model into another without an engine change.
export const DEFAULT_VIEWS = [
    { name: 'primary', label: 'Primary Axes', camera: '+x+y+z', opacity: { primary: 1 } },
    {
        // The whole point of a 3D previewer: a flat wheel cannot show an edge
        // axis at its true angle. The face axes stay faintly lit as the frame
        // the edge axes are measured against.
        name: 'secondary', label: 'Secondary Axes', camera: '+x+y+z',
        opacity: { primary: 0.18, secondary: 1 },
    },
    {
        // Seen from a direction PERPENDICULAR to the sacred diagonal, so the one
        // axis that matters most shows its true length instead of collapsing to
        // a point (which is exactly what the iso view does to it).
        name: 'tertiary', label: 'Tertiary Axes', camera: '-x+y',
        opacity: { primary: 0.15, tertiary: 1, sacred: 1, vertex: 0.85, [CENTRE]: 1 },
    },
    {
        name: 'cube', label: 'The Cube', camera: '+x+y+z',
        opacity: {
            primary: 0.55, secondary: 0.5, tertiary: 0.5, sacred: 0.85,
            face: 1, edge: 1, vertex: 1, [CENTRE]: 1, glass: GLASS_OPACITY,
        },
    },
];

const KINDS = { 1: 'face', 2: 'edge', 3: 'vertex' };

export function buildCubeModel(options = {}) {
    const {
        name = 'cube13',
        label = 'The Thirteen Axes',
        size = 1,
        sacred = '+x+y+z',
        registers = REGISTERS,
        vocabulary = DEMO_VOCABULARY,
        views = DEFAULT_VIEWS,
    } = options;

    checkVocabulary(vocabulary, registers);
    const sacredToken = sacred ? canonicalToken(sacred) : null;
    const sacredEnds = sacredToken ? new Set([sacredToken, oppositeToken(sacredToken)]) : new Set();
    const palette = deriveAll();
    const dress = (token) => (sacredEnds.has(token) ? SACRED : palette[token]);

    return validate({
        name,
        label,
        root: ROOT_NAME,
        size: Number(size),
        registers: [...registers],
        axes: buildAxes(sacredToken, registers, vocabulary, dress),
        cells: buildCells(size, registers, vocabulary, dress),
        glass: { opacity: GLASS_OPACITY },
        views: views.map(expandView),
    });
}

function buildAxes(sacredToken, registers, vocabulary, dress) {
    const axes = [];
    for (const letters of [1, 2, 3]) {
        for (const [positive, negative] of cubeAxes(letters)) {
            axes.push({
                id: positive,
                tier: positive === sacredToken ? 'sacred' : tierOf(positive),
                name: `${positive} / ${negative}`,
                ends: [positive, negative].map((token) => ({
                    direction: token,
                    color: dress(token),
                    names: namesFor(token, registers, vocabulary),
                })),
            });
        }
    }
    return axes;
}

// The 26 seats plus the centre. A seat's position is its token's UN-normalised
// vector times half the cube: '+x' lands on a face centre, '+x+y' on an edge
// midpoint, '+x+y+z' on a vertex. One rule, three kinds of seat — and each seat
// is exactly where the axis end of the same name points.
function buildCells(size, registers, vocabulary, dress) {
    const half = Number(size) / 2;
    const cells = [];
    for (const letters of [1, 2, 3]) {
        for (const token of cubeTokens(letters)) {
            cells.push({
                id: token,
                kind: KINDS[letters],
                position: tokenVector(token).map((component) => component * half),
                color: dress(token),
                names: namesFor(token, registers, vocabulary),
            });
        }
    }
    cells.push({
        id: CENTRE,
        kind: CENTRE,
        position: [0, 0, 0],
        // The centre is the one seat no axis points at; it wears the sacred
        // dress whether or not a sacred axis was named, because it is where
        // every axis crosses.
        color: SACRED,
        names: namesFor(CENTRE, registers, vocabulary),
    });
    return cells;
}

function namesFor(token, registers, vocabulary) {
    return Object.fromEntries(registers.map((register) => [register, seat(token, vocabulary[register])]));
}

function seat(token, words) {
    if (token === CENTRE) return { luminous: words[CENTRE][0], fallen: words[CENTRE][1] };
    const poles = tokenLetters(token).map(([letter, sign]) => (sign > 0 ? '+' : '-') + letter);
    return {
        luminous: poles.map((pole) => words[pole][0]).join(JOIN),
        fallen: poles.map((pole) => words[pole][1]).join(JOIN),
    };
}

// A missing word must fail here, not as a blank label nobody can explain.
function checkVocabulary(vocabulary, registers) {
    const needed = [...cubeTokens(1), CENTRE];
    for (const register of registers) {
        const words = vocabulary[register];
        if (!words) {
            throw new Error(`The vocabulary has no register '${register}' — it must cover ${registers.join(', ')}`);
        }
        const missing = needed.filter((token) => !(token in words));
        if (missing.length) {
            throw new Error(
                `The '${register}' vocabulary is missing ${missing.join(', ')} — every register `
                + 'needs the six poles and the centre',
            );
        }
    }
}

// Turn a view's short group keys into the part paths the viewer addresses.
// Every group the view does not mention is set to 0 explicitly rather than left
// out, so switching between views can never leave a group lit from the one
// before it.
function expandView(view) {
    const unknown = Object.keys(view.opacity).filter((key) => !(key in GROUP_PATHS));
    if (unknown.length) {
        throw new Error(
            `View '${view.name}' sets unknown group(s) ${unknown.sort().join(', ')} — `
            + `available: ${Object.keys(GROUP_PATHS).join(', ')}`,
        );
    }
    const opacity = Object.fromEntries(Object.values(GROUP_PATHS).map((path) => [path, 0]));
    for (const [group, alpha] of Object.entries(view.opacity)) opacity[GROUP_PATHS[group]] = Number(alpha);
    const result = { name: view.name, opacity };
    if ('label' in view) result.label = view.label;
    if ('camera' in view) result.camera = view.camera;
    return result;
}
