"""
Acid Banger 303 Pattern Generators

Python port of vitling's acid-banger 303 bassline patterns from:
https://github.com/vitling/acid-banger

Each function generates patterns with note and velocity values for TB-303 style acid basslines.
Patterns use probability-based triggering to create varied sequences.

Note values are integers (0-127) representing MIDI note offsets from C1 (value 0).
Velocity values are floats (0.0-1.0), where 0.0 means no hit.
"""

import random
from typing import List, Tuple, Optional


# 303 offset patterns from acid-banger (semitones from root note)
# These are the exact patterns from vitling's acid-banger pattern.ts
OFFSET_PATTERNS = [
    [0, 0, 12, 24, 27],                       # Octave jumps with high fifth
    [0, 0, 0, 12, 10, 19, 26, 27],            # Dense chromatic spread
    [0, 1, 7, 10, 12, 13],                    # Chromatic cluster
    [0],                                       # Single note (root only)
    [0, 0, 0, 12],                            # Root emphasis with octave
    [0, 0, 12, 14, 15, 19],                   # Octave with chromatic upper
    [0, 0, 0, 0, 12, 13, 16, 19, 22, 24, 25], # Wide chromatic range
    [0, 0, 0, 7, 12, 15, 17, 20, 24],         # Fifth-based with extensions
]


class AcidPattern:
    """Represents a 303-style acid bassline pattern.

    Attributes:
        notes: List of MIDI note values (0-127), None means no note
        velocities: List of velocity values (0.0-1.0)
        accents: List of booleans indicating accented notes
        glides: List of booleans indicating glide/slide between notes
    """

    def __init__(self, length: int = 16):
        self.notes: List[Optional[int]] = [None] * length
        self.velocities: List[float] = [0.0] * length
        self.accents: List[bool] = [False] * length
        self.glides: List[bool] = [False] * length

    def __len__(self) -> int:
        return len(self.notes)


def bass_303_random(rng: random.Random, length: int = 64,
                    root_note: int = 24, density: float = 1.0) -> AcidPattern:
    """Generate a random 303-style acid bassline pattern.

    Uses vitling's acid-banger probability system:
    - Steps 0,4,8,12...: 60% chance
    - Steps divisible by 3: 50% chance
    - Even steps: 30% chance
    - Remaining odd steps: 10% chance

    Args:
        rng: Random number generator
        length: Pattern length in steps (default 64 for 4x16-step phrases)
        root_note: MIDI root note (default 24 = C3)
        density: Overall note density multiplier (default 1.0)

    Returns:
        AcidPattern with notes, velocities, accents, and glides
    """
    pattern = AcidPattern(length)

    # Choose a random offset pattern
    offsets = rng.choice(OFFSET_PATTERNS)

    # Generate notes for each step using probability-based triggering
    for i in range(length):
        # Calculate trigger probability based on step position
        if i % 4 == 0:
            # Strong beats (0, 4, 8, 12, ...)
            probability = 0.6
        elif i % 3 == 0:
            # Every third step
            probability = 0.5
        elif i % 2 == 0:
            # Even steps
            probability = 0.3
        else:
            # Odd steps
            probability = 0.1

        # Apply density multiplier
        probability *= density

        # Trigger note?
        if rng.random() < probability:
            # Choose random offset and create note
            offset = rng.choice(offsets)
            pattern.notes[i] = root_note + offset

            # Base velocity (0.7-1.0 range for varied dynamics)
            base_velocity = 0.7 + rng.random() * 0.3

            # Accent (30% chance)
            if rng.random() < 0.3:
                pattern.accents[i] = True
                pattern.velocities[i] = min(1.0, base_velocity * 1.2)
            else:
                pattern.velocities[i] = base_velocity

            # Glide/slide (10% chance, only if not first note and previous note exists)
            if i > 0 and pattern.notes[i - 1] is not None and rng.random() < 0.1:
                pattern.glides[i] = True

    return pattern


def bass_303_sparse(rng: random.Random, length: int = 64,
                    root_note: int = 24) -> AcidPattern:
    """Generate a sparse 303 pattern (lower density).

    Uses density=0.6 for less frequent notes.
    """
    return bass_303_random(rng, length, root_note, density=0.6)


def bass_303_dense(rng: random.Random, length: int = 64,
                   root_note: int = 24) -> AcidPattern:
    """Generate a dense 303 pattern (higher density).

    Uses density=1.3 for more frequent notes.
    """
    return bass_303_random(rng, length, root_note, density=1.3)


def bass_303_offbeat(rng: random.Random, length: int = 64,
                     root_note: int = 24) -> AcidPattern:
    """Generate an offbeat 303 pattern emphasizing syncopation.

    Higher probability on offbeats (odd steps).
    """
    pattern = AcidPattern(length)
    offsets = rng.choice(OFFSET_PATTERNS)

    for i in range(length):
        # Emphasize offbeats
        if i % 2 == 1:
            probability = 0.7
        elif i % 4 == 0:
            probability = 0.3
        else:
            probability = 0.2

        if rng.random() < probability:
            offset = rng.choice(offsets)
            pattern.notes[i] = root_note + offset
            pattern.velocities[i] = 0.7 + rng.random() * 0.3

            if rng.random() < 0.3:
                pattern.accents[i] = True
                pattern.velocities[i] = min(1.0, pattern.velocities[i] * 1.2)

            if i > 0 and pattern.notes[i - 1] is not None and rng.random() < 0.1:
                pattern.glides[i] = True

    return pattern


# Pattern function registry
BASS_303_PATTERNS = {
    'random': bass_303_random,
    'sparse': bass_303_sparse,
    'dense': bass_303_dense,
    'offbeat': bass_303_offbeat,
}


def get_random_303_pattern(rng: random.Random, length: int = 64,
                          root_note: int = 24) -> Tuple[str, AcidPattern]:
    """Get a random 303 bassline pattern.

    Args:
        rng: Random number generator
        length: Pattern length in steps (default 64)
        root_note: MIDI root note (default 24 = C3)

    Returns:
        Tuple of (pattern_name, AcidPattern)
    """
    pattern_name = rng.choice(list(BASS_303_PATTERNS.keys()))
    pattern = BASS_303_PATTERNS[pattern_name](rng, length, root_note)
    return pattern_name, pattern
