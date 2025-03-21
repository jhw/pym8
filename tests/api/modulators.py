import unittest
from m8.api import M8Block
from m8.api.modulators import (
    M8ModulatorBase, M8Modulators, create_default_modulators,
    M8AHDEnvelope, M8ADSREnvelope, M8DrumEnvelope, M8LFO, 
    M8TriggerEnvelope, M8TrackingEnvelope,
    BLOCK_SIZE, BLOCK_COUNT, MODULATOR_TYPES
)

class TestM8ModulatorBase(unittest.TestCase):
    def setUp(self):
        # Create a minimal concrete modulator class for testing
        class TestModulator(M8ModulatorBase):
            TYPE_VALUE = 0xF  # Test type value
            
            DEFAULT_PARAM1 = 0x10
            DEFAULT_PARAM2 = 0x20
            DEFAULT_PARAM3 = 0x30
            
            _param_defs = [
                ("param1", DEFAULT_PARAM1),
                ("param2", DEFAULT_PARAM2),
                ("param3", DEFAULT_PARAM3)
            ]
            
            def _get_type(self):
                return self.TYPE_VALUE
        
        self.TestModulator = TestModulator
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        mod = self.TestModulator()
        
        # Check type is set correctly
        self.assertEqual(mod.type, 0xF)
        
        # Check default values
        self.assertEqual(mod.destination, M8ModulatorBase.DEFAULT_DESTINATION)
        self.assertEqual(mod.amount, M8ModulatorBase.DEFAULT_AMOUNT)
        self.assertEqual(mod.param1, 0x10)
        self.assertEqual(mod.param2, 0x20)
        self.assertEqual(mod.param3, 0x30)
        
        # Test with kwargs
        mod = self.TestModulator(
            destination=0x5,
            amount=0x80,
            param1=0x40,
            param2=0x50,
            param3=0x60
        )
        
        # Check values
        self.assertEqual(mod.destination, 0x5)
        self.assertEqual(mod.amount, 0x80)
        self.assertEqual(mod.param1, 0x40)
        self.assertEqual(mod.param2, 0x50)
        self.assertEqual(mod.param3, 0x60)
    
    def test_read_from_binary(self):
        # Create test binary data
        binary_data = bytearray([
            0xF5,  # type=0xF, destination=0x5 (combined byte)
            0x80,  # amount
            0x40,  # param1
            0x50,  # param2
            0x60,  # param3
            0x00   # padding
        ])
        
        # Read from binary
        mod = self.TestModulator.read(binary_data)
        
        # Check values
        self.assertEqual(mod.type, 0xF)
        self.assertEqual(mod.destination, 0x5)
        self.assertEqual(mod.amount, 0x80)
        self.assertEqual(mod.param1, 0x40)
        self.assertEqual(mod.param2, 0x50)
        self.assertEqual(mod.param3, 0x60)
        
        # Test with truncated data (should set defaults for missing values)
        binary_data = bytearray([
            0xF5,  # type=0xF, destination=0x5 (combined byte)
            0x80   # amount
            # Missing param values
        ])
        
        mod = self.TestModulator.read(binary_data)
        
        # Check that it read what was available and defaulted the rest
        self.assertEqual(mod.type, 0xF)
        self.assertEqual(mod.destination, 0x5)
        self.assertEqual(mod.amount, 0x80)
        # These should have default values
        self.assertEqual(mod.param1, 0x10)
        self.assertEqual(mod.param2, 0x20)
        self.assertEqual(mod.param3, 0x30)
    
    def test_write_to_binary(self):
        # Create modulator
        mod = self.TestModulator(
            destination=0x5,
            amount=0x80,
            param1=0x40,
            param2=0x50,
            param3=0x60
        )
        
        # Write to binary
        binary = mod.write()
        
        # Check binary output
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0xF5)  # type=0xF, destination=0x5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # param1
        self.assertEqual(binary[3], 0x50)  # param2
        self.assertEqual(binary[4], 0x60)  # param3
        self.assertEqual(binary[5], 0x00)  # padding
    
    def test_clone(self):
        # Create original modulator
        original = self.TestModulator(
            destination=0x5,
            amount=0x80,
            param1=0x40,
            param2=0x50,
            param3=0x60
        )
        
        # Clone
        clone = original.clone()
        
        # Check they are different objects
        self.assertIsNot(clone, original)
        
        # Check values match
        self.assertEqual(clone.type, original.type)
        self.assertEqual(clone.destination, original.destination)
        self.assertEqual(clone.amount, original.amount)
        self.assertEqual(clone.param1, original.param1)
        self.assertEqual(clone.param2, original.param2)
        self.assertEqual(clone.param3, original.param3)
        
        # Modify clone and check original unchanged
        clone.destination = 0x7
        clone.param1 = 0x70
        
        self.assertEqual(original.destination, 0x5)
        self.assertEqual(original.param1, 0x40)
    
    def test_is_empty(self):
        # Empty modulator (destination = 0)
        mod = self.TestModulator(destination=0)
        self.assertTrue(mod.is_empty())
        
        # Non-empty modulator
        mod = self.TestModulator(destination=1)
        self.assertFalse(mod.is_empty())
    
    def test_as_dict(self):
        # Create modulator
        mod = self.TestModulator(
            destination=0x5,
            amount=0x80,
            param1=0x40,
            param2=0x50,
            param3=0x60
        )
        
        # Convert to dict
        result = mod.as_dict()
        
        # Check dict
        expected = {
            "type": 0xF,
            "destination": 0x5,
            "amount": 0x80,
            "param1": 0x40,
            "param2": 0x50,
            "param3": 0x60
        }
        
        self.assertEqual(result, expected)
    
    def test_from_dict(self):
        # Test data
        data = {
            "type": 0xF,
            "destination": 0x5,
            "amount": 0x80,
            "param1": 0x40,
            "param2": 0x50,
            "param3": 0x60
        }
        
        # Create from dict
        mod = self.TestModulator.from_dict(data)
        
        # Check values
        self.assertEqual(mod.type, 0xF)
        self.assertEqual(mod.destination, 0x5)
        self.assertEqual(mod.amount, 0x80)
        self.assertEqual(mod.param1, 0x40)
        self.assertEqual(mod.param2, 0x50)
        self.assertEqual(mod.param3, 0x60)
        
        # Test with partial data
        data = {
            "destination": 0x7,
            "param1": 0x70
        }
        
        mod = self.TestModulator.from_dict(data)
        
        # Check provided values and defaults
        self.assertEqual(mod.destination, 0x7)
        self.assertEqual(mod.param1, 0x70)
        self.assertEqual(mod.amount, M8ModulatorBase.DEFAULT_AMOUNT)
        self.assertEqual(mod.param2, 0x20)
        self.assertEqual(mod.param3, 0x30)


