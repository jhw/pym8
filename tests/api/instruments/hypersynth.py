import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument
from m8.api.instruments.hypersynth import M8HyperSynth
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8HyperSynthParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor for HyperSynth params
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        
        # Check defaults for key parameters
        self.assertEqual(params.shape, 0x0)  # SIN
        self.assertEqual(params.harmonics, 0x80)
        self.assertEqual(params.mix, 0x80)
        self.assertEqual(params.morph, 0x0)
        self.assertEqual(params.spread, 0x0)
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
        
        # Test with kwargs
        params = M8InstrumentParams.from_config("HYPERSYNTH",
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        self.assertEqual(params.shape, 0x02)
        self.assertEqual(params.harmonics, 0x70)
        self.assertEqual(params.mix, 0x90)
        self.assertEqual(params.morph, 0x10)
        self.assertEqual(params.spread, 0x20)
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
        binary_data[18] = 0x02  # shape (offset 18)
        binary_data[19] = 0x70  # harmonics (offset 19)
        binary_data[20] = 0x90  # mix (offset 20)
        binary_data[21] = 0x10  # morph (offset 21)
        binary_data[22] = 0x20  # spread (offset 22)
        binary_data[23] = 0x02  # filter (offset 23)
        binary_data[24] = 0xE0  # cutoff (offset 24)
        binary_data[25] = 0x30  # res (offset 25)
        binary_data[26] = 0x40  # amp (offset 26)
        binary_data[27] = 0x01  # limit (offset 27)
        binary_data[28] = 0x60  # pan (offset 28)
        binary_data[29] = 0xB0  # dry (offset 29)
        binary_data[30] = 0x70  # chorus (offset 30)
        binary_data[31] = 0x80  # delay (offset 31)
        binary_data[32] = 0x90  # reverb (offset 32)
        
        # Create params and read from binary
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        params.read(binary_data)
        
        # Check key parameter values
        self.assertEqual(params.shape, 0x02)
        self.assertEqual(params.harmonics, 0x70)
        self.assertEqual(params.mix, 0x90)
        self.assertEqual(params.morph, 0x10)
        self.assertEqual(params.spread, 0x20)
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
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        min_size = 33  # Should at least include up to reverb at offset 32
        self.assertGreaterEqual(len(binary), min_size)
        
        # Check key parameters
        self.assertEqual(binary[18], 0x02)  # shape
        self.assertEqual(binary[19], 0x70)  # harmonics
        self.assertEqual(binary[20], 0x90)  # mix
        self.assertEqual(binary[21], 0x10)  # morph
        self.assertEqual(binary[22], 0x20)  # spread
        self.assertEqual(binary[23], 0x02)  # filter
        self.assertEqual(binary[24], 0xE0)  # cutoff
        self.assertEqual(binary[25], 0x30)  # res
        self.assertEqual(binary[26], 0x40)  # amp
        self.assertEqual(binary[27], 0x01)  # limit
        self.assertEqual(binary[28], 0x60)  # pan
        self.assertEqual(binary[29], 0xB0)  # dry
        self.assertEqual(binary[30], 0x70)  # chorus
        self.assertEqual(binary[31], 0x80)  # delay
        self.assertEqual(binary[32], 0x90)  # reverb
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8InstrumentParams.from_config("HYPERSYNTH",
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        self.assertEqual(deserialized.shape, original.shape)
        self.assertEqual(deserialized.harmonics, original.harmonics)
        self.assertEqual(deserialized.mix, original.mix)
        self.assertEqual(deserialized.morph, original.morph)
        self.assertEqual(deserialized.spread, original.spread)
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
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        self.assertEqual(result["harmonics"], 0x70)
        self.assertEqual(result["mix"], 0x90)
        self.assertEqual(result["morph"], 0x10)
        self.assertEqual(result["spread"], 0x20)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["res"], 0x30)
        self.assertEqual(result["amp"], 0x40)
        self.assertEqual(result["pan"], 0x60)
        self.assertEqual(result["dry"], 0xB0)
        self.assertEqual(result["chorus"], 0x70)
        self.assertEqual(result["delay"], 0x80)
        self.assertEqual(result["reverb"], 0x90)
        
        # Check enum values are strings
        self.assertIsInstance(result["shape"], str)
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
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90
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
        self.assertEqual(synth.params.shape, 0x02)  # SQR
        self.assertEqual(synth.params.harmonics, 0x70)
        self.assertEqual(synth.params.mix, 0x90)
    
    def test_from_dict(self):
        # Test creating from dict
        data = {
            "type": "HYPERSYNTH",
            "name": "TestHyperSynth",
            "shape": "SQR",
            "harmonics": 0x70,
            "mix": 0x90,
            "morph": 0x10,
            "spread": 0x20,
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
        self.assertEqual(synth.params.shape, 0x02)  # SQR
        self.assertEqual(synth.params.harmonics, 0x70)
        self.assertEqual(synth.params.mix, 0x90)
        self.assertEqual(synth.params.morph, 0x10)
        self.assertEqual(synth.params.spread, 0x20)
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
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        self.assertEqual(result["harmonics"], 0x70)
        self.assertEqual(result["mix"], 0x90)
        self.assertEqual(result["morph"], 0x10)
        self.assertEqual(result["spread"], 0x20)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["res"], 0x30)
        self.assertEqual(result["amp"], 0x40)
        self.assertEqual(result["pan"], 0x60)
        self.assertEqual(result["dry"], 0xB0)
        self.assertEqual(result["chorus"], 0x70)
        self.assertEqual(result["delay"], 0x80)
        self.assertEqual(result["reverb"], 0x90)
        
        # Check enum values are strings
        self.assertEqual(result["shape"], "SQR")
        self.assertEqual(result["filter"], "HIGHPASS")
        self.assertEqual(result["limit"], "SIN")
    
    def test_read_parameters(self):
        # Create a HyperSynth
        synth = M8HyperSynth()
        
        # Create test binary data
        binary_data = bytearray([
            0x05,   # type (HyperSynth)
            0x54, 0x45, 0x53, 0x54, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # name "TEST"
            0x42,   # transpose/eq (4/2)
            0x02,   # table_tick
            0x10,   # volume
            0x20,   # pitch
            0x90,   # finetune
            0x02,   # shape (SQR)
            0x70,   # harmonics
            0x90,   # mix
            0x10,   # morph
            0x20,   # spread
            0x02,   # filter (HIGHPASS)
            0xE0,   # cutoff
            0x30,   # res
            0x40,   # amp
            0x01,   # limit (SIN)
            0x60,   # pan
            0xB0,   # dry
            0x70,   # chorus
            0x80,   # delay
            0x90    # reverb
        ])
        
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
        self.assertEqual(synth.params.shape, 0x02)  # SQR
        self.assertEqual(synth.params.harmonics, 0x70)
        self.assertEqual(synth.params.mix, 0x90)
        self.assertEqual(synth.params.morph, 0x10)
        self.assertEqual(synth.params.spread, 0x20)
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
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        self.assertEqual(binary[18], 0x02)  # shape (SQR)
        self.assertEqual(binary[19], 0x70)  # harmonics
        self.assertEqual(binary[20], 0x90)  # mix
        self.assertEqual(binary[21], 0x10)  # morph
        self.assertEqual(binary[22], 0x20)  # spread
        self.assertEqual(binary[23], 0x02)  # filter (HIGHPASS)
        self.assertEqual(binary[24], 0xE0)  # cutoff
        self.assertEqual(binary[25], 0x30)  # res
        self.assertEqual(binary[26], 0x40)  # amp
        self.assertEqual(binary[27], 0x01)  # limit (SIN)
        self.assertEqual(binary[28], 0x60)  # pan
        self.assertEqual(binary[29], 0xB0)  # dry
        self.assertEqual(binary[30], 0x70)  # chorus
        self.assertEqual(binary[31], 0x80)  # delay
        self.assertEqual(binary[32], 0x90)  # reverb
    
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
            shape=0x02,  # SQR
            harmonics=0x70,
            mix=0x90,
            morph=0x10,
            spread=0x20,
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
        self.assertEqual(deserialized.params.shape, original.params.shape)
        self.assertEqual(deserialized.params.harmonics, original.params.harmonics)
        self.assertEqual(deserialized.params.mix, original.params.mix)
        self.assertEqual(deserialized.params.morph, original.params.morph)
        self.assertEqual(deserialized.params.spread, original.params.spread)
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