# tests/api/chain.py
import unittest
from m8.api.chain import (
    M8ChainStep, M8Chain, M8Chains,
    STEP_BLOCK_SIZE, STEP_COUNT, CHAIN_COUNT, CHAIN_BLOCK_SIZE,
    EMPTY_PHRASE, DEFAULT_TRANSPOSE
)


class TestM8ChainStep(unittest.TestCase):
    """Tests for M8ChainStep class."""

    def test_constructor_defaults(self):
        """Test default constructor creates empty step."""
        step = M8ChainStep()
        self.assertEqual(step.phrase, EMPTY_PHRASE)
        self.assertEqual(step.transpose, DEFAULT_TRANSPOSE)

    def test_constructor_with_values(self):
        """Test constructor with explicit values."""
        step = M8ChainStep(phrase=0x10, transpose=0x0C)
        self.assertEqual(step.phrase, 0x10)
        self.assertEqual(step.transpose, 0x0C)

    def test_phrase_property(self):
        """Test phrase getter and setter."""
        step = M8ChainStep()

        step.phrase = 0x42
        self.assertEqual(step.phrase, 0x42)

        step.phrase = 0x00
        self.assertEqual(step.phrase, 0x00)

        step.phrase = EMPTY_PHRASE
        self.assertEqual(step.phrase, EMPTY_PHRASE)

    def test_transpose_property(self):
        """Test transpose getter and setter."""
        step = M8ChainStep()

        # Positive transpose (up 12 semitones)
        step.transpose = 0x0C
        self.assertEqual(step.transpose, 0x0C)

        # Negative transpose (down 12 semitones as two's complement)
        step.transpose = 0xF4
        self.assertEqual(step.transpose, 0xF4)

        # No transpose
        step.transpose = 0x00
        self.assertEqual(step.transpose, 0x00)

    def test_read_from_binary(self):
        """Test reading step from binary data."""
        test_data = bytes([0x05, 0x0C])  # phrase=5, transpose=12
        step = M8ChainStep.read(test_data)

        self.assertEqual(step.phrase, 0x05)
        self.assertEqual(step.transpose, 0x0C)

    def test_read_empty_step(self):
        """Test reading empty step from binary."""
        test_data = bytes([EMPTY_PHRASE, DEFAULT_TRANSPOSE])
        step = M8ChainStep.read(test_data)

        self.assertEqual(step.phrase, EMPTY_PHRASE)
        self.assertEqual(step.transpose, DEFAULT_TRANSPOSE)

    def test_write_to_binary(self):
        """Test writing step to binary data."""
        step = M8ChainStep(phrase=0x10, transpose=0x05)
        binary = step.write()

        self.assertEqual(len(binary), STEP_BLOCK_SIZE)
        self.assertEqual(binary[0], 0x10)
        self.assertEqual(binary[1], 0x05)

    def test_write_empty_step(self):
        """Test writing empty step to binary."""
        step = M8ChainStep()
        binary = step.write()

        expected = bytes([EMPTY_PHRASE, DEFAULT_TRANSPOSE])
        self.assertEqual(binary, expected)

    def test_read_write_consistency(self):
        """Test binary serialization roundtrip."""
        test_cases = [
            bytes([0x00, 0x00]),  # phrase 0, no transpose
            bytes([0x10, 0x0C]),  # phrase 16, up 12 semitones
            bytes([0x7F, 0xF4]),  # phrase 127, down 12 semitones
            bytes([EMPTY_PHRASE, DEFAULT_TRANSPOSE]),  # empty step
        ]

        for test_data in test_cases:
            original = M8ChainStep.read(test_data)
            binary = original.write()
            deserialized = M8ChainStep.read(binary)

            self.assertEqual(deserialized.phrase, original.phrase)
            self.assertEqual(deserialized.transpose, original.transpose)

    def test_clone(self):
        """Test clone creates independent copy."""
        original = M8ChainStep(phrase=0x10, transpose=0x05)
        clone = original.clone()

        # Values match
        self.assertEqual(clone.phrase, original.phrase)
        self.assertEqual(clone.transpose, original.transpose)

        # Different objects
        self.assertIsNot(clone, original)

        # Modifications don't affect original
        clone.phrase = 0x20
        self.assertEqual(original.phrase, 0x10)


