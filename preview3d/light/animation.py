"""Timeline playback for the LIGHT renderer — scenes as DATA.

Pure Python, no Qt: keyframe evaluation and the playback clock stay testable
without a GUI, and `view.py` only owns the timer that drives `tick()`.

The descriptor format, the channel table and the easing curves are the SAME
contract the web core implements in `src/animation.js` — a scene written per
SCENES.md must play identically in both. The values the two read come from
shared/spec.json, and `tests/test_animation_parity.py` pins that they agree at
t = 0, ½ and 1 of every shipped scene.
"""

import math

from ..resources import load_shared_spec

_SPEC = load_shared_spec()
ANIMATION_DEFAULTS: dict = _SPEC["animation"]
CHANNELS: dict = ANIMATION_DEFAULTS["channels"]

# Cubic curves — the standard set. `step` holds the outgoing value until the
# next key, which is also what any non-numeric value does automatically.
EASINGS = {
    "linear": lambda t: t,
    "ease-in": lambda t: t * t * t,
    "ease-out": lambda t: 1 - (1 - t) ** 3,
    "ease-in-out": lambda t: 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2,
    "step": lambda t: 0.0,
}

# The shared spec advertises the curve names to scene authors; disagreeing with
# what is actually implemented would be a silent authoring trap (Rule #1).
_UNIMPLEMENTED = [name for name in ANIMATION_DEFAULTS["easings"] if name not in EASINGS]
if _UNIMPLEMENTED:
    raise RuntimeError(
        f"shared/spec.json lists easings {_UNIMPLEMENTED}, which animation.py does not implement"
    )

# Reported when no scene is loaded, so a host's readout never special-cases None.
NO_ANIMATION = {
    "scene": None,
    "label": "",
    "playing": False,
    "time": 0.0,
    "duration": 0.0,
    "progress": 0.0,
    "speed": float(ANIMATION_DEFAULTS["defaultSpeed"]),
    "frame": 0,
    "frames": 0,
    "loop": False,
}


def ease(name: str, t: float) -> float:
    curve = EASINGS.get(name)
    if curve is None:
        raise ValueError(f"Unknown easing {name!r} — available: {', '.join(EASINGS)}")
    return curve(t)


