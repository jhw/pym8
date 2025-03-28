import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument, create_instrument
from m8.api.instruments.fmsynth import M8FMSynth
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8FMSynthParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor for FMSynth params
        params = M8InstrumentParams.from_config("FMSYNTH")
        
        # Check defaults for key parameters
        self.assertEqual(params.algo, 0x0)  # A_B_C_D
        self.assertEqual(params.shape1, 0x0)  # SIN
        self.assertEqual(params.ratio1, 0x0)
        self.assertEqual(params.level1, 0x0)
        self.assertEqual(params.feedback1, 0x0)
        self.assertEqual(params.filter, 0x0)
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
        params = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x06,  # TRI
            shape2=0x07,  # SAW
            shape3=0x08,  # SQR
            shape4=0x09,  # PUL
            ratio1=0x08,
            ratio2=0x04,
            ratio3=0x02,
            ratio4=0x01,
            level1=0xF0,
            level2=0xE0,
            level3=0xD0,
            level4=0xC0,
            feedback1=0x10,
            feedback2=0x20,
            feedback3=0x30,
            feedback4=0x40,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # FOLD
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Check values
        self.assertEqual(params.algo, 0x02)
        self.assertEqual(params.shape1, 0x06)
        self.assertEqual(params.ratio1, 0x08)
        self.assertEqual(params.level1, 0xF0)
        self.assertEqual(params.feedback1, 0x10)
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
        binary_data[18] = 0x02  # algo (offset 18)
        binary_data[19] = 0x06  # shape1 (offset 19)
        binary_data[23] = 0x08  # ratio1 (offset 23)
        binary_data[31] = 0xF0  # level1 (offset 31)
        binary_data[32] = 0x10  # feedback1 (offset 32)
        binary_data[51] = 0x02  # filter (offset 51)
        binary_data[52] = 0xE0  # cutoff (offset 52)
        binary_data[60] = 0x90  # reverb (offset 60)
        
        # Create params and read from binary
        params = M8InstrumentParams.from_config("FMSYNTH")
        params.read(binary_data)
        
        # Check key parameter values
        self.assertEqual(params.algo, 0x02)
        self.assertEqual(params.shape1, 0x06)
        self.assertEqual(params.ratio1, 0x08)
        self.assertEqual(params.level1, 0xF0)
        self.assertEqual(params.feedback1, 0x10)
        self.assertEqual(params.filter, 0x02)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.reverb, 0x90)
    
    def test_write_to_binary(self):
        # Create params with specific values
        params = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,
            shape1=0x06,
            ratio1=0x08,
            level1=0xF0,
            feedback1=0x10,
            filter=0x02,
            cutoff=0xE0,
            reverb=0x90
        )
        
        # Write to binary
        binary = params.write()
        
        # Check binary has sufficient size
        min_size = 61  # Should at least include up to reverb at offset 60
        self.assertGreaterEqual(len(binary), min_size)
        
        # Check key parameters
        self.assertEqual(binary[18], 0x02)  # algo
        self.assertEqual(binary[19], 0x06)  # shape1
        self.assertEqual(binary[23], 0x08)  # ratio1
        self.assertEqual(binary[31], 0xF0)  # level1
        self.assertEqual(binary[32], 0x10)  # feedback1
        self.assertEqual(binary[51], 0x02)  # filter
        self.assertEqual(binary[52], 0xE0)  # cutoff
        self.assertEqual(binary[60], 0x90)  # reverb
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,
            shape1=0x06,
            shape2=0x07,
            ratio1=0x08,
            ratio2=0x04,
            level1=0xF0,
            level2=0xE0,
            feedback1=0x10,
            feedback2=0x20,
            filter=0x02,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("FMSYNTH")
        deserialized.read(binary)
        
        # Check values match
        self.assertEqual(deserialized.algo, original.algo)
        self.assertEqual(deserialized.shape1, original.shape1)
        self.assertEqual(deserialized.ratio1, original.ratio1)
        self.assertEqual(deserialized.level1, original.level1)
        self.assertEqual(deserialized.feedback1, original.feedback1)
        self.assertEqual(deserialized.filter, original.filter)
        self.assertEqual(deserialized.cutoff, original.cutoff)
        self.assertEqual(deserialized.reverb, original.reverb)
    
    def test_as_dict(self):
        # Create params
        params = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x06,  # TRI
            ratio1=0x08,
            level1=0xF0,
            feedback1=0x10,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            limit=0x01,  # FOLD
            reverb=0x90
        )
        
        # Convert to dict
        result = params.as_dict()
        
        # Check non-enum values
        self.assertEqual(result["ratio1"], 0x08)
        self.assertEqual(result["level1"], 0xF0)
        self.assertEqual(result["feedback1"], 0x10)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["reverb"], 0x90)
        
        # Check enum values are strings
        self.assertIsInstance(result["algo"], str)
        self.assertIsInstance(result["shape1"], str)
        self.assertIsInstance(result["filter"], str)
        self.assertIsInstance(result["limit"], str)


