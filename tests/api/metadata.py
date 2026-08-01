"""Tests for M8Metadata.

Metadata covers the contiguous 146-byte block at file offset 14:
directory + transpose + tempo + quantize + name. The musical `key`
byte lives at file offset 187 (after MidiSettings) and is exposed on
`M8Project` directly (`project.key`), not here.
"""
import struct
import unittest

from m8.api.metadata import M8Metadata, METADATA_BLOCK_SIZE


class TestM8MetadataBinary(unittest.TestCase):
    def _build_binary(self, directory, transpose, tempo, quantize, name):
        """Build a 146-byte metadata block by hand."""
        buf = bytearray()
        dir_bytes = directory.encode("utf-8")
        buf.extend(dir_bytes)
        buf.extend(bytes(128 - len(dir_bytes)))
        buf.append(transpose)
        buf.extend(struct.pack("<f", tempo))
        buf.append(quantize)
        name_bytes = name.encode("utf-8")
        buf.extend(name_bytes)
        buf.extend(bytes(12 - len(name_bytes)))
        assert len(buf) == METADATA_BLOCK_SIZE
        return buf

    def test_block_size_is_146(self):
        """directory(128) + transpose(1) + tempo(4) + quantize(1) + name(12)."""
        self.assertEqual(METADATA_BLOCK_SIZE, 146)
        self.assertEqual(M8Metadata.BLOCK_SIZE, 146)
        self.assertEqual(len(M8Metadata().write()), 146)

    def test_read_from_binary(self):
        data = self._build_binary("/Songs/", 2, 140.5, 4, "TEST SONG")
        m = M8Metadata.read(data)
        self.assertEqual(m.directory, "/Songs/")
        self.assertEqual(m.transpose, 2)
        self.assertAlmostEqual(m.tempo, 140.5, places=4)
        self.assertEqual(m.quantize, 4)
        self.assertEqual(m.name, "TEST SONG")

    def test_read_handles_null_terminated_strings(self):
        data = self._build_binary("/Songs", 0, 120.0, 0, "SHORT")
        m = M8Metadata.read(data)
        self.assertEqual(m.directory, "/Songs")
        self.assertEqual(m.name, "SHORT")

    def test_write_then_read_consistency(self):
        cases = [
            ("/Songs/", 0, 120.0, 0, "TEST1"),
            ("/Projects/MyProj/", 3, 145.75, 2, "COMPLEX"),
            ("/", 15, 60.0, 7, "MINIMAL"),
        ]
        for directory, transpose, tempo, quantize, name in cases:
            with self.subTest(name=name):
                original = M8Metadata(
                    directory=directory, transpose=transpose, tempo=tempo,
                    quantize=quantize, name=name,
                )
                reloaded = M8Metadata.read(original.write())
                self.assertEqual(reloaded.directory, original.directory)
                self.assertEqual(reloaded.transpose, original.transpose)
                self.assertAlmostEqual(reloaded.tempo, original.tempo, places=4)
                self.assertEqual(reloaded.quantize, original.quantize)
                self.assertEqual(reloaded.name, original.name)


class TestM8MetadataConstructor(unittest.TestCase):
    def test_defaults(self):
        m = M8Metadata()
        self.assertEqual(m.directory, "/Songs/")
        self.assertEqual(m.transpose, 0)
        self.assertEqual(m.tempo, 120.0)
        self.assertEqual(m.quantize, 0)
        self.assertEqual(m.name, "HELLO")

    def test_with_arguments(self):
        m = M8Metadata(
            directory="/Custom/", transpose=3, tempo=140.0,
            quantize=2, name="CUSTOM",
        )
        self.assertEqual(m.directory, "/Custom/")
        self.assertEqual(m.transpose, 3)
        self.assertEqual(m.tempo, 140.0)
        self.assertEqual(m.quantize, 2)
        self.assertEqual(m.name, "CUSTOM")

    def test_partial(self):
        m = M8Metadata(directory="/Partial/", name="PARTIAL")
        self.assertEqual(m.directory, "/Partial/")
        self.assertEqual(m.name, "PARTIAL")
        self.assertEqual(m.transpose, 0)
        self.assertEqual(m.tempo, 120.0)


class TestM8MetadataClone(unittest.TestCase):
    def test_clone_copies_all_fields(self):
        original = M8Metadata(
            directory="/Clone/", transpose=4, tempo=125.5,
            quantize=3, name="ORIGINAL",
        )
        cloned = original.clone()
        self.assertIsNot(cloned, original)
        self.assertEqual(cloned.directory, "/Clone/")
        self.assertEqual(cloned.transpose, 4)
        self.assertEqual(cloned.tempo, 125.5)
        self.assertEqual(cloned.name, "ORIGINAL")

    def test_clone_is_independent(self):
        original = M8Metadata(name="ORIGINAL")
        cloned = original.clone()
        cloned.name = "MODIFIED"
        self.assertEqual(original.name, "ORIGINAL")


class TestM8MetadataByteFidelity(unittest.TestCase):
    """A no-edit read().write() must reproduce the source bytes exactly,
    including stale bytes trailing a string's null terminator — real
    device files leave non-zero garbage there from a previously-longer
    path/name, and it must not be zeroed unless the field is reassigned."""

    DIRECTORY = "/Songs/short/"
    DIRECTORY_TERMINATOR = len(DIRECTORY)  # index of the directory field's null byte
    NAME = "SHORT"
    NAME_TERMINATOR = 134 + len(NAME)  # index (absolute) of the name field's null byte

    def _build_binary_with_stale_tail(self):
        buf = bytearray(METADATA_BLOCK_SIZE)
        buf[0:self.DIRECTORY_TERMINATOR] = self.DIRECTORY.encode("utf-8")
        buf[self.DIRECTORY_TERMINATOR] = 0
        # Stale non-zero bytes left over from a previously-longer path.
        gap = 128 - self.DIRECTORY_TERMINATOR - 1
        buf[self.DIRECTORY_TERMINATOR + 1:128] = bytes((i % 254) + 1 for i in range(gap))
        buf[128] = 5  # transpose
        buf[129:133] = struct.pack("<f", 128.0)  # tempo
        buf[133] = 2  # quantize
        buf[134:self.NAME_TERMINATOR] = self.NAME.encode("utf-8")
        buf[self.NAME_TERMINATOR] = 0
        buf[self.NAME_TERMINATOR + 1:146] = bytes([0xAB]) * (146 - self.NAME_TERMINATOR - 1)
        return bytes(buf)

    def test_unmodified_metadata_round_trips_byte_identically(self):
        original = self._build_binary_with_stale_tail()
        m = M8Metadata.read(original)
        self.assertEqual(m.write(), original)

    def test_reassigning_field_zero_pads_it(self):
        original = self._build_binary_with_stale_tail()
        m = M8Metadata.read(original)
        m.directory = self.DIRECTORY  # same string, but reassigned
        rewritten = m.write()

        self.assertNotEqual(rewritten, original)
        self.assertEqual(rewritten[self.DIRECTORY_TERMINATOR + 1:128], bytes(128 - self.DIRECTORY_TERMINATOR - 1))
        # Untouched fields (name) still preserve their stale tail.
        self.assertEqual(rewritten[134:146], original[134:146])


class TestKeyNotOnMetadata(unittest.TestCase):
    """The musical-key byte is on M8Project, not on M8Metadata."""

    def test_no_key_attribute(self):
        m = M8Metadata()
        self.assertFalse(hasattr(m, "key"))


if __name__ == "__main__":
    unittest.main()