def _is_number(value) -> bool:
    """True for a real number, deliberately NOT for a bool.

    `bool` is an `int` subclass in Python, so without this check a visibility
    flag would interpolate through 0.5 here while stepping in JavaScript — the
    two renderers would disagree on a channel neither implementation looks
    wrong in.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _round_half_up(value: float) -> int:
    """JavaScript's Math.round. Python's built-in rounds halves to even, which
    would put the two renderers one frame apart on an exact tie."""
    return math.floor(value + 0.5)


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def prepare_track(track: dict, scene: str) -> dict:
    """Validate once, at load: a typo must fail where the scene is named, not
    silently animate nothing halfway through playback."""
    channel = track.get("channel")
    spec = CHANNELS.get(channel)
    if spec is None:
        raise ValueError(
            f"Scene {scene!r}: unknown channel {channel!r} — available: {', '.join(CHANNELS)}"
        )
    if spec["path"] and not track.get("path"):
        raise ValueError(f"Scene {scene!r}: channel {channel!r} needs a 'path' to the part it drives")

    keys = sorted(track.get("keys") or [], key=lambda key: key["t"])
    if not keys:
        raise ValueError(f"Scene {scene!r}: channel {channel!r} has no keys")
    for key in keys:
        if key.get("ease") and key["ease"] not in EASINGS:
            raise ValueError(
                f"Scene {scene!r}: channel {channel!r} uses unknown easing {key['ease']!r}"
            )
    return {"channel": channel, "path": track.get("path"), "keys": keys}


def sample_track(track: dict, progress: float):
    """The track's value at `progress` (0..1 of the scene).

    A key's easing governs the segment that STARTS at it. Values that are not
    both numbers cannot be interpolated, so they step — which is exactly what a
    projection name, a visibility flag or a switch-group child needs.
    """
    keys = track["keys"]
    if progress <= keys[0]["t"]:
        return keys[0]["value"]
    if progress >= keys[-1]["t"]:
        return keys[-1]["value"]

    index = 0
    while index < len(keys) - 1 and keys[index + 1]["t"] <= progress:
        index += 1
    start, end = keys[index], keys[index + 1]
    span = end["t"] - start["t"]
    if span <= 0:
        return end["value"]
    if not (_is_number(start["value"]) and _is_number(end["value"])):
        return start["value"]

    eased = ease(start.get("ease") or ANIMATION_DEFAULTS["defaultEasing"],
                 (progress - start["t"]) / span)
    return start["value"] + (end["value"] - start["value"]) * eased


class Timeline:
    """A loaded scene plus its playback clock. Knows nothing about rendering."""

    def __init__(self, descriptor: dict):
        self.name = descriptor.get("name", "scene")
        self.label = descriptor.get("label", self.name)
        self.duration = float(descriptor.get("duration", ANIMATION_DEFAULTS["defaultDuration"]))
        if self.duration <= 0:
            raise ValueError(f"Scene {self.name!r} needs a positive duration, got {self.duration}")
        self.loop = bool(descriptor.get("loop"))
        self.fps = int(ANIMATION_DEFAULTS["fps"])
        self.frames = max(1, _round_half_up(self.duration * self.fps))
        self.tracks = [prepare_track(track, self.name) for track in descriptor.get("tracks", ())]

        self.time = 0.0
        self.speed = float(ANIMATION_DEFAULTS["defaultSpeed"])
        self.playing = False
        self._carry = 0.0     # leftover wall time not yet spent on a fixed step

    @property
    def progress(self) -> float:
        return self.time / self.duration

    @property
    def frame(self) -> int:
        return _round_half_up(self.progress * self.frames)

    def sample(self, progress: float) -> list[dict]:
        return [
            {"channel": track["channel"], "path": track["path"],
             "value": sample_track(track, progress)}
            for track in self.tracks
        ]

    def values(self) -> list[dict]:
        return self.sample(self.progress)

    # ---- Transport ---------------------------------------------------------

    def play(self) -> None:
        if not self.loop and self.time >= self.duration:
            self.time = 0.0      # replay rather than sit at the end
        self.playing = True
        self._carry = 0.0

    def pause(self) -> None:
        self.playing = False
        self._carry = 0.0

    def toggle(self) -> None:
        self.pause() if self.playing else self.play()

    def stop(self) -> None:
        """Back to the first frame, paused."""
        self.pause()
        self.time = 0.0

    def seek(self, progress: float) -> None:
        self.time = _clamp(progress, 0.0, 1.0) * self.duration
        self._carry = 0.0

    def jump_to_end(self) -> None:
        """INSTANT mode: the end state without the flight — reduced motion, and
        what a test drives to assert where a scene lands."""
        self.pause()
        self.time = self.duration

    def set_speed(self, speed: float) -> None:
        if speed <= 0:
            raise ValueError(f"Playback speed must be positive, got {speed}")
        self.speed = float(speed)

    def step_frame(self, delta: int) -> None:
        """One frame at a time; +1 forward, -1 back. Pauses playback."""
        self.pause()
        nxt = self.frame + delta
        nxt = nxt % self.frames if self.loop else int(_clamp(nxt, 0, self.frames))
        self.time = (nxt / self.frames) * self.duration

    # ---- Clock -------------------------------------------------------------

    def tick(self, elapsed: float) -> bool:
        """Advance by `elapsed` wall seconds; returns True if the time moved.

        Fixed timestep: wall time accumulates and is spent in whole 1/fps steps,
        so the same scene evaluates at the same instants in both renderers no
        matter what the host's frame rate is.
        """
        if not self.playing:
            return False
        self._carry = min(self._carry + elapsed, float(ANIMATION_DEFAULTS["maxStep"]))
        step = 1.0 / self.fps
        advanced = False
        while self.playing and self._carry >= step:
            self._carry -= step
            self._advance(step * self.speed)
            advanced = True
        return advanced

    def state(self) -> dict:
        return {
            "scene": self.name,
            "label": self.label,
            "playing": self.playing,
            "time": self.time,
            "duration": self.duration,
            "progress": self.progress,
            "speed": self.speed,
            "frame": self.frame,
            "frames": self.frames,
            "loop": self.loop,
        }

    def _advance(self, dt: float) -> None:
        self.time += dt
        if self.time < self.duration:
            return
        if self.loop:
            self.time %= self.duration
        else:
            self.time = self.duration
            # The state emitted next carries playing=False — that IS the
            # end-of-scene signal; there is no second callback to miss.
            self.playing = False