class TestM8FMSynthInstrument(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8FMSynth()
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x04)  # FMSYNTH type_id is 4
        self.assertEqual(synth.instrument_type, "FMSYNTH")
        
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
        
        # Test with kwargs for both common and synth-specific parameters
        synth = M8FMSynth(
            # Common instrument parameters
            name="TestFMSynth",
            transpose=0x5,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            
            # FMSynth-specific parameters
            algo=0x02,  # A_B_PLUS_C_D = 0x02
            shape1=0x00,  # SIN = 0x00
            ratio1=8,
            level1=200,
            feedback1=30,
            cutoff=0xE0,
            pan=0x60
        )
        
        # Check common parameters
        self.assertEqual(synth.name, "TestFMSynth")
        self.assertEqual(synth.transpose, 0x5)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check FMSynth-specific parameters (just a sample)
        self.assertEqual(synth.params.algo, 0x02)  # A_B_PLUS_C_D = 0x02
        self.assertEqual(synth.params.shape1, 0x00)  # SIN = 0x00
        self.assertEqual(synth.params.ratio1, 8)
        self.assertEqual(synth.params.level1, 200)
        self.assertEqual(synth.params.feedback1, 30)
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.pan, 0x60)
    
    def test_from_dict(self):
        # Test creating from dict
        data = {
            "type": "FMSYNTH",
            "name": "TestFMSynth",
            "algo": 2,  # A_B_PLUS_C_D = 0x02
            "shape1": 0,  # SIN = 0x00
            "shape2": 6,  # TRI = 0x06
            "ratio1": 8,
            "level1": 200,
            "feedback1": 30,
        }
        
        # Create from dict
        synth = M8FMSynth.from_dict(data)
        
        # Check type
        self.assertEqual(synth.instrument_type, "FMSYNTH")
        self.assertEqual(synth.type, 0x04)
        
        # Check it's the right class
        self.assertIsInstance(synth, M8FMSynth)
        
        # Check parameters
        self.assertEqual(synth.name, "TestFMSynth")
        self.assertEqual(synth.params.algo, 0x02)
        self.assertEqual(synth.params.shape1, 0x00)
        self.assertEqual(synth.params.shape2, 0x06)
        self.assertEqual(synth.params.ratio1, 8)
        self.assertEqual(synth.params.level1, 200)
        self.assertEqual(synth.params.feedback1, 30)
    
    def test_read_parameters(self):
        # Create a FMSynth
        synth = M8FMSynth()
        
        # Create test binary data
        binary_data = bytearray([
            0x04,   # type (FMSynth)
            0x54, 0x45, 0x53, 0x54, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # name "TEST"
            0x42,   # transpose/eq (4/2)
            0x02,   # table_tick
            0x10,   # volume
            0x20,   # pitch
            0x90,   # finetune
            0x02,   # algo
            0x06,   # shape1
        ])
        
        # Add additional parameter bytes
        binary_data.extend([0] * (63 - len(binary_data)))  # Fill up to modulator offset
        binary_data.extend([0] * 24)  # Four empty modulators (6 bytes each)
        
        # Call the method to read parameters
        synth._read_parameters(binary_data)
        
        # Check common parameters
        self.assertEqual(synth.type, 0x04)
        self.assertEqual(synth.name, "TEST")
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check synth parameters
        self.assertEqual(synth.params.algo, 0x02)
        self.assertEqual(synth.params.shape1, 0x06)
    
    def test_as_dict(self):
        # Create a FMSynth with specific parameters
        synth = M8FMSynth(
            name="TestFMSynth",
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x00,  # SIN
            shape2=0x06,  # TRI
            ratio1=8,
            ratio2=4,
            level1=200,
            level2=150,
            feedback1=30,
            feedback2=20
        )
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "FMSYNTH")
        self.assertEqual(result["name"], "TestFMSynth")
        
        # Check synth-specific parameters (just a sample)
        self.assertEqual(result["algo"], "A_B_PLUS_C_D")
        self.assertEqual(result["shape1"], "SIN")
        self.assertEqual(result["shape2"], "TRI")
        self.assertEqual(result["ratio1"], 8)
        self.assertEqual(result["ratio2"], 4)
        self.assertEqual(result["level1"], 200)
        self.assertEqual(result["level2"], 150)
        self.assertEqual(result["feedback1"], 30)
        self.assertEqual(result["feedback2"], 20)
    
    def test_write(self):
        # Create a FMSynth with specific parameters
        synth = M8FMSynth(
            name="TEST",
            transpose=0x4,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x06,  # TRI
            ratio1=0x08,
            level1=0xF0,
            feedback1=0x10
        )
        
        # Call the method to write
        binary = synth.write()
        
        # Check the binary output
        self.assertEqual(len(binary), 215)  # Should be BLOCK_SIZE bytes
        
        # Check common parameters
        self.assertEqual(binary[0], 0x04)  # type
        self.assertEqual(binary[1:5], b"TEST")  # name (first 4 bytes)
        self.assertEqual(binary[13], 0x42)  # transpose/eq
        self.assertEqual(binary[14], 0x02)  # table_tick
        self.assertEqual(binary[15], 0x10)  # volume
        self.assertEqual(binary[16], 0x20)  # pitch
        self.assertEqual(binary[17], 0x90)  # finetune
        
        # Check synth-specific parameters
        self.assertEqual(binary[18], 0x02)  # algo
        self.assertEqual(binary[19], 0x06)  # shape1
        self.assertEqual(binary[23], 0x08)  # ratio1
        self.assertEqual(binary[31], 0xF0)  # level1
        self.assertEqual(binary[32], 0x10)  # feedback1
    
    def test_add_modulator(self):
        # Create a FMSynth
        synth = M8FMSynth()
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        slot = synth.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(synth.modulators[0].type, 3)  # LFO type value
        self.assertEqual(synth.modulators[0].destination, 2)  # PITCH value
        self.assertEqual(synth.modulators[0].amount, 100)
        self.assertEqual(synth.modulators[0].params.frequency, 50)
    
    def test_create_instrument_factory(self):
        # Test that the factory creates the right subclass
        synth = create_instrument("FMSYNTH")
        self.assertIsInstance(synth, M8FMSynth)
        
        # For dictionaries we need to use create_instrument_from_dict, not directly create_instrument
        from m8.api.instruments import create_instrument_from_dict
        
        # Test with dictionary data
        data = {
            "type": "FMSYNTH",
            "name": "TestFMSynth"
        }
        
        synth = create_instrument_from_dict(data)
        self.assertIsInstance(synth, M8FMSynth)
    
    def test_read_write_consistency(self):
        # Create original synth
        original = M8FMSynth(
            name="TestFMSynth",
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x06,  # TRI
            ratio1=0x08,
            level1=0xF0,
            feedback1=0x10
        )
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        original.add_modulator(mod)
        
        # Write to binary
        binary = original.write()
        
        # Create a new instance and read the binary
        deserialized = M8FMSynth()
        deserialized._read_parameters(binary)
        
        # Check values match
        self.assertEqual(deserialized.name, original.name)
        self.assertEqual(deserialized.params.algo, original.params.algo)
        self.assertEqual(deserialized.params.shape1, original.params.shape1)
        self.assertEqual(deserialized.params.ratio1, original.params.ratio1)
        self.assertEqual(deserialized.params.level1, original.params.level1)
        self.assertEqual(deserialized.params.feedback1, original.params.feedback1)
        
        # Check modulator
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)


if __name__ == '__main__':
    unittest.main()