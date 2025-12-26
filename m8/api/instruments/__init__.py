"""M8 Instruments module."""

from m8.api.instrument import M8FilterType, M8LimiterType
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam, M8PlayMode, M8SamplerModDest
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam, M8WavShape, M8WavsynthModDest
from m8.api.instruments.fmsynth import M8FMSynth, M8FMSynthParam, M8FMAlgo, M8FMWave, M8FMSynthModDest, M8FMOperatorModDest

__all__ = [
    # Common enums (shared across instrument types)
    'M8FilterType',
    'M8LimiterType',
    # Sampler
    'M8Sampler',
    'M8SamplerParam',
    'M8PlayMode',
    'M8SamplerModDest',
    # Wavsynth
    'M8Wavsynth',
    'M8WavsynthParam',
    'M8WavShape',
    'M8WavsynthModDest',
    # FM Synth
    'M8FMSynth',
    'M8FMSynthParam',
    'M8FMAlgo',
    'M8FMWave',
    'M8FMSynthModDest',
    'M8FMOperatorModDest',
]
