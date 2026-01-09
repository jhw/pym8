"""
Euclidean Rhythm Pattern Generators using Bjorklund Algorithm

Based on:
- Bjorklund algorithm: https://github.com/brianhouse/bjorklund
- Euclidean rhythms theory: "The Euclidean Algorithm Generates Traditional Musical Rhythms"
  by Godfried Toussaint (https://cgm.cs.mcgill.ca/~godfried/publications/banff.pdf)

The Bjorklund algorithm distributes k pulses as evenly as possible over n steps,
generating Euclidean rhythms found in traditional music worldwide.

Note: The algorithm takes (steps, pulses) but we output 16-step patterns for M8 by
repeating or truncating the Euclidean pattern as needed.
"""

import random
from typing import List, Tuple


def bjorklund(steps: int, pulses: int) -> List[int]:
    """
    Generate a Euclidean rhythm using the Bjorklund algorithm.

    Args:
        steps: Total number of time positions in the cycle
        pulses: Number of onsets (beats) to distribute

    Returns:
        Binary pattern list where 1 = onset, 0 = rest

    Source: https://github.com/brianhouse/bjorklund
    """
    steps = int(steps)
    pulses = int(pulses)

    if pulses > steps:
        raise ValueError("Pulses cannot exceed steps")

    if pulses == 0:
        return [0] * steps

    pattern = []
    counts = []
    remainders = []
    divisor = steps - pulses
    remainders.append(pulses)
    level = 0

    while True:
        counts.append(divisor // remainders[level])
        remainders.append(divisor % remainders[level])
        divisor = remainders[level]
        level = level + 1
        if remainders[level] <= 1:
            break

    counts.append(divisor)

    def build(level):
        if level == -1:
            pattern.append(0)
        elif level == -2:
            pattern.append(1)
        else:
            for i in range(0, counts[level]):
                build(level - 1)
            if remainders[level] != 0:
                build(level - 2)

    build(level)

    # Rotate so pattern starts with first pulse
    if 1 in pattern:
        i = pattern.index(1)
        pattern = pattern[i:] + pattern[0:i]

    return pattern


# Euclidean Rhythm Presets
# Source: Toussaint, G. "The Euclidean Algorithm Generates Traditional Musical Rhythms"
# https://cgm.cs.mcgill.ca/~godfried/publications/banff.pdf

EUCLIDEAN_RHYTHMS = {
    # E(3,8) - Cuban tresillo [3-3-2]
    # Found in West African music (Ewe dance from Ghana) and Cuban music
    'tresillo': (3, 8),

    # E(5,8) - Cuban cinquillo [2-1-2-1-2]
    # Intimately related to tresillo, used in jazz throughout 20th century
    'cinquillo': (5, 8),

    # E(5,12) - West African bell pattern
    # Used in various African rhythms
    'african_bell_12': (5, 12),

    # E(7,12) - West African bell pattern [2-1-2-2-1-2-2]
    # Popular in Ghana (Ashanti people) and Guinea (Dunumba rhythm)
    'african_bell_7_12': (7, 12),

    # E(5,16) - Bossa nova pattern
    # Common in Brazilian music
    'bossa_nova': (5, 16),

    # E(7,16) - Brazilian/Samba pattern
    # Found in various Brazilian rhythms
    'samba': (7, 16),

    # E(9,16) - Complex rhythm
    # Found in many musical traditions
    'complex_9': (9, 16),

    # E(11,16) - Dense rhythm
    # Nearly binary pattern
    'dense': (11, 16),

    # E(3,4) - Standard waltz
    # Classic 3/4 time signature pattern
    'waltz': (3, 4),

    # E(4,9) - Middle Eastern aksak
    # Irregular meter common in Turkish music
    'aksak': (4, 9),

    # E(5,9) - Another aksak variant
    # Turkish/Balkan irregular meter
    'aksak_5': (5, 9),

    # E(4,7) - Another common pattern
    # Found in various traditions
    'four_seven': (4, 7),

    # E(4,11) - Sparse pattern
    # Creates interesting polyrhythmic feel
    'sparse': (4, 11),
}

# Categorize by type
KICK_RHYTHMS = ['tresillo', 'cinquillo', 'bossa_nova', 'four_seven', 'sparse']
SNARE_RHYTHMS = ['african_bell_12', 'african_bell_7_12', 'aksak', 'aksak_5', 'waltz']
HAT_RHYTHMS = ['samba', 'complex_9', 'dense', 'cinquillo', 'african_bell_7_12']


def euclidean_to_16(pulses: int, steps: int, target_length: int = 16) -> List[int]:
    """
    Generate a Euclidean rhythm and adjust to target length.

    Args:
        pulses: Number of onsets
        steps: Number of steps in Euclidean pattern
        target_length: Desired output length (default 16 for M8 phrases)

    Returns:
        Binary pattern of target_length
    """
    pattern = bjorklund(steps, pulses)

    if len(pattern) == target_length:
        return pattern
    elif len(pattern) < target_length:
        # Repeat pattern to fill target length
        repeats = (target_length // len(pattern)) + 1
        extended = (pattern * repeats)[:target_length]
        return extended
    else:
        # Truncate to target length
        return pattern[:target_length]


# Groove Algorithms (inspired by Erica Synths Perkons HD-01)
# Source: Perkons HD-01 applies groove templates that "humanize" patterns
# with volume variations on specific steps

def groove_straight(pattern: List[int]) -> List[float]:
    """
    Straight groove - uniform velocity.

    Args:
        pattern: Binary pattern (0s and 1s)

    Returns:
        Pattern with velocities (0.0-1.0)
    """
    return [0.9 if hit else 0.0 for hit in pattern]


def groove_accent_downbeats(pattern: List[int]) -> List[float]:
    """
    Accent downbeats (every 4th step).

    Args:
        pattern: Binary pattern

    Returns:
        Pattern with accented downbeats
    """
    result = []
    for i, hit in enumerate(pattern):
        if not hit:
            result.append(0.0)
        elif i % 4 == 0:
            result.append(1.0)  # Accent downbeat
        else:
            result.append(0.7)  # Normal hit
    return result


def groove_accent_offbeats(pattern: List[int]) -> List[float]:
    """
    Accent offbeats (every other step).

    Args:
        pattern: Binary pattern

    Returns:
        Pattern with accented offbeats
    """
    result = []
    for i, hit in enumerate(pattern):
        if not hit:
            result.append(0.0)
        elif i % 2 == 1:
            result.append(0.95)  # Accent offbeat
        else:
            result.append(0.6)  # Normal hit
    return result


def groove_velocity_ramp(pattern: List[int]) -> List[float]:
    """
    Velocity ramp - gradually increase velocity through pattern.

    Args:
        pattern: Binary pattern

    Returns:
        Pattern with ramping velocities
    """
    result = []
    hits = sum(pattern)
    if hits == 0:
        return [0.0] * len(pattern)

    hit_count = 0
    for hit in pattern:
        if hit:
            # Ramp from 0.5 to 1.0
            velocity = 0.5 + (0.5 * hit_count / (hits - 1)) if hits > 1 else 0.8
            result.append(velocity)
            hit_count += 1
        else:
            result.append(0.0)
    return result


def groove_random_humanize(pattern: List[int], rng: random.Random) -> List[float]:
    """
    Random humanization - slight velocity variations.

    Args:
        pattern: Binary pattern
        rng: Random number generator

    Returns:
        Pattern with humanized velocities
    """
    result = []
    for hit in pattern:
        if hit:
            # Random velocity between 0.6 and 1.0
            velocity = 0.6 + (rng.random() * 0.4)
            result.append(velocity)
        else:
            result.append(0.0)
    return result


def groove_swing(pattern: List[int]) -> List[float]:
    """
    Swing groove - emphasize alternating hits.

    Args:
        pattern: Binary pattern

    Returns:
        Pattern with swing feel
    """
    result = []
    hit_idx = 0
    for hit in pattern:
        if not hit:
            result.append(0.0)
        else:
            # Alternate between strong and weak
            velocity = 0.95 if hit_idx % 2 == 0 else 0.65
            result.append(velocity)
            hit_idx += 1
    return result


# Groove registry
GROOVE_FUNCTIONS = [
    groove_straight,
    groove_accent_downbeats,
    groove_accent_offbeats,
    groove_velocity_ramp,
    groove_random_humanize,
    groove_swing,
]


def get_random_euclidean_pattern(
    rhythm_type: str,
    rng: random.Random,
    length: int = 16
) -> Tuple[str, List[float]]:
    """
    Generate a random Euclidean rhythm with groove applied.

    Args:
        rhythm_type: 'kick', 'snare', or 'hat'
        rng: Random number generator
        length: Output pattern length

    Returns:
        Tuple of (rhythm_name, velocity_pattern)
    """
    # Select appropriate rhythm set
    if rhythm_type == 'kick':
        rhythm_names = KICK_RHYTHMS
    elif rhythm_type == 'snare':
        rhythm_names = SNARE_RHYTHMS
    else:  # hat
        rhythm_names = HAT_RHYTHMS

    # Pick random rhythm
    rhythm_name = rng.choice(rhythm_names)
    pulses, steps = EUCLIDEAN_RHYTHMS[rhythm_name]

    # Generate binary pattern
    pattern = euclidean_to_16(pulses, steps, length)

    # Apply random groove
    groove_func = rng.choice(GROOVE_FUNCTIONS)
    if groove_func == groove_random_humanize:
        velocity_pattern = groove_func(pattern, rng)
    else:
        velocity_pattern = groove_func(pattern)

    return rhythm_name, velocity_pattern
