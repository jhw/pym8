import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument
from m8.api.instruments.hypersynth import M8HyperSynth
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8HyperSynthParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor for HyperSynth params
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        
        # Check defaults for key parameters
        self.assertEqual(params.filter, 0x0)  # OFF
        self.assertEqual(params.cutoff, 0xFF)
        self.assertEqual(params.res, 0x0)
        self.assertEqual(params.amp, 0x0)
        self.assertEqual(params.limit, 0x0)  # CLIP = 0
        self.assertEqual(params.pan, 0x80)
        self.assertEqual(params.dry, 0xC0)
        self.assertEqual(params.chorus, 0x0)
        self.assertEqual(params.delay, 0x0)
        self.assertEqual(params.reverb, 0x0)
        self.assertEqual(params.shift, 0x0)
        self.assertEqual(params.swarm, 0x0)
        self.assertEqual(params.width, 0x0)
        self.assertEqual(params.subosc, 0x0)
        self.assertEqual(params.note1, 0x0)
        self.assertEqual(params.note2, 0x0)
        self.assertEqual(params.note3, 0x0)
        self.assertEqual(params.note4, 0x0)
        self.assertEqual(params.note5, 0x0)
        self.assertEqual(params.note6, 0x0)
        
    def test_new_hypersynth_params(self):
        # Test constructor with new HyperSynth params
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            shift=0x20,
            swarm=0x40,
            width=0x60,
            subosc=0x80
        )
        
        # Check values
        self.assertEqual(params.shift, 0x20)
        self.assertEqual(params.swarm, 0x40)
        self.assertEqual(params.width, 0x60)
        self.assertEqual(params.subosc, 0x80)
        
        # Create test binary data with the new parameters
        binary_data = bytearray([0] * 100)
        
        # Set values at the exact offsets from the YAML config
        binary_data[26] = 0x25  # shift at offset 26
        binary_data[27] = 0x45  # swarm at offset 27
        binary_data[28] = 0x65  # width at offset 28
        binary_data[29] = 0x85  # subosc at offset 29
        
        # Create params and read from binary
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        params.read(binary_data)
        
        # Check new parameter values
        self.assertEqual(params.shift, 0x25)
        self.assertEqual(params.swarm, 0x45)
        self.assertEqual(params.width, 0x65)
        self.assertEqual(params.subosc, 0x85)
        
        # Test writing to binary
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            shift=0x21,
            swarm=0x41,
            width=0x61,
            subosc=0x81
        )
        
        # Write to binary
        binary = params.write()
        
        # Check key parameters
        self.assertEqual(binary[26], 0x21)  # shift
        self.assertEqual(binary[27], 0x41)  # swarm
        self.assertEqual(binary[28], 0x61)  # width
        self.assertEqual(binary[29], 0x81)  # subosc
        
        # Test read-write consistency
        original = M8InstrumentParams.from_config("HYPERSYNTH",
            shift=0x22,
            swarm=0x42,
            width=0x62,
            subosc=0x82
        )
        
        binary = original.write()
        deserialized = M8InstrumentParams.from_config("HYPERSYNTH")
        deserialized.read(binary)
        
        self.assertEqual(deserialized.shift, original.shift)
        self.assertEqual(deserialized.swarm, original.swarm)
        self.assertEqual(deserialized.width, original.width)
        self.assertEqual(deserialized.subosc, original.subosc)
        
        # Test dictionary representation
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            shift=0x23,
            swarm=0x43,
            width=0x63,
            subosc=0x83
        )
        
        result = params.as_dict()
        
        self.assertEqual(result["shift"], 0x23)
        self.assertEqual(result["swarm"], 0x43)
        self.assertEqual(result["width"], 0x63)
        self.assertEqual(result["subosc"], 0x83)
        
    def test_hypersynth_note_params(self):
        # Test constructor with note HyperSynth params
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0x31,
            note2=0x32,
            note3=0x33,
            note4=0x34,
            note5=0x35,
            note6=0x36
        )
        
        # Check values
        self.assertEqual(params.note1, 0x31)
        self.assertEqual(params.note2, 0x32)
        self.assertEqual(params.note3, 0x33)
        self.assertEqual(params.note4, 0x34)
        self.assertEqual(params.note5, 0x35)
        self.assertEqual(params.note6, 0x36)
        
        # Create test binary data with the new parameters
        binary_data = bytearray([0] * 100)
        
        # Set values at the exact offsets from the YAML config
        binary_data[19] = 0x41  # note1 at offset 19
        binary_data[20] = 0x42  # note2 at offset 20
        binary_data[21] = 0x43  # note3 at offset 21
        binary_data[22] = 0x44  # note4 at offset 22
        binary_data[23] = 0x45  # note5 at offset 23
        binary_data[24] = 0x46  # note6 at offset 24
        
        # Create params and read from binary
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        params.read(binary_data)
        
        # Check new parameter values
        self.assertEqual(params.note1, 0x41)
        self.assertEqual(params.note2, 0x42)
        self.assertEqual(params.note3, 0x43)
        self.assertEqual(params.note4, 0x44)
        self.assertEqual(params.note5, 0x45)
        self.assertEqual(params.note6, 0x46)
        
        # Test writing to binary
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0x51,
            note2=0x52,
            note3=0x53,
            note4=0x54,
            note5=0x55,
            note6=0x56
        )
        
        # Write to binary
        binary = params.write()
        
        # Check key parameters
        self.assertEqual(binary[19], 0x51)  # note1
        self.assertEqual(binary[20], 0x52)  # note2
        self.assertEqual(binary[21], 0x53)  # note3
        self.assertEqual(binary[22], 0x54)  # note4
        self.assertEqual(binary[23], 0x55)  # note5
        self.assertEqual(binary[24], 0x56)  # note6
        
        # Test read-write consistency
        original = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0x61,
            note2=0x62,
            note3=0x63,
            note4=0x64,
            note5=0x65,
            note6=0x66
        )
        
        binary = original.write()
        deserialized = M8InstrumentParams.from_config("HYPERSYNTH")
        deserialized.read(binary)
        
        self.assertEqual(deserialized.note1, original.note1)
        self.assertEqual(deserialized.note2, original.note2)
        self.assertEqual(deserialized.note3, original.note3)
        self.assertEqual(deserialized.note4, original.note4)
        self.assertEqual(deserialized.note5, original.note5)
        self.assertEqual(deserialized.note6, original.note6)
        
        # Test dictionary representation
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0x71,
            note2=0x72,
            note3=0x73,
            note4=0x74,
            note5=0x75,
            note6=0x76
        )
        
        result = params.as_dict()
        
        self.assertEqual(result["note1"], 0x71)
        self.assertEqual(result["note2"], 0x72)
        self.assertEqual(result["note3"], 0x73)
        self.assertEqual(result["note4"], 0x74)
        self.assertEqual(result["note5"], 0x75)
        self.assertEqual(result["note6"], 0x76)
        
        # Test with kwargs
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Check values
        self.assertEqual(params.filter, 0x02)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x01)
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_read_from_binary(self):
        # Create test binary data with key parameters
        binary_data = bytearray([0] * 100)  # Create a buffer large enough
        
        # Set values at the exact offsets from the YAML config
        binary_data[19] = 0xA1  # note1 (offset 19)
        binary_data[20] = 0xA2  # note2 (offset 20)
        binary_data[21] = 0xA3  # note3 (offset 21)
        binary_data[22] = 0xA4  # note4 (offset 22)
        binary_data[23] = 0xA5  # note5 (offset 23)
        binary_data[24] = 0xA6  # note6 (offset 24)
        binary_data[26] = 0x1A  # shift (offset 26)
        binary_data[27] = 0x2A  # swarm (offset 27)
        binary_data[28] = 0x3A  # width (offset 28)
        binary_data[29] = 0x4A  # subosc (offset 29)
        binary_data[30] = 0x02  # filter (offset 30)
        binary_data[31] = 0xE0  # cutoff (offset 31)
        binary_data[32] = 0x30  # res (offset 32)
        binary_data[33] = 0x40  # amp (offset 33)
        binary_data[34] = 0x01  # limit (offset 34)
        binary_data[35] = 0x60  # pan (offset 35)
        binary_data[36] = 0xB0  # dry (offset 36)
        binary_data[37] = 0x70  # chorus (offset 37)
        binary_data[38] = 0x80  # delay (offset 38)
        binary_data[39] = 0x90  # reverb (offset 39)
        
        # Create params and read from binary
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        params.read(binary_data)
        
        # Check key parameter values
        self.assertEqual(params.note1, 0xA1)
        self.assertEqual(params.note2, 0xA2)
        self.assertEqual(params.note3, 0xA3)
        self.assertEqual(params.note4, 0xA4)
        self.assertEqual(params.note5, 0xA5)
        self.assertEqual(params.note6, 0xA6)
        self.assertEqual(params.shift, 0x1A)
        self.assertEqual(params.swarm, 0x2A)
        self.assertEqual(params.width, 0x3A)
        self.assertEqual(params.subosc, 0x4A)
        self.assertEqual(params.filter, 0x02)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x01)
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_write_to_binary(self):
        # Create params with specific values
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0xB1,
            note2=0xB2,
            note3=0xB3,
            note4=0xB4,
            note5=0xB5,
            note6=0xB6,
            shift=0x15,
            swarm=0x25,
            width=0x35,
            subosc=0x45,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = params.write()
        
        # Check binary has sufficient size
        min_size = 40  # Should at least include up to reverb at offset 39
        self.assertGreaterEqual(len(binary), min_size)
        
        # Check key parameters
        self.assertEqual(binary[19], 0xB1)  # note1
        self.assertEqual(binary[20], 0xB2)  # note2
        self.assertEqual(binary[21], 0xB3)  # note3
        self.assertEqual(binary[22], 0xB4)  # note4
        self.assertEqual(binary[23], 0xB5)  # note5
        self.assertEqual(binary[24], 0xB6)  # note6
        self.assertEqual(binary[26], 0x15)  # shift
        self.assertEqual(binary[27], 0x25)  # swarm
        self.assertEqual(binary[28], 0x35)  # width
        self.assertEqual(binary[29], 0x45)  # subosc
        self.assertEqual(binary[30], 0x02)  # filter
        self.assertEqual(binary[31], 0xE0)  # cutoff
        self.assertEqual(binary[32], 0x30)  # res
        self.assertEqual(binary[33], 0x40)  # amp
        self.assertEqual(binary[34], 0x01)  # limit
        self.assertEqual(binary[35], 0x60)  # pan
        self.assertEqual(binary[36], 0xB0)  # dry
        self.assertEqual(binary[37], 0x70)  # chorus
        self.assertEqual(binary[38], 0x80)  # delay
        self.assertEqual(binary[39], 0x90)  # reverb
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0xC1,
            note2=0xC2,
            note3=0xC3,
            note4=0xC4,
            note5=0xC5,
            note6=0xC6,
            shift=0x16,
            swarm=0x26,
            width=0x36,
            subosc=0x46,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("HYPERSYNTH")
        deserialized.read(binary)
        
        # Check values match
        self.assertEqual(deserialized.note1, original.note1)
        self.assertEqual(deserialized.note2, original.note2)
        self.assertEqual(deserialized.note3, original.note3)
        self.assertEqual(deserialized.note4, original.note4)
        self.assertEqual(deserialized.note5, original.note5)
        self.assertEqual(deserialized.note6, original.note6)
        self.assertEqual(deserialized.shift, original.shift)
        self.assertEqual(deserialized.swarm, original.swarm)
        self.assertEqual(deserialized.width, original.width)
        self.assertEqual(deserialized.subosc, original.subosc)
        self.assertEqual(deserialized.filter, original.filter)
        self.assertEqual(deserialized.cutoff, original.cutoff)
        self.assertEqual(deserialized.res, original.res)
        self.assertEqual(deserialized.amp, original.amp)
        self.assertEqual(deserialized.limit, original.limit)
        self.assertEqual(deserialized.pan, original.pan)
        self.assertEqual(deserialized.dry, original.dry)
        self.assertEqual(deserialized.chorus, original.chorus)
        self.assertEqual(deserialized.delay, original.delay)
        self.assertEqual(deserialized.reverb, original.reverb)
    
    def test_as_dict(self):
        # Create params
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            note1=0xD1,
            note2=0xD2,
            note3=0xD3,
            note4=0xD4,
            note5=0xD5,
            note6=0xD6,
            shift=0x17,
            swarm=0x27,
            width=0x37,
            subosc=0x47,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Convert to dict
        result = params.as_dict()
        
        # Check non-enum values
        self.assertEqual(result["note1"], 0xD1)
        self.assertEqual(result["note2"], 0xD2)
        self.assertEqual(result["note3"], 0xD3)
        self.assertEqual(result["note4"], 0xD4)
        self.assertEqual(result["note5"], 0xD5)
        self.assertEqual(result["note6"], 0xD6)
        self.assertEqual(result["shift"], 0x17)
        self.assertEqual(result["swarm"], 0x27)
        self.assertEqual(result["width"], 0x37)
        self.assertEqual(result["subosc"], 0x47)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["res"], 0x30)
        self.assertEqual(result["amp"], 0x40)
        self.assertEqual(result["pan"], 0x60)
        self.assertEqual(result["dry"], 0xB0)
        self.assertEqual(result["chorus"], 0x70)
        self.assertEqual(result["delay"], 0x80)
        self.assertEqual(result["reverb"], 0x90)
        
        # Check enum values are strings
        self.assertIsInstance(result["filter"], str)
        self.assertIsInstance(result["limit"], str)


