"""Arithmetic defined to match JavaScript's.

Two implementations of one formula must produce the same number, not nearly the
same number. Python's built-in `round` breaks ties to EVEN while JavaScript's
`Math.round` breaks them UP, so any formula that rounds — a frame index, a
colour channel — would put the two renderers one unit apart on an exact tie and
nowhere else, which is the hardest kind of drift to notice.

Small on purpose: this is the one place that difference is spelled out, so no
module has to remember it (root Rule 5).
"""

import math


def round_half_up(value: float) -> int:
    """JavaScript's `Math.round`."""
    return math.floor(value + 0.5)
