// Axis directions — one grammar for every direction a cube has.
//
// An arm used to be one of six hardcoded entries, which made the cube's SIX
// edge axes and FOUR vertex diagonals literally inexpressible. They are now the
// same thing as the face axes, written in one grammar (root Rule 19: define how
// the pieces move, never enumerate the games):
//
//     a TOKEN is one or more distinct signed cube letters — '+x', '-z',
//     '+x+y', '+x-z', '+x+y+z', '-x+y-z' — and its direction is the
//     NORMALISED sum of those letters.
//
// So '+x' is (1,0,0), '+x+y' is (1,1,0)/sqrt(2) — the true midpoint of the
// cube's +x/+y edge — and '+x+y+z' is (1,1,1)/sqrt(3), the true body diagonal.
// The six legacy tokens keep working because they are the one-letter case of
// the same rule, not a special case beside it. A raw unit vector is accepted
// anywhere a token is.
//
// Mirror of preview3d/directions.py; both read `axisLetters` / `axisTiers` from
// shared/spec.json, so the grammar cannot drift between them.

import SHARED from '../shared/spec.json';

export const LETTERS = SHARED.axisLetters;
export const LETTER_ORDER = Object.keys(LETTERS);
export const AXIS_TIERS = Object.fromEntries(
    Object.entries(SHARED.axisTiers).filter(([name]) => !name.startsWith('_')),
);
export const TIER_ORDER = SHARED.tierOrder;

// Cube directions are separated by tens of degrees, so this is orders of
// magnitude away from ever confusing two of them.
const SAME_DIRECTION = 1e-9;

const TIER_BY_LETTERS = Object.fromEntries(
    Object.entries(AXIS_TIERS)
        .filter(([name]) => name !== 'sacred')
        .map(([name, tier]) => [tier.letters, name]),
);

// Split a token into [letter, sign] pairs, in the order written. Anything that
// is not a run of distinct signed cube letters fails, naming what was wrong — a
// typo in a direction must never resolve to some other direction.
export function tokenLetters(token) {
    if (typeof token !== 'string' || !token.length || token.length % 2 !== 0) {
        throw new Error(
            `Unknown direction token '${token}' — expected signed letters from `
            + `${LETTER_ORDER.join(', ')}, e.g. '+x' or '+x-y+z'`,
        );
    }
    const parsed = [];
    const seen = new Set();
    for (let i = 0; i < token.length; i += 2) {
        const sign = token[i];
        const letter = token[i + 1];
        if ((sign !== '+' && sign !== '-') || !LETTERS[letter]) {
            throw new Error(
                `Unknown direction token '${token}' — '${token.slice(i, i + 2)}' is not a `
                + `signed letter from ${LETTER_ORDER.join(', ')}`,
            );
        }
        if (seen.has(letter)) throw new Error(`Direction token '${token}' repeats the letter '${letter}'`);
        seen.add(letter);
        parsed.push([letter, sign === '+' ? 1 : -1]);
    }
    return parsed;
}

export function tokenVector(token) {
    const sum = [0, 0, 0];
    for (const [letter, sign] of tokenLetters(token)) {
        const vector = LETTERS[letter];
        for (let i = 0; i < 3; i++) sum[i] += vector[i] * sign;
    }
    return sum;
}

function unit(vector) {
    const length = Math.hypot(vector[0], vector[1], vector[2]);
    if (!length) throw new Error('A direction cannot be the zero vector');
    return [vector[0] / length, vector[1] / length, vector[2] / length];
}

// A token or a 3-vector to a UNIT direction. Anything else fails loudly.
export function parseDirection(value) {
    if (typeof value === 'string') return unit(tokenVector(value));
    if (Array.isArray(value) && value.length === 3) return unit(value.map(Number));
    throw new Error(
        `Unusable direction ${JSON.stringify(value)} — expected a token like '+x' or `
        + "'+x-y+z', or a 3-element vector",
    );
}

// The same direction with its letters in the cube's own order: '+y+x' and
// '+x+y' are one direction and must therefore be one NAME, or the same arm
// would be addressable by two paths.
export function canonicalToken(token) {
    const signs = Object.fromEntries(tokenLetters(token));
    return LETTER_ORDER
        .filter((letter) => letter in signs)
        .map((letter) => (signs[letter] > 0 ? '+' : '-') + letter)
        .join('');
}

