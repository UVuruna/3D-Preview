"""Axis directions — one grammar for every direction a cube has.

An arm used to be one of six hardcoded entries, which made the cube's SIX edge
axes and FOUR vertex diagonals literally inexpressible. They are now the same
thing as the face axes, written in one grammar (root Rule 19: define how the
pieces move, never enumerate the games):

    a TOKEN is one or more distinct signed cube letters — "+x", "-z",
    "+x+y", "+x-z", "+x+y+z", "-x+y-z" — and its direction is the
    NORMALISED sum of those letters.

So "+x" is (1, 0, 0), "+x+y" is (1, 1, 0)/sqrt(2) — the true midpoint of the
cube's +x/+y edge — and "+x+y+z" is (1, 1, 1)/sqrt(3), the true body diagonal.
The six legacy tokens keep working because they are the one-letter case of the
same rule, not a special case beside it.

A raw unit vector is accepted anywhere a token is, so a host is never forced
into the cube's vocabulary.

Pure Python — no Qt, no renderer. The JS mirror is src/directions.js and both
read `axisLetters` / `axisTiers` from shared/spec.json, so the grammar cannot
drift between them.
"""

import math
from itertools import combinations

from .resources import load_shared_spec
from .vectors import Vec3, normalize

_SPEC = load_shared_spec()
LETTERS: dict[str, Vec3] = {
    letter: tuple(float(v) for v in vector)
    for letter, vector in _SPEC["axisLetters"].items()
}
LETTER_ORDER: list[str] = list(LETTERS)
AXIS_TIERS: dict[str, dict] = {
    name: tier for name, tier in _SPEC["axisTiers"].items() if not name.startswith("_")
}
TIER_ORDER: list[str] = list(_SPEC["tierOrder"])

# How close two directions must be to count as the same one when a vector is
# named back into a token. Cube directions are separated by tens of degrees, so
# this is orders of magnitude away from ever confusing two of them.
_SAME_DIRECTION = 1e-9

# The tier a direction belongs to, keyed by how many letters it carries. `sacred`
# shares the vertex geometry with `tertiary`, so it is never derived — a model
# singles it out by name.
_TIER_BY_LETTERS: dict[int, str] = {
    int(tier["letters"]): name
    for name, tier in AXIS_TIERS.items()
    if name != "sacred"
}


def parse_direction(value) -> Vec3:
    """A token or a 3-vector to a UNIT direction. Anything else fails loudly."""
    if isinstance(value, str):
        return normalize(token_vector(value))
    if isinstance(value, (list, tuple)) and len(value) == 3:
        vector = tuple(float(component) for component in value)
        if math.isclose(vector[0], 0.0) and math.isclose(vector[1], 0.0) and math.isclose(vector[2], 0.0):
            raise ValueError("A direction cannot be the zero vector")
        return normalize(vector)
    raise ValueError(
        f"Unusable direction {value!r} — expected a token like '+x' or '+x-y+z', "
        "or a 3-element vector"
    )


def token_letters(token: str) -> list[tuple[str, float]]:
    """Split a token into (letter, sign) pairs, in the order written.

    Raises on anything that is not a run of distinct signed cube letters, naming
    what was wrong — a typo in a direction must not resolve to something else.
    """
    if not token or len(token) % 2 != 0:
        raise ValueError(
            f"Unknown direction token {token!r} — expected signed letters from "
            f"{', '.join(LETTER_ORDER)}, e.g. '+x' or '+x-y+z'"
        )
    parsed: list[tuple[str, float]] = []
    seen: set[str] = set()
    for index in range(0, len(token), 2):
        sign, letter = token[index], token[index + 1]
        if sign not in "+-" or letter not in LETTERS:
            raise ValueError(
                f"Unknown direction token {token!r} — {token[index:index + 2]!r} is not a "
                f"signed letter from {', '.join(LETTER_ORDER)}"
            )
        if letter in seen:
            raise ValueError(f"Direction token {token!r} repeats the letter {letter!r}")
        seen.add(letter)
        parsed.append((letter, 1.0 if sign == "+" else -1.0))
    return parsed


def token_vector(token: str) -> Vec3:
    """The (un-normalised) sum of a token's letters."""
    x = y = z = 0.0
    for letter, sign in token_letters(token):
        vector = LETTERS[letter]
        x += vector[0] * sign
        y += vector[1] * sign
        z += vector[2] * sign
    return (x, y, z)