class TestM8HyperSynthInstrument(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8HyperSynth()
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x05)  # HYPERSYNTH type_id is 5
        self.assertEqual(synth.instrument_type, "HYPERSYNTH")
        
        # Check params object is created
        self.assertTrue(hasattr(synth, "params"))
        
        # Check common parameters
        self.assertNotEqual(synth.name, "")  # Should auto-generate a name
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x1)
        self.assertEqual(synth.table_tick, 0x01)
        self.assertEqual(synth.volume, 0x0)
        self.assertEqual(synth.pitch, 0x0)
        self.assertEqual(synth.finetune, 0x80)
        
        # Test with kwargs for common parameters
        synth = M8HyperSynth(
            # Common instrument parameters
            name="TestHyperSynth",
            transpose=0x5,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            
            # HyperSynth-specific parameters
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30
        )
        
        # Check common parameters
        self.assertEqual(synth.name, "TestHyperSynth")
        self.assertEqual(synth.transpose, 0x5)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check instrument-specific parameters
        self.assertEqual(synth.params.filter, 0x02)  # HIGHPASS
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.res, 0x30)
    
    def test_from_dict(self):
        # Test creating from dict
        data = {
            "type": "HYPERSYNTH",
            "name": "TestHyperSynth",
            "note1": 0xE1,
            "note2": 0xE2,
            "note3": 0xE3,
            "note4": 0xE4,
            "note5": 0xE5,
            "note6": 0xE6,
            "shift": 0x51,
            "swarm": 0x52,
            "width": 0x53,
            "subosc": 0x54,
            "filter": "HIGHPASS",
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": "SIN",
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        # Create from dict
        synth = M8HyperSynth.from_dict(data)
        
        # Check type
        self.assertEqual(synth.instrument_type, "HYPERSYNTH")
        self.assertEqual(synth.type, 0x05)
        
        # Check it's the right class
        self.assertIsInstance(synth, M8HyperSynth)
        
        # Check parameters
        self.assertEqual(synth.name, "TestHyperSynth")
        self.assertEqual(synth.params.note1, 0xE1)
        self.assertEqual(synth.params.note2, 0xE2)
        self.assertEqual(synth.params.note3, 0xE3)
        self.assertEqual(synth.params.note4, 0xE4)
        self.assertEqual(synth.params.note5, 0xE5)
        self.assertEqual(synth.params.note6, 0xE6)
        self.assertEqual(synth.params.shift, 0x51)
        self.assertEqual(synth.params.swarm, 0x52)
        self.assertEqual(synth.params.width, 0x53)
        self.assertEqual(synth.params.subosc, 0x54)
        self.assertEqual(synth.params.filter, 0x02)  # HIGHPASS
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.res, 0x30)
        self.assertEqual(synth.params.amp, 0x40)
        self.assertEqual(synth.params.limit, 0x01)  # SIN
        self.assertEqual(synth.params.pan, 0x60)
        self.assertEqual(synth.params.dry, 0xB0)
        self.assertEqual(synth.params.chorus, 0x70)
        self.assertEqual(synth.params.delay, 0x80)
        self.assertEqual(synth.params.reverb, 0x90)
    
    def test_as_dict(self):
        # Create synth with specific parameters
        synth = M8HyperSynth(
            name="TestHyperSynth",
            note1=0xF1,
            note2=0xF2,
            note3=0xF3,
            note4=0xF4,
            note5=0xF5,
            note6=0xF6,
            shift=0x61,
            swarm=0x62,
            width=0x63,
            subosc=0x64,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "HYPERSYNTH")
        self.assertEqual(result["name"], "TestHyperSynth")
        
        # Check instrument-specific parameters
        self.assertEqual(result["note1"], 0xF1)
        self.assertEqual(result["note2"], 0xF2)
        self.assertEqual(result["note3"], 0xF3)
        self.assertEqual(result["note4"], 0xF4)
        self.assertEqual(result["note5"], 0xF5)
        self.assertEqual(result["note6"], 0xF6)
        self.assertEqual(result["shift"], 0x61)
        self.assertEqual(result["swarm"], 0x62)
        self.assertEqual(result["width"], 0x63)
        self.assertEqual(result["subosc"], 0x64)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["res"], 0x30)
        self.assertEqual(result["amp"], 0x40)
        self.assertEqual(result["pan"], 0x60)
        self.assertEqual(result["dry"], 0xB0)
        self.assertEqual(result["chorus"], 0x70)
        self.assertEqual(result["delay"], 0x80)
        self.assertEqual(result["reverb"], 0x90)
        
        # Check enum values are strings
        self.assertEqual(result["filter"], "HIGHPASS")
        self.assertEqual(result["limit"], "SIN")
    
    def test_read_parameters(self):
        # Create a HyperSynth
        synth = M8HyperSynth()
        
        # Create test binary data with fixed values
        # Let's test this differently - set values in a way we know will work
        binary_data = bytearray([0] * 100)  # Create a buffer large enough
        
        # Common parameters
        binary_data[0] = 0x05   # type (HyperSynth)
        for i, c in enumerate(b"TEST"):
            binary_data[1 + i] = c  # name
        binary_data[13] = 0x42  # transpose/eq
        binary_data[14] = 0x02  # table_tick
        binary_data[15] = 0x10  # volume
        binary_data[16] = 0x20  # pitch
        binary_data[17] = 0x90  # finetune
        
        # Set HyperSynth specific parameters
        binary_data[19] = 0x10  # note1
        binary_data[20] = 0x20  # note2
        binary_data[21] = 0x30  # note3
        binary_data[22] = 0x40  # note4
        binary_data[23] = 0x50  # note5
        binary_data[24] = 0x60  # note6
        binary_data[26] = 0x70  # shift
        binary_data[27] = 0x71  # swarm
        binary_data[28] = 0x72  # width
        binary_data[29] = 0x73  # subosc
        binary_data[30] = 0x02  # filter
        binary_data[31] = 0xE0  # cutoff
        binary_data[32] = 0x30  # res
        binary_data[33] = 0x40  # amp
        binary_data[34] = 0x01  # limit
        binary_data[35] = 0x60  # pan
        binary_data[36] = 0xB0  # dry
        binary_data[37] = 0x70  # chorus
        binary_data[38] = 0x80  # delay
        binary_data[39] = 0x90  # reverb
        
        # Add additional parameter bytes
        binary_data.extend([0] * (63 - len(binary_data)))  # Fill up to modulator offset
        binary_data.extend([0] * 24)  # Four empty modulators (6 bytes each)
        
        # Call the method to read parameters
        synth._read_parameters(binary_data)
        
        # Check common parameters
        self.assertEqual(synth.type, 0x05)
        self.assertEqual(synth.name, "TEST")
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check instrument-specific parameters
        self.assertEqual(synth.params.note1, 16)  # 0x10
        self.assertEqual(synth.params.note2, 32)  # 0x20
        self.assertEqual(synth.params.note3, 48)  # 0x30
        self.assertEqual(synth.params.note4, 64)  # 0x40
        self.assertEqual(synth.params.note5, 80)  # 0x50
        self.assertEqual(synth.params.note6, 96)  # 0x60
        self.assertEqual(synth.params.shift, 112)  # 0x70
        self.assertEqual(synth.params.swarm, 113)  # 0x71
        self.assertEqual(synth.params.width, 114)  # 0x72
        self.assertEqual(synth.params.subosc, 115)  # 0x73
        self.assertEqual(synth.params.filter, 0x02)  # HIGHPASS
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.res, 0x30)
        self.assertEqual(synth.params.amp, 0x40)
        self.assertEqual(synth.params.limit, 0x01)  # SIN
        self.assertEqual(synth.params.pan, 0x60)
        self.assertEqual(synth.params.dry, 0xB0)
        self.assertEqual(synth.params.chorus, 0x70)
        self.assertEqual(synth.params.delay, 0x80)
        self.assertEqual(synth.params.reverb, 0x90)
    
    def test_write(self):
        # Create synth with specific parameters
        synth = M8HyperSynth(
            name="TEST",
            # Explicitly set common parameters to match the expected values
            transpose=0x4,
            eq=0x2,
            table_tick=0x2,
            volume=0x10,
            pitch=0x20,  # Explicitly set pitch to match assertion
            finetune=0x90,
            note1=0x19,
            note2=0x29,
            note3=0x39,
            note4=0x49,
            note5=0x59,
            note6=0x69,
            shift=0x59,
            swarm=0x5A,
            width=0x5B,
            subosc=0x5C,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Call the method to write
        binary = synth.write()
        
        # Check the binary output
        self.assertEqual(len(binary), 215)  # Should be BLOCK_SIZE bytes
        
        # Check common parameters
        self.assertEqual(binary[0], 0x05)  # type
        self.assertEqual(binary[1:5], b"TEST")  # name (first 4 bytes)
        
        # For transpose/eq, we're combining 0x4 (transpose) and 0x2 (eq)
        # which gives us 0x42 in the binary representation
        self.assertEqual(binary[13], 0x42)  # transpose/eq
        self.assertEqual(binary[14], 0x02)  # table_tick
        self.assertEqual(binary[15], 0x10)  # volume
        self.assertEqual(binary[16], 0x20)  # pitch
        self.assertEqual(binary[17], 0x90)  # finetune
        
        # Check instrument-specific parameters
        self.assertEqual(binary[19], 0x19)  # note1
        self.assertEqual(binary[20], 0x29)  # note2
        self.assertEqual(binary[21], 0x39)  # note3
        self.assertEqual(binary[22], 0x49)  # note4
        self.assertEqual(binary[23], 0x59)  # note5
        self.assertEqual(binary[24], 0x69)  # note6
        self.assertEqual(binary[26], 0x59)  # shift
        self.assertEqual(binary[27], 0x5A)  # swarm
        self.assertEqual(binary[28], 0x5B)  # width
        self.assertEqual(binary[29], 0x5C)  # subosc
        self.assertEqual(binary[30], 0x02)  # filter (HIGHPASS)
        self.assertEqual(binary[31], 0xE0)  # cutoff
        self.assertEqual(binary[32], 0x30)  # res
        self.assertEqual(binary[33], 0x40)  # amp
        self.assertEqual(binary[34], 0x01)  # limit (SIN)
        self.assertEqual(binary[35], 0x60)  # pan
        self.assertEqual(binary[36], 0xB0)  # dry
        self.assertEqual(binary[37], 0x70)  # chorus
        self.assertEqual(binary[38], 0x80)  # delay
        self.assertEqual(binary[39], 0x90)  # reverb
    
    def test_add_modulator(self):
        # Create a HyperSynth
        synth = M8HyperSynth()
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        slot = synth.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(synth.modulators[0].type, 3)  # LFO type value
        self.assertEqual(synth.modulators[0].destination, 2)  # PITCH value
        self.assertEqual(synth.modulators[0].amount, 100)
        self.assertEqual(synth.modulators[0].params.frequency, 50)
    
    def test_read_write_consistency(self):
        # Create original synth
        original = M8HyperSynth(
            name="TEST",  # Using a shorter name to avoid truncation issues
            note1=0x1A,
            note2=0x2A,
            note3=0x3A,
            note4=0x4A,
            note5=0x5A,
            note6=0x6A,
            shift=0x5D,
            swarm=0x5E,
            width=0x5F,
            subosc=0x60,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # SIN
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        original.add_modulator(mod)
        
        # Write to binary
        binary = original.write()
        
        # Create a new instance and read the binary
        deserialized = M8HyperSynth()
        deserialized._read_parameters(binary)
        
        # Check values match
        self.assertEqual(deserialized.name, original.name)
        self.assertEqual(deserialized.params.note1, original.params.note1)
        self.assertEqual(deserialized.params.note2, original.params.note2)
        self.assertEqual(deserialized.params.note3, original.params.note3)
        self.assertEqual(deserialized.params.note4, original.params.note4)
        self.assertEqual(deserialized.params.note5, original.params.note5)
        self.assertEqual(deserialized.params.note6, original.params.note6)
        self.assertEqual(deserialized.params.shift, original.params.shift)
        self.assertEqual(deserialized.params.swarm, original.params.swarm)
        self.assertEqual(deserialized.params.width, original.params.width)
        self.assertEqual(deserialized.params.subosc, original.params.subosc)
        self.assertEqual(deserialized.params.filter, original.params.filter)
        self.assertEqual(deserialized.params.cutoff, original.params.cutoff)
        self.assertEqual(deserialized.params.res, original.params.res)
        self.assertEqual(deserialized.params.amp, original.params.amp)
        self.assertEqual(deserialized.params.limit, original.params.limit)
        self.assertEqual(deserialized.params.pan, original.params.pan)
        self.assertEqual(deserialized.params.dry, original.params.dry)
        self.assertEqual(deserialized.params.chorus, original.params.chorus)
        self.assertEqual(deserialized.params.delay, original.params.delay)
        self.assertEqual(deserialized.params.reverb, original.params.reverb)
        
        # Check modulator
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)


if __name__ == '__main__':
    unittest.main()