class TestM8Chain(unittest.TestCase):
    """Tests for M8Chain class."""

    def test_constructor_creates_empty_chain(self):
        """Test default constructor creates chain with 16 empty steps."""
        chain = M8Chain()

        self.assertEqual(len(chain), STEP_COUNT)
        for step in chain:
            self.assertEqual(step.phrase, EMPTY_PHRASE)
            self.assertEqual(step.transpose, DEFAULT_TRANSPOSE)

    def test_index_access(self):
        """Test list-style index access."""
        chain = M8Chain()

        # Set values
        chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
        chain[5] = M8ChainStep(phrase=0x05, transpose=0x0C)
        chain[15] = M8ChainStep(phrase=0x0F, transpose=0xF4)

        # Get values
        self.assertEqual(chain[0].phrase, 0x00)
        self.assertEqual(chain[5].phrase, 0x05)
        self.assertEqual(chain[5].transpose, 0x0C)
        self.assertEqual(chain[15].phrase, 0x0F)

    def test_read_from_binary(self):
        """Test reading chain from binary data."""
        # Create test data: 16 steps of 2 bytes each
        test_data = bytearray()
        for i in range(STEP_COUNT):
            test_data.extend([i, i * 2])  # phrase=i, transpose=i*2

        chain = M8Chain.read(test_data)

        self.assertEqual(len(chain), STEP_COUNT)
        for i in range(STEP_COUNT):
            self.assertEqual(chain[i].phrase, i)
            self.assertEqual(chain[i].transpose, i * 2)

    def test_write_to_binary(self):
        """Test writing chain to binary data."""
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=0x01, transpose=0x02)
        chain[5] = M8ChainStep(phrase=0x10, transpose=0x0C)

        binary = chain.write()

        # Should be STEP_COUNT * STEP_BLOCK_SIZE bytes
        self.assertEqual(len(binary), CHAIN_BLOCK_SIZE)

        # Check step 0
        self.assertEqual(binary[0], 0x01)
        self.assertEqual(binary[1], 0x02)

        # Check step 5
        self.assertEqual(binary[10], 0x10)  # offset 5 * 2
        self.assertEqual(binary[11], 0x0C)

    def test_read_write_consistency(self):
        """Test binary serialization roundtrip."""
        original = M8Chain()
        original[0] = M8ChainStep(phrase=0x00, transpose=0x00)
        original[3] = M8ChainStep(phrase=0x10, transpose=0x0C)
        original[7] = M8ChainStep(phrase=0x20, transpose=0xF4)
        original[15] = M8ChainStep(phrase=0x30, transpose=0x06)

        binary = original.write()
        deserialized = M8Chain.read(binary)

        for i in range(STEP_COUNT):
            self.assertEqual(deserialized[i].phrase, original[i].phrase)
            self.assertEqual(deserialized[i].transpose, original[i].transpose)

    def test_clone(self):
        """Test clone creates independent deep copy."""
        original = M8Chain()
        original[0] = M8ChainStep(phrase=0x10, transpose=0x05)
        original[5] = M8ChainStep(phrase=0x20, transpose=0x0C)

        clone = original.clone()

        # Values match
        for i in range(STEP_COUNT):
            self.assertEqual(clone[i].phrase, original[i].phrase)
            self.assertEqual(clone[i].transpose, original[i].transpose)

        # Different objects
        self.assertIsNot(clone, original)
        self.assertIsNot(clone[0], original[0])

        # Modifications don't affect original
        clone[0].phrase = 0x99
        self.assertEqual(original[0].phrase, 0x10)


