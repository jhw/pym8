# m8/api/instruments/__init__.py
"""Simplified sampler-only instrument system."""

from m8.api.instruments.sampler import M8Sampler, M8InstrumentParams, BLOCK_SIZE, BLOCK_COUNT

# Re-export for compatibility
M8Instrument = M8Sampler
M8Instruments = None  # Will be imported below

# Avoid circular import by importing M8Instruments after the classes are defined
from m8.api.instruments.sampler import M8Instruments

__all__ = ['M8Sampler', 'M8Instrument', 'M8Instruments', 'M8InstrumentParams', 'BLOCK_SIZE', 'BLOCK_COUNT']