class TestModulatorTypes(unittest.TestCase):
    """Test each specific modulator type."""
    
    def test_ahd_envelope(self):
        # Test AHD Envelope
        env = M8AHDEnvelope(
            destination=0x5,
            amount=0x80,
            attack=0x40,
            hold=0x50,
            decay=0x60
        )
        
        # Check type
        self.assertEqual(env.type, 0x0)
        
        # Check parameters
        self.assertEqual(env.destination, 0x5)
        self.assertEqual(env.amount, 0x80)
        self.assertEqual(env.attack, 0x40)
        self.assertEqual(env.hold, 0x50)
        self.assertEqual(env.decay, 0x60)
        
        # Test serialization
        binary = env.write()
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0x05)  # type=0, destination=5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # attack
        self.assertEqual(binary[3], 0x50)  # hold
        self.assertEqual(binary[4], 0x60)  # decay
        
        # Test deserialization
        env2 = M8AHDEnvelope.read(binary)
        self.assertEqual(env2.type, env.type)
        self.assertEqual(env2.destination, env.destination)
        self.assertEqual(env2.amount, env.amount)
        self.assertEqual(env2.attack, env.attack)
        self.assertEqual(env2.hold, env.hold)
        self.assertEqual(env2.decay, env.decay)
    
    def test_adsr_envelope(self):
        # Test ADSR Envelope
        env = M8ADSREnvelope(
            destination=0x5,
            amount=0x80,
            attack=0x40,
            decay=0x50,
            sustain=0x60,
            release=0x70
        )
        
        # Check type
        self.assertEqual(env.type, 0x1)
        
        # Check parameters
        self.assertEqual(env.destination, 0x5)
        self.assertEqual(env.amount, 0x80)
        self.assertEqual(env.attack, 0x40)
        self.assertEqual(env.decay, 0x50)
        self.assertEqual(env.sustain, 0x60)
        self.assertEqual(env.release, 0x70)
        
        # Test serialization
        binary = env.write()
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0x15)  # type=1, destination=5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # attack
        self.assertEqual(binary[3], 0x50)  # decay
        self.assertEqual(binary[4], 0x60)  # sustain
        self.assertEqual(binary[5], 0x70)  # release
    
    def test_drum_envelope(self):
        # Test Drum Envelope
        env = M8DrumEnvelope(
            destination=0x5,
            amount=0x80,
            peak=0x40,
            body=0x50,
            decay=0x60
        )
        
        # Check type
        self.assertEqual(env.type, 0x2)
        
        # Check parameters
        self.assertEqual(env.destination, 0x5)
        self.assertEqual(env.amount, 0x80)
        self.assertEqual(env.peak, 0x40)
        self.assertEqual(env.body, 0x50)
        self.assertEqual(env.decay, 0x60)
        
        # Test serialization
        binary = env.write()
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0x25)  # type=2, destination=5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # peak
        self.assertEqual(binary[3], 0x50)  # body
        self.assertEqual(binary[4], 0x60)  # decay
    
    def test_lfo(self):
        # Test LFO
        lfo = M8LFO(
            destination=0x5,
            amount=0x80,
            oscillator=0x40,
            trigger=0x50,
            frequency=0x60
        )
        
        # Check type
        self.assertEqual(lfo.type, 0x3)
        
        # Check parameters
        self.assertEqual(lfo.destination, 0x5)
        self.assertEqual(lfo.amount, 0x80)
        self.assertEqual(lfo.oscillator, 0x40)
        self.assertEqual(lfo.trigger, 0x50)
        self.assertEqual(lfo.frequency, 0x60)
        
        # Test serialization
        binary = lfo.write()
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0x35)  # type=3, destination=5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # oscillator
        self.assertEqual(binary[3], 0x50)  # trigger
        self.assertEqual(binary[4], 0x60)  # frequency
    
    def test_trigger_envelope(self):
        # Test Trigger Envelope
        env = M8TriggerEnvelope(
            destination=0x5,
            amount=0x80,
            attack=0x40,
            hold=0x50,
            decay=0x60,
            source=0x70
        )
        
        # Check type
        self.assertEqual(env.type, 0x4)
        
        # Check parameters
        self.assertEqual(env.destination, 0x5)
        self.assertEqual(env.amount, 0x80)
        self.assertEqual(env.attack, 0x40)
        self.assertEqual(env.hold, 0x50)
        self.assertEqual(env.decay, 0x60)
        self.assertEqual(env.source, 0x70)
        
        # Test serialization
        binary = env.write()
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0x45)  # type=4, destination=5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # attack
        self.assertEqual(binary[3], 0x50)  # hold
        self.assertEqual(binary[4], 0x60)  # decay
        self.assertEqual(binary[5], 0x70)  # source
    
    def test_tracking_envelope(self):
        # Test Tracking Envelope
        env = M8TrackingEnvelope(
            destination=0x5,
            amount=0x80,
            source=0x40,
            low_value=0x50,
            high_value=0x60
        )
        
        # Check type
        self.assertEqual(env.type, 0x5)
        
        # Check parameters
        self.assertEqual(env.destination, 0x5)
        self.assertEqual(env.amount, 0x80)
        self.assertEqual(env.source, 0x40)
        self.assertEqual(env.low_value, 0x50)
        self.assertEqual(env.high_value, 0x60)
        
        # Test serialization
        binary = env.write()
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary[0], 0x55)  # type=5, destination=5
        self.assertEqual(binary[1], 0x80)  # amount
        self.assertEqual(binary[2], 0x40)  # source
        self.assertEqual(binary[3], 0x50)  # low_value
        self.assertEqual(binary[4], 0x60)  # high_value


