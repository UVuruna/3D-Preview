"""The colour of an axis end, COMPUTED from the poles it lies between.

Owner decree 2026-07-28, and a direct application of root Rule 19: a colour per
axis would be twenty-six invented values to keep in sync, where four rules
cover every direction the cube has.

    primary    the sealed pole hue itself
    secondary  the blend of its two poles, THINNED BY MOONLIGHT
    tertiary   the blend of its three poles, DEEPENED toward ink
    sacred     none of the six — white-gold, the seventh dress

The moonlight thinning is not decoration. A naive two-pole blend can land on a
hue the palette already spends (the blue+yellow case the canon names), and two
seats wearing one colour is a lie about the structure. Thinning every edge
colour toward a pale moonlight moves the whole family off the saturated pole
ring, so the collision cannot happen by construction rather than by luck — and
`verify_palette` fails loudly if it ever does anyway (Rule 1).

Deepening does the same job for the vertex family in the other direction: three
poles average toward grey, so without it the four body diagonals would read as
mud between the edges. Darkened, they read as the heavier family they are.

Pure Python. The JS mirror is src/axiscolors.js; both read `poles` and
`axisColors` from shared/spec.json, so neither can restate a value.
"""

from .directions import cube_tokens, tier_of, token_letters
from .jsmath import round_half_up
from .resources import load_shared_spec

_SPEC = load_shared_spec()
POLE_COLORS: dict[str, str] = _SPEC["poles"]
_COLORS: dict = _SPEC["axisColors"]

MOONLIGHT: str = _COLORS["moonlight"]
THIN: float = float(_COLORS["thin"])
INK: str = _COLORS["ink"]
DEEPEN: float = float(_COLORS["deepen"])
SACRED: str = _COLORS["sacred"]
MIN_POLE_DISTANCE: float = float(_COLORS["minPoleDistance"])
MIN_SEAT_DISTANCE: float = float(_COLORS["minSeatDistance"])

Rgb = tuple[int, int, int]


def hex_to_rgb(color: str) -> Rgb:
    if not isinstance(color, str) or len(color) != 7 or color[0] != "#":
        raise ValueError(f"Unusable colour {color!r} — expected '#rrggbb'")
    try:
        return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    except ValueError as error:
        raise ValueError(f"Unusable colour {color!r} — expected '#rrggbb'") from error


def rgb_to_hex(rgb: Rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, int(channel))):02X}" for channel in rgb)


def mix(a: str, b: str, t: float) -> str:
    """Move `t` of the way from colour `a` to colour `b`, per channel."""
    left, right = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(tuple(
        round_half_up(left[i] + (right[i] - left[i]) * t) for i in range(3)
    ))


def blend(colors: list[str]) -> str:
    """The per-channel mean. One colour blends to itself, which is what makes
    the primary case the same rule as the others rather than an exception."""
    if not colors:
        raise ValueError("Cannot blend an empty list of colours")
    channels = [hex_to_rgb(color) for color in colors]
    return rgb_to_hex(tuple(
        round_half_up(sum(channel[i] for channel in channels) / len(channels))
        for i in range(3)
    ))


def poles_of(token: str) -> list[str]:
    """The pole hues a direction token lies between, in the token's own order."""
    return [
        POLE_COLORS[("+" if sign > 0 else "-") + letter]
        for letter, sign in token_letters(token)
    ]


def color_for(token: str, tier: str) -> str:
    """The colour of the axis end (or the cell) that `token` points at."""
    if tier == "sacred":
        return SACRED
    poles = poles_of(token)
    base = blend(poles)
    if len(poles) == 1:
        return base
    if len(poles) == 2:
        return mix(base, MOONLIGHT, THIN)
    return mix(base, INK, DEEPEN)


def derive_all() -> dict[str, str]:
    """Every one of the cube's 26 directions dressed by its GEOMETRY alone.

    The sacred dress is deliberately not applied here: which body diagonal is
    sacred is a model's statement about meaning, not something the cube knows,
    and leaving it out is what lets the collision check see the derived family
    for what it is (two seats may legitimately share white-gold; two DERIVED
    seats sharing a colour is a defect).
    """
    colors = {
        token: color_for(token, tier_of(token))
        for letters in (1, 2, 3)
        for token in cube_tokens(letters)
    }
    verify_palette(colors)
    return colors


def distance(a: str, b: str) -> float:
    """Straight-line distance in RGB — good enough to prove two colours are not
    the same colour, which is all the collision rule asks."""
    left, right = hex_to_rgb(a), hex_to_rgb(b)
    return sum((left[i] - right[i]) ** 2 for i in range(3)) ** 0.5


def verify_palette(colors: dict[str, str]) -> None:
    """The collision rule, enforced: no derived colour may sit on a pole hue,
    and no two seats may wear the same colour.

    Called by every model build, so a palette tweak that quietly makes two seats
    identical fails where it is made instead of confusing a reader later.
    """
    collisions = []
    for token, color in colors.items():
        if len(token_letters(token)) == 1:
            continue                      # a pole IS its pole hue
        for pole, pole_color in POLE_COLORS.items():
            if distance(color, pole_color) < MIN_POLE_DISTANCE:
                collisions.append(f"{token} ({color}) collides with the {pole} pole ({pole_color})")
    tokens = sorted(colors)
    for index, token in enumerate(tokens):
        for other in tokens[index + 1:]:
            apart = distance(colors[token], colors[other])
            if apart < MIN_SEAT_DISTANCE:
                collisions.append(
                    f"{token} ({colors[token]}) and {other} ({colors[other]}) "
                    f"are only {apart:.1f} apart"
                )
    if collisions:
        raise ValueError(
            "The computed axis palette collides — shared/spec.json axisColors "
            "needs adjusting: " + "; ".join(sorted(collisions))
        )