class TestM8Chains(unittest.TestCase):
    """Tests for M8Chains collection class."""

    def test_constructor_creates_empty_collection(self):
        """Default constructor creates 255 empty chains (matches file format)."""
        chains = M8Chains()

        self.assertEqual(len(chains), CHAIN_COUNT)
        for chain in chains:
            self.assertIsInstance(chain, M8Chain)
            # Each chain should have 16 empty steps
            self.assertEqual(len(chain), STEP_COUNT)

    def test_chain_count_matches_file_format(self):
        """CHAIN_COUNT must be 255 to fully cover the file's chain region
        (CHAINS_OFFSET .. TABLE_OFFSET = 8160 bytes / 32 bytes per chain).

        pym8 used to have this at 128 — half the file capacity. Chains
        128..254 were silently inaccessible from Python; song matrix
        cells referencing them would be valid bytes but unreachable.
        """
        from m8.api.chain import CHAINS_OFFSET, CHAIN_BLOCK_SIZE
        from m8.api.table import TABLE_OFFSET
        self.assertEqual(CHAIN_COUNT, 255)
        self.assertEqual(CHAIN_COUNT * CHAIN_BLOCK_SIZE, TABLE_OFFSET - CHAINS_OFFSET)

    def test_high_chain_index_accessible(self):
        """A chain beyond the old 128 limit must be addressable and round-trip."""
        from m8.api.project import M8Project
        p = M8Project.initialise()
        p.chains[200][0].phrase = 99
        reloaded = M8Project.read(p.write())
        self.assertEqual(reloaded.chains[200][0].phrase, 99)

    def test_index_access(self):
        """Test list-style index access for chains."""
        chains = M8Chains()

        # Set chain 0 with some data
        chains[0][0] = M8ChainStep(phrase=0x01, transpose=0x00)
        chains[0][1] = M8ChainStep(phrase=0x02, transpose=0x00)

        # Set chain 50
        chains[50][0] = M8ChainStep(phrase=0x10, transpose=0x0C)

        # Verify
        self.assertEqual(chains[0][0].phrase, 0x01)
        self.assertEqual(chains[0][1].phrase, 0x02)
        self.assertEqual(chains[50][0].phrase, 0x10)
        self.assertEqual(chains[50][0].transpose, 0x0C)

    def test_read_from_binary(self):
        """Test reading chains collection from binary data."""
        # Create test data: CHAIN_COUNT chains
        test_data = bytearray()
        for chain_idx in range(CHAIN_COUNT):
            for step_idx in range(STEP_COUNT):
                # Simple pattern: phrase = chain_idx, transpose = step_idx
                test_data.extend([chain_idx & 0xFF, step_idx])

        chains = M8Chains.read(test_data)

        self.assertEqual(len(chains), CHAIN_COUNT)

        # Verify a few chains
        self.assertEqual(chains[0][0].phrase, 0)
        self.assertEqual(chains[0][0].transpose, 0)
        self.assertEqual(chains[10][5].phrase, 10)
        self.assertEqual(chains[10][5].transpose, 5)
        self.assertEqual(chains[127][15].phrase, 127)
        self.assertEqual(chains[127][15].transpose, 15)

    def test_write_to_binary(self):
        """Test writing chains collection to binary data."""
        chains = M8Chains()
        chains[0][0] = M8ChainStep(phrase=0x01, transpose=0x00)
        chains[10][5] = M8ChainStep(phrase=0x10, transpose=0x0C)

        binary = chains.write()

        # Total size should be CHAIN_COUNT * CHAIN_BLOCK_SIZE
        expected_size = CHAIN_COUNT * CHAIN_BLOCK_SIZE
        self.assertEqual(len(binary), expected_size)

        # Verify chain 0, step 0
        self.assertEqual(binary[0], 0x01)
        self.assertEqual(binary[1], 0x00)

        # Verify chain 10, step 5 (offset: 10 * 32 + 5 * 2 = 330)
        offset = 10 * CHAIN_BLOCK_SIZE + 5 * STEP_BLOCK_SIZE
        self.assertEqual(binary[offset], 0x10)
        self.assertEqual(binary[offset + 1], 0x0C)

    def test_read_write_consistency(self):
        """Test binary serialization roundtrip."""
        original = M8Chains()
        original[0][0] = M8ChainStep(phrase=0x01, transpose=0x02)
        original[5][3] = M8ChainStep(phrase=0x10, transpose=0x0C)
        original[127][15] = M8ChainStep(phrase=0x7F, transpose=0xF4)

        binary = original.write()
        deserialized = M8Chains.read(binary)

        for chain_idx in range(CHAIN_COUNT):
            for step_idx in range(STEP_COUNT):
                self.assertEqual(
                    deserialized[chain_idx][step_idx].phrase,
                    original[chain_idx][step_idx].phrase
                )
                self.assertEqual(
                    deserialized[chain_idx][step_idx].transpose,
                    original[chain_idx][step_idx].transpose
                )

    def test_clone(self):
        """Test clone creates independent deep copy."""
        original = M8Chains()
        original[0][0] = M8ChainStep(phrase=0x10, transpose=0x05)
        original[50][10] = M8ChainStep(phrase=0x20, transpose=0x0C)

        clone = original.clone()

        # Values match
        self.assertEqual(clone[0][0].phrase, original[0][0].phrase)
        self.assertEqual(clone[50][10].phrase, original[50][10].phrase)

        # Different objects
        self.assertIsNot(clone, original)
        self.assertIsNot(clone[0], original[0])
        self.assertIsNot(clone[0][0], original[0][0])

        # Modifications don't affect original
        clone[0][0].phrase = 0x99
        self.assertEqual(original[0][0].phrase, 0x10)


class TestChainStepBoundaries(unittest.TestCase):
    """Edge values for chain step fields."""

    def test_empty_phrase_reference(self):
        step = M8ChainStep()
        self.assertEqual(step.phrase, 255)  # EMPTY_PHRASE

    def test_max_phrase_reference(self):
        step = M8ChainStep(phrase=254, transpose=0)
        self.assertEqual(step.phrase, 254)

    def test_transpose_boundary_values(self):
        """Transpose is 8-bit: 0..127 positive, 128..255 two's-complement-style."""
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=0, transpose=127)
        self.assertEqual(chain[0].transpose, 127)
        chain[1] = M8ChainStep(phrase=0, transpose=128)
        self.assertEqual(chain[1].transpose, 128)


class TestChainValidation(unittest.TestCase):
    """Validation rules on chain step / chain / chains."""

    def test_chain_step_valid(self):
        M8ChainStep(phrase=0, transpose=0).validate()  # no raise

    def test_chain_step_empty_phrase(self):
        M8ChainStep(phrase=255, transpose=0).validate()  # no raise

    def test_chain_step_max_phrase(self):
        M8ChainStep(phrase=254, transpose=0).validate()  # no raise

    def test_chain_valid(self):
        M8Chain().validate()  # no raise

    def test_chain_wrong_step_count(self):
        chain = M8Chain()
        chain.append(M8ChainStep())  # one extra
        with self.assertRaises(ValueError) as ctx:
            chain.validate()
        self.assertIn("steps", str(ctx.exception))

    def test_chains_valid(self):
        M8Chains().validate()  # no raise

    def test_chains_too_many(self):
        chains = M8Chains()
        chains.append(M8Chain())  # one over the limit
        with self.assertRaises(ValueError) as ctx:
            chains.validate()
        self.assertIn("Too many chains", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