class TestM8Modulators(unittest.TestCase):
    def test_constructor(self):
        # Test default constructor
        modulators = M8Modulators()
        
        # Should have BLOCK_COUNT modulators
        self.assertEqual(len(modulators), BLOCK_COUNT)
        
        # All modulators should be M8Block instances (empty slots)
        for mod in modulators:
            self.assertIsInstance(mod, M8Block)
        
        # Test with items
        item1 = M8LFO(destination=1, amount=100)
        item2 = M8AHDEnvelope(destination=2, amount=110)
        
        modulators = M8Modulators(items=[item1, item2])
        
        # Should still have BLOCK_COUNT modulators
        self.assertEqual(len(modulators), BLOCK_COUNT)
        
        # First two should be our custom modulators
        self.assertIs(modulators[0], item1)
        self.assertIs(modulators[1], item2)
        
        # Rest should be M8Block instances
        for i in range(2, BLOCK_COUNT):
            self.assertIsInstance(modulators[i], M8Block)
    
    def test_read_from_binary(self):
        # Create test binary data
        test_data = bytearray()
        
        # Modulator 0: LFO (type 0x3)
        mod0_data = bytearray([
            0x31,  # type=3 (LFO), destination=1
            0x64,  # amount=100
            0x10,  # oscillator
            0x20,  # trigger
            0x30,  # frequency
            0x00   # padding
        ])
        test_data.extend(mod0_data)
        
        # Modulator 1: AHD Envelope (type 0x0)
        mod1_data = bytearray([
            0x02,  # type=0 (AHD), destination=2
            0x6E,  # amount=110
            0x40,  # attack
            0x50,  # hold
            0x60,  # decay
            0x00   # padding
        ])
        test_data.extend(mod1_data)
        
        # Fill remaining slots with empty data
        for _ in range(BLOCK_COUNT - 2):
            test_data.extend([0] * BLOCK_SIZE)
        
        # Read modulators
        modulators = M8Modulators.read(test_data)
        
        # Check count
        self.assertEqual(len(modulators), BLOCK_COUNT)
        
        # Check modulator 0 (LFO)
        self.assertIsInstance(modulators[0], M8LFO)
        self.assertEqual(modulators[0].type, 0x3)
        self.assertEqual(modulators[0].destination, 0x1)
        self.assertEqual(modulators[0].amount, 0x64)
        self.assertEqual(modulators[0].oscillator, 0x10)
        self.assertEqual(modulators[0].trigger, 0x20)
        self.assertEqual(modulators[0].frequency, 0x30)
        
        # Check modulator 1 (AHD Envelope)
        self.assertIsInstance(modulators[1], M8AHDEnvelope)
        self.assertEqual(modulators[1].type, 0x0)
        self.assertEqual(modulators[1].destination, 0x2)
        self.assertEqual(modulators[1].amount, 0x6E)
        self.assertEqual(modulators[1].attack, 0x40)
        self.assertEqual(modulators[1].hold, 0x50)
        self.assertEqual(modulators[1].decay, 0x60)
        
        # Check that remaining slots have empty destinations
        for i in range(2, BLOCK_COUNT):
            # They might not be M8Block instances but should have empty destinations
            self.assertTrue(hasattr(modulators[i], 'is_empty') and modulators[i].is_empty())
    
    def test_write_to_binary(self):
        # Create modulators
        modulators = M8Modulators()
        
        # Set up two modulators
        modulators[0] = M8LFO(
            destination=0x1,
            amount=0x64,
            oscillator=0x10,
            trigger=0x20,
            frequency=0x30
        )
        
        modulators[1] = M8AHDEnvelope(
            destination=0x2,
            amount=0x6E,
            attack=0x40,
            hold=0x50,
            decay=0x60
        )
        
        # Write to binary
        binary = modulators.write()
        
        # Check size
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)
        
        # Check modulator 0 (LFO)
        self.assertEqual(binary[0], 0x31)  # type=3, destination=1
        self.assertEqual(binary[1], 0x64)  # amount
        self.assertEqual(binary[2], 0x10)  # oscillator
        self.assertEqual(binary[3], 0x20)  # trigger
        self.assertEqual(binary[4], 0x30)  # frequency
        
        # Check modulator 1 (AHD Envelope)
        offset = BLOCK_SIZE
        self.assertEqual(binary[offset + 0], 0x02)  # type=0, destination=2
        self.assertEqual(binary[offset + 1], 0x6E)  # amount
        self.assertEqual(binary[offset + 2], 0x40)  # attack
        self.assertEqual(binary[offset + 3], 0x50)  # hold
        self.assertEqual(binary[offset + 4], 0x60)  # decay
    
    def test_clone(self):
        # Create original modulators
        original = M8Modulators()
        original[0] = M8LFO(destination=0x1, amount=0x64)
        original[1] = M8AHDEnvelope(destination=0x2, amount=0x6E)
        
        # Clone
        clone = original.clone()
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Check modulator values match
        self.assertEqual(clone[0].type, original[0].type)
        self.assertEqual(clone[0].destination, original[0].destination)
        self.assertEqual(clone[0].amount, original[0].amount)
        
        self.assertEqual(clone[1].type, original[1].type)
        self.assertEqual(clone[1].destination, original[1].destination)
        self.assertEqual(clone[1].amount, original[1].amount)
        
        # Modify clone and verify original unchanged
        clone[0].destination = 0x3
        self.assertEqual(original[0].destination, 0x1)
    
    def test_as_list(self):
        # Create modulators
        modulators = M8Modulators()
        modulators[0] = M8LFO(destination=0x1, amount=0x64)
        modulators[1] = M8AHDEnvelope(destination=0x2, amount=0x6E)
        
        # Convert to list
        result = modulators.as_list()
        
        # Should only include non-empty modulators
        self.assertEqual(len(result), 2)
        
        # Check specific modulators
        mod0 = next(m for m in result if m["index"] == 0)
        self.assertEqual(mod0["type"], 0x3)  # LFO type
        self.assertEqual(mod0["destination"], 0x1)
        self.assertEqual(mod0["amount"], 0x64)
        
        mod1 = next(m for m in result if m["index"] == 1)
        self.assertEqual(mod1["type"], 0x0)  # AHD Envelope type
        self.assertEqual(mod1["destination"], 0x2)
        self.assertEqual(mod1["amount"], 0x6E)
    
    def test_from_list(self):
        # Test data
        data = [
            {
                "index": 0,
                "type": 0x3,  # LFO
                "destination": 0x1,
                "amount": 0x64,
                "oscillator": 0x10,
                "trigger": 0x20,
                "frequency": 0x30
            },
            {
                "index": 1,
                "type": 0x0,  # AHD Envelope
                "destination": 0x2,
                "amount": 0x6E,
                "attack": 0x40,
                "hold": 0x50,
                "decay": 0x60
            }
        ]
        
        # Create from list
        modulators = M8Modulators.from_list(data)
        
        # Check count
        self.assertEqual(len(modulators), BLOCK_COUNT)
        
        # Check specific modulators
        self.assertIsInstance(modulators[0], M8LFO)
        self.assertEqual(modulators[0].type, 0x3)
        self.assertEqual(modulators[0].destination, 0x1)
        self.assertEqual(modulators[0].amount, 0x64)
        self.assertEqual(modulators[0].oscillator, 0x10)
        self.assertEqual(modulators[0].trigger, 0x20)
        self.assertEqual(modulators[0].frequency, 0x30)
        
        self.assertIsInstance(modulators[1], M8AHDEnvelope)
        self.assertEqual(modulators[1].type, 0x0)
        self.assertEqual(modulators[1].destination, 0x2)
        self.assertEqual(modulators[1].amount, 0x6E)
        self.assertEqual(modulators[1].attack, 0x40)
        self.assertEqual(modulators[1].hold, 0x50)
        self.assertEqual(modulators[1].decay, 0x60)
        
        # Test with invalid index
        data = [
            {
                "index": BLOCK_COUNT + 5,  # Out of range
                "type": 0x3,
                "destination": 0x1,
                "amount": 0x64
            }
        ]
        
        modulators = M8Modulators.from_list(data)
        # All slots should be empty
        for mod in modulators:
            self.assertIsInstance(mod, M8Block)
        
        # Test with empty list
        modulators = M8Modulators.from_list([])
        # All slots should be empty
        for mod in modulators:
            self.assertIsInstance(mod, M8Block)


class TestHelperFunctions(unittest.TestCase):
    def test_create_default_modulators(self):
        # Test the create_default_modulators function
        modulators = create_default_modulators()
        
        # Should have exactly BLOCK_COUNT items (default 4)
        self.assertEqual(len(modulators), BLOCK_COUNT)
        
        # Check the default config (2 AHD envelopes, 2 LFOs)
        self.assertIsInstance(modulators[0], M8AHDEnvelope)
        self.assertIsInstance(modulators[1], M8AHDEnvelope)
        self.assertIsInstance(modulators[2], M8LFO)
        self.assertIsInstance(modulators[3], M8LFO)
        
        # All should have empty destinations
        for mod in modulators:
            self.assertEqual(mod.destination, 0)


if __name__ == '__main__':
    unittest.main()