def canonical_token(token: str) -> str:
    """The same direction with its letters in the cube's own x, y, z order.

    '+y+x' and '+x+y' are one direction and must therefore be one NAME, or the
    same arm would be addressable by two paths.
    """
    signs = dict(token_letters(token))
    return "".join(
        ("+" if signs[letter] > 0 else "-") + letter
        for letter in LETTER_ORDER
        if letter in signs
    )


def opposite_token(token: str) -> str:
    """The other end of the same axis."""
    return "".join(
        ("-" if sign > 0 else "+") + letter for letter, sign in token_letters(token)
    )


def is_positive_end(token: str) -> bool:
    """True for the end an axis is NAMED after: first letter written positive."""
    return token_letters(token)[0][1] > 0


def tier_of(token: str) -> str:
    """primary / secondary / tertiary, from how many letters the token carries.

    `sacred` is never returned: it is not a geometry but a model's choice of one
    vertex diagonal, and only the model can make it.
    """
    count = len(token_letters(token))
    tier = _TIER_BY_LETTERS.get(count)
    if tier is None:
        raise ValueError(
            f"Direction token {token!r} carries {count} letters; the tiers cover "
            f"{sorted(_TIER_BY_LETTERS)}"
        )
    return tier


def cube_tokens(letters: int) -> list[str]:
    """Every canonical-order token with exactly `letters` letters.

    6 for one letter (the face normals), 12 for two (the edge midpoints), 8 for
    three (the vertex diagonals) — computed from the grammar, never listed.
    """
    tokens: list[str] = []
    for mask in range(1, 1 << len(LETTER_ORDER)):
        chosen = [LETTER_ORDER[i] for i in range(len(LETTER_ORDER)) if mask & (1 << i)]
        if len(chosen) != letters:
            continue
        for combination in range(1 << letters):
            tokens.append("".join(
                ("+" if combination & (1 << i) == 0 else "-") + letter
                for i, letter in enumerate(chosen)
            ))
    return tokens


def cube_axes(letters: int) -> list[tuple[str, str]]:
    """Every axis of that tier as (positive end, negative end).

    Each line is listed once, named after the end whose first letter is written
    positive: 3 face axes, 6 edge axes, 4 vertex axes.
    """
    return [
        (token, opposite_token(token))
        for token in cube_tokens(letters)
        if is_positive_end(token)
    ]


def vertex_neighbors(vertex: str) -> list[str]:
    """The three vertices an edge away from `vertex` — flip exactly one of its
    own letters' signs, keep the other two.

    Computed from the vertex's own letters (root Rule 19), never listed: this is
    what makes a cube's silhouette hexagon (seen down the OPPOSITE diagonal)
    split into two triangles — one per pole's own three neighbours — which is
    the geometry the Hexagram X-ray draws.
    """
    signed = token_letters(vertex)
    if len(signed) != 3:
        raise ValueError(f"vertex_neighbors needs a vertex token (3 letters), got {vertex!r}")
    neighbors = []
    for index in range(3):
        flipped = list(signed)
        letter, sign = flipped[index]
        flipped[index] = (letter, -sign)
        neighbors.append(canonical_token(
            "".join(("+" if s > 0 else "-") + letter for letter, s in flipped)
        ))
    return neighbors


def hidden_from(vertex: str) -> list[str]:
    """The seven cells hidden behind `vertex`'s own view: the ANTIPODE vertex,
    its three adjacent edges and its three adjacent faces.

    Standing at one vertex of the cube, the antipode's own "court" — every cell
    that shares the antipode's sign combination — sits directly behind it and
    out of sight (the Blindness law: 26 - 7 = 19 visible). Computed from the
    antipode's own letters (root Rule 19), never enumerated per vertex.
    """
    antipode = token_letters(opposite_token(vertex))
    if len(antipode) != 3:
        raise ValueError(f"hidden_from needs a vertex token (3 letters), got {vertex!r}")
    hidden = []
    for count in (1, 2, 3):
        for combo in combinations(antipode, count):
            hidden.append(canonical_token(
                "".join(("+" if sign > 0 else "-") + letter for letter, sign in combo)
            ))
    return hidden


def token_of(vector: Vec3) -> str:
    """The token for a direction that IS one of the cube's 26, or a failure.

    Used to name a seat from its position; a host passing some other direction
    supplies its own name instead.
    """
    unit = parse_direction(vector)
    for letters in sorted(_TIER_BY_LETTERS):
        for token in cube_tokens(letters):
            candidate = parse_direction(token)
            if sum((candidate[i] - unit[i]) ** 2 for i in range(3)) < _SAME_DIRECTION:
                return token
    raise ValueError(f"Direction {vector!r} is not one of the cube's 26 directions")
