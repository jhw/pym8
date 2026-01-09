"""
Acid Banger 909 Pattern Generators

Python port of vitling's acid-banger drum patterns (909 drum machine patterns) from:
https://github.com/vitling/acid-banger

Each function generates a 16-step pattern with velocity values (0.0-1.0).
Zero indicates no hit (off).

Note: This module contains 909-style drum patterns. For 303-style acid basslines,
see the separate acid_banger_303 module.
"""

import random
from typing import List


def kick_fourfloor(rng: random.Random, length: int = 16) -> List[float]:
    """Four-on-the-floor kick pattern.

    Kicks on every 4th beat (0.9 intensity), with 10% chance
    of additional kicks on even beats (0.6 intensity).
    """
    pattern = [0.0] * length
    for i in range(length):
        if i % 4 == 0:
            pattern[i] = 0.9
        elif i % 2 == 0 and rng.random() < 0.1:
            pattern[i] = 0.6
    return pattern


def kick_electro(rng: random.Random, length: int = 16) -> List[float]:
    """Electro kick pattern.

    Kick at position 0 (1.0), random mid-tempo hits at 50% probability
    (0.9 max), plus sparse random triggers at 5% chance.
    """
    pattern = [0.0] * length
    for i in range(length):
        if i == 0:
            pattern[i] = 1.0
        elif i % 2 == 0 and i % 8 != 4 and rng.random() < 0.5:
            pattern[i] = rng.random() * 0.9
        elif rng.random() < 0.05:
            pattern[i] = rng.random() * 0.9
    return pattern


def snare_backbeat(rng: random.Random, length: int = 16) -> List[float]:
    """Backbeat snare pattern.

    Snare hits at positions 4 and 12 (1.0 intensity).
    Classic 2 and 4 backbeat.
    """
    pattern = [0.0] * length
    for i in range(length):
        if i % 8 == 4:
            pattern[i] = 1.0
    return pattern


def snare_skip(rng: random.Random, length: int = 16) -> List[float]:
    """Skip snare pattern.

    Snare at positions 3,6,11,14 (0.6-1.0 intensity) plus additional
    random hits with varying probabilities.
    """
    pattern = [0.0] * length
    for i in range(length):
        if i % 8 == 3 or i % 8 == 6:
            pattern[i] = 0.6 + rng.random() * 0.4
        elif i % 2 == 0 and rng.random() < 0.2:
            pattern[i] = 0.4 + rng.random() * 0.2
        elif rng.random() < 0.1:
            pattern[i] = 0.2 + rng.random() * 0.2
    return pattern


def hat_closed(rng: random.Random, length: int = 16) -> List[float]:
    """Closed hi-hat pattern.

    Hits every other beat at 0.4 intensity, with 50% chance
    of additional varied hits.
    """
    pattern = [0.0] * length
    for i in range(length):
        if i % 2 == 0:
            pattern[i] = 0.4
        elif rng.random() < 0.5:
            pattern[i] = rng.random() * 0.3
    return pattern


def hat_offbeats(rng: random.Random, length: int = 16) -> List[float]:
    """Offbeat hi-hat pattern.

    Hits at positions 2,6,10,14 at 0.4 intensity, with 30% chance
    of additional random hits (0.2 max).
    """
    pattern = [0.0] * length
    for i in range(length):
        if i % 4 == 2:
            pattern[i] = 0.4
        elif rng.random() < 0.3:
            pattern[i] = rng.random() * 0.2
    return pattern


# Pattern function registries by type
KICK_PATTERNS = {
    'fourfloor': kick_fourfloor,
    'electro': kick_electro,
}

SNARE_PATTERNS = {
    'backbeat': snare_backbeat,
    'skip': snare_skip,
}

HAT_PATTERNS = {
    'closed': hat_closed,
    'offbeats': hat_offbeats,
}


def get_random_kick_pattern(rng: random.Random, length: int = 16) -> tuple[str, List[float]]:
    """Get a random kick pattern."""
    pattern_name = rng.choice(list(KICK_PATTERNS.keys()))
    pattern = KICK_PATTERNS[pattern_name](rng, length)
    return pattern_name, pattern


def get_random_snare_pattern(rng: random.Random, length: int = 16) -> tuple[str, List[float]]:
    """Get a random snare pattern."""
    pattern_name = rng.choice(list(SNARE_PATTERNS.keys()))
    pattern = SNARE_PATTERNS[pattern_name](rng, length)
    return pattern_name, pattern


def get_random_hat_pattern(rng: random.Random, length: int = 16) -> tuple[str, List[float]]:
    """Get a random hat pattern."""
    pattern_name = rng.choice(list(HAT_PATTERNS.keys()))
    pattern = HAT_PATTERNS[pattern_name](rng, length)
    return pattern_name, pattern