export function oppositeToken(token) {
    return tokenLetters(token).map(([letter, sign]) => (sign > 0 ? '-' : '+') + letter).join('');
}

// True for the end an axis is NAMED after: first letter written positive.
export function isPositiveEnd(token) {
    return tokenLetters(token)[0][1] > 0;
}

// primary / secondary / tertiary, from how many letters the token carries.
// `sacred` is never returned: it is not a geometry but a model's choice of one
// vertex diagonal, and only the model can make it.
export function tierOf(token) {
    const count = tokenLetters(token).length;
    const tier = TIER_BY_LETTERS[count];
    if (!tier) {
        throw new Error(
            `Direction token '${token}' carries ${count} letters; the tiers cover `
            + Object.keys(TIER_BY_LETTERS).join(', '),
        );
    }
    return tier;
}

// Every canonical-order token with exactly `letters` letters: 6 for one (the
// face normals), 12 for two (the edge midpoints), 8 for three (the vertex
// diagonals) — computed from the grammar, never listed.
export function cubeTokens(letters) {
    const tokens = [];
    for (let mask = 1; mask < (1 << LETTER_ORDER.length); mask++) {
        const chosen = LETTER_ORDER.filter((_, i) => mask & (1 << i));
        if (chosen.length !== letters) continue;
        for (let combination = 0; combination < (1 << letters); combination++) {
            tokens.push(chosen
                .map((letter, i) => ((combination & (1 << i)) === 0 ? '+' : '-') + letter)
                .join(''));
        }
    }
    return tokens;
}

// Every axis of that tier as [positive end, negative end]: each line listed
// once, named after the end whose first letter is written positive.
export function cubeAxes(letters) {
    return cubeTokens(letters).filter(isPositiveEnd).map((token) => [token, oppositeToken(token)]);
}

// The three vertices an edge away from `vertex` — flip exactly one of its own
// letters' signs, keep the other two. Computed from the vertex's own letters
// (root Rule 19), never listed: this is what makes a cube's silhouette hexagon
// (seen down the OPPOSITE diagonal) split into two triangles — one per pole's
// own three neighbours — which is the geometry the Hexagram X-ray draws.
export function vertexNeighbors(vertex) {
    const signed = tokenLetters(vertex);
    if (signed.length !== 3) throw new Error(`vertexNeighbors needs a vertex token (3 letters), got '${vertex}'`);
    const neighbors = [];
    for (let index = 0; index < 3; index++) {
        const flipped = signed.map((pair) => [...pair]);
        flipped[index][1] = -flipped[index][1];
        neighbors.push(canonicalToken(
            flipped.map(([letter, sign]) => (sign > 0 ? '+' : '-') + letter).join(''),
        ));
    }
    return neighbors;
}

// The seven cells hidden behind `vertex`'s own view: the ANTIPODE vertex, its
// three adjacent edges and its three adjacent faces — every cell sharing the
// antipode's sign combination (the Blindness law: 26 - 7 = 19 visible).
// Computed from the antipode's own letters (root Rule 19), never enumerated.
export function hiddenFrom(vertex) {
    const antipode = tokenLetters(oppositeToken(vertex));
    if (antipode.length !== 3) throw new Error(`hiddenFrom needs a vertex token (3 letters), got '${vertex}'`);
    const hidden = [];
    for (const count of [1, 2, 3]) {
        for (const combo of combinationsOf(antipode, count)) {
            hidden.push(canonicalToken(combo.map(([letter, sign]) => (sign > 0 ? '+' : '-') + letter).join('')));
        }
    }
    return hidden;
}

function combinationsOf(items, count) {
    if (count === 0) return [[]];
    if (items.length < count) return [];
    const [first, ...rest] = items;
    const withFirst = combinationsOf(rest, count - 1).map((combo) => [first, ...combo]);
    const withoutFirst = combinationsOf(rest, count);
    return [...withFirst, ...withoutFirst];
}

// The token for a direction that IS one of the cube's 26, or a failure.
export function tokenOf(vector) {
    const target = parseDirection(vector);
    for (const letters of [1, 2, 3]) {
        for (const token of cubeTokens(letters)) {
            const candidate = parseDirection(token);
            const gap = candidate.reduce((sum, c, i) => sum + (c - target[i]) ** 2, 0);
            if (gap < SAME_DIRECTION) return token;
        }
    }
    throw new Error(`Direction ${JSON.stringify(vector)} is not one of the cube's 26 directions`);
}
