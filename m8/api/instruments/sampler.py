# m8/api/instruments/sampler.py
from m8.api.instruments import M8InstrumentBase, M8ParamsBase, M8ParamType

class M8SamplerParams(M8ParamsBase):
    """Class to handle Sampler parameters including playback, filtering, amp, and mixer settings.
    
    The Sampler is a key instrument in the M8 tracker that allows loading and manipulating 
    external audio samples. This class manages all parameters related to sample playback,
    filtering, amplification, and mixing, along with the path to the sample file.
    
    The parameters are organized into sections:
    - Playback section: play_mode, slice, start, loop_start, length, degrade
    - Filter section: filter type, cutoff, resonance
    - Amp section: amplitude, limiting
    - Mixer section: panning, dry level, effect sends (chorus, delay, reverb)
    - Sample reference: path to the sample file
    """
    
    _param_defs = [
        # Synth section parameters
        ("play_mode", 0x0, M8ParamType.UINT8, 18, 19),    # Sample playback mode
        ("slice", 0x0, M8ParamType.UINT8, 19, 20),        # Current slice index if using sliced sample
        ("start", 0x0, M8ParamType.UINT8, 20, 21),        # Sample start position
        ("loop_start", 0x0, M8ParamType.UINT8, 21, 22),   # Loop start position
        ("length", 0xFF, M8ParamType.UINT8, 22, 23),      # Sample playback length - default 0xFF (full)
        ("degrade", 0x0, M8ParamType.UINT8, 23, 24),      # Bit degradation amount
        
        # Filter section parameters
        ("filter", 0x0, M8ParamType.UINT8, 24, 25),       # Filter type selection
        ("cutoff", 0xFF, M8ParamType.UINT8, 25, 26),      # Filter cutoff frequency - default 0xFF (fully open)
        ("res", 0x0, M8ParamType.UINT8, 26, 27),          # Filter resonance
        
        # Amp section parameters
        ("amp", 0x0, M8ParamType.UINT8, 27, 28),          # Amplifier drive amount
        ("limit", 0x0, M8ParamType.UINT8, 28, 29),        # Limiting amount
        
        # Mixer section parameters
        ("pan", 0x80, M8ParamType.UINT8, 29, 30),         # Stereo panning - default 0x80 (centered)
        ("dry", 0xC0, M8ParamType.UINT8, 30, 31),         # Dry signal level - default 0xC0 (75%)
        ("chorus", 0x0, M8ParamType.UINT8, 31, 32),       # Chorus send level
        ("delay", 0x0, M8ParamType.UINT8, 32, 33),        # Delay send level
        ("reverb", 0x0, M8ParamType.UINT8, 33, 34),       # Reverb send level
        
        # Sample path at offset 0x57 with length 128
        ("sample_path", "", M8ParamType.STRING, 0x57, 0x57 + 128)  # Path to sample file
    ]
    
    def __init__(self, offset=None, **kwargs):
        """Initialize Sampler parameters.
        
        Args:
            offset (int, optional): Byte offset for parameter data in the binary structure.
            **kwargs: Parameter values to set during initialization.
        """
        super().__init__(self._param_defs, offset, **kwargs)

class M8Sampler(M8InstrumentBase):
    """Sampler instrument implementation for the M8 tracker.
    
    The Sampler is a sample-based instrument in the M8 tracker with a type ID of 0x02.
    It allows loading and manipulating external audio samples with controls for playback
    mode, slicing, start/loop positions, length, filtering, amplification, and mixing.
    This class manages the Sampler instrument parameters and serialization/deserialization
    for M8 project files.
    """
    
    # Offset for modulator data in the binary structure
    MODULATORS_OFFSET = 63
    
    def __init__(self, **kwargs):
        """Initialize a Sampler instrument.
        
        Creates a new Sampler instrument with the specified parameters. Parameters specific to
        the Sampler are passed to the underlying M8SamplerParams object.
        
        Args:
            **kwargs: Instrument parameters to set during initialization. Can include both
                     general instrument parameters and sampler-specific parameters.
        """
        # Set type before calling parent class init
        self.type = 0x02  # Type ID for Sampler instruments
        
        # Create synth parameter object
        self.synth = M8SamplerParams()
        
        # Gather all parameters that match parameters in the synth object
        synth_kwargs = {}
        for key in kwargs:
            if hasattr(self.synth, key):
                synth_kwargs[key] = kwargs[key]
        
        # Apply the parameters to the synth object
        for key, value in synth_kwargs.items():
            setattr(self.synth, key, value)
        
        # Call parent constructor to finish setup
        super().__init__(**kwargs)
    
    def _read_specific_parameters(self, data, offset):
        """Read Sampler-specific parameters from binary data.
        
        Args:
            data (bytes): Binary data containing instrument parameters.
            offset (int): Byte offset where instrument data begins.
        """
        self.synth = M8SamplerParams.read(data)
    
    def _write_specific_parameters(self):
        """Write Sampler-specific parameters to binary format.
        
        Returns:
            bytes: Binary representation of the Sampler parameters.
        """
        return self.synth.write()
    
    def is_empty(self):
        """Check if the Sampler instrument is empty/initialized to defaults.
        
        An empty Sampler is defined as having an empty name, zero volume,
        and no sample path assigned.
        
        Returns:
            bool: True if the instrument is empty, False otherwise.
        """
        return (self.name.strip() == "" and 
                self.volume == 0x0 and 
                self.synth.sample_path == "")
