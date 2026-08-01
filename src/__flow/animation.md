# Timeline — Flow

**About:** [description](../__about/animation.md)

## Algorithm

```mermaid
flowchart TB
    A[sampleTrack track, progress] --> B{progress <= first key t?}
    B -->|yes| C[return first key value]
    B -->|no| D{progress >= last key t?}
    D -->|yes| E[return last key value]
    D -->|no| F[find bracketing keys from, to]
    F --> G[local = progress - from.t / to.t - from.t]
    G --> H[eased = ease from.ease, local]
    H --> I{from.value and to.value both numbers?}
    I -->|yes| J[lerp the two numbers by eased]
    I -->|no| K{both vectors, same length?}
    K -->|yes| L[lerp each component by eased]
    K -->|no| M[STEP: return from.value]
```

Pseudocode (language-neutral):

    FUNCTION sampleTrack(track, progress):
        keys ← track.keys, sorted by t
        IF progress <= keys[0].t → RETURN keys[0].value
        IF progress >= keys[last].t → RETURN keys[last].value
        (from, to) ← the consecutive key pair bracketing progress
        local ← (progress - from.t) / (to.t - from.t)
        eased ← ease(from.ease OR default, local)
        IF from.value AND to.value are both numbers:
            RETURN from.value + (to.value - from.value) × eased
        IF from.value AND to.value are both vectors of the SAME length:
            RETURN [lerp each component by eased]        # part.position slides
        OTHERWISE:
            RETURN from.value                              # names, flags, mismatched shapes STEP

    FUNCTION tick(elapsedSeconds):                          # the clock, fixed timestep
        carry ← min(carry + elapsedSeconds, maxStep)
        step ← 1 / fps
        moved ← false
        WHILE playing AND carry >= step:
            carry ← carry - step
            advance(step × speed)
            moved ← true
        RETURN moved

A key's easing governs the segment that **starts** at it, so the last key's easing is never used. A **vector** is a fixed-length array of numbers — `part.position`'s `[x, y, z]` — lerped component-wise by the identical rule a lone number follows; two vectors of different lengths cannot be lerped and step instead, the same fallback a name or a flag gets.
