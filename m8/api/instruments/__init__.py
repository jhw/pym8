"""M8 Instruments module."""

from m8.api.instruments.sampler import M8Sampler, M8SamplerParam, M8PlayMode
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavShape

__all__ = [
    'M8Sampler',
    'M8SamplerParam',
    'M8PlayMode',
    'M8Wavsynth',
    'M8WavsynthParam',
    'M8WavShape',
]
