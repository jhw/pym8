"""M8 instrument types."""

from m8.api.instrument import M8FilterType, M8LimiterType
from m8.api.instruments.sampler import (
    M8Sampler, M8PlayMode, M8SamplerModDest,
)
from m8.api.instruments.wavsynth import (
    M8Wavsynth, M8WavShape, M8WavsynthModDest,
)
from m8.api.instruments.macrosynth import (
    M8Macrosynth, M8MacroShape, M8MacrosynthModDest,
)
from m8.api.instruments.fmsynth import (
    M8FMSynth, M8FMAlgo, M8FMWave, M8FMSynthModDest, M8FMOperatorModDest,
)
from m8.api.instruments.external import (
    M8External, M8ExternalInput, M8ExternalPort, M8ExternalModDest,
)
from m8.api.instruments.midiout import (
    M8MIDIOut, M8MIDIPort, M8MIDIOutModDest,
)

__all__ = [
    "M8FilterType",
    "M8LimiterType",
    "M8Sampler", "M8PlayMode", "M8SamplerModDest",
    "M8Wavsynth", "M8WavShape", "M8WavsynthModDest",
    "M8Macrosynth", "M8MacroShape", "M8MacrosynthModDest",
    "M8FMSynth", "M8FMAlgo", "M8FMWave", "M8FMSynthModDest", "M8FMOperatorModDest",
    "M8External", "M8ExternalInput", "M8ExternalPort", "M8ExternalModDest",
    "M8MIDIOut", "M8MIDIPort", "M8MIDIOutModDest",
]
