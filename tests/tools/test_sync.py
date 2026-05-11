"""Tests for tools/sync.py.

The script lives outside any package, so we load it via importlib. Tests
patch the module-level path constants to point at tmpdir fixtures, then
exercise each subcommand's logic.
"""
import contextlib
import importlib.util
import io
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock


# Load sync.py as a module
_SYNC_PATH = pathlib.Path(__file__).parent.parent.parent / "tools" / "sync.py"
_spec = importlib.util.spec_from_file_location("sync", _SYNC_PATH)
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)


class SyncTestBase(unittest.TestCase):
    """Patches LOCAL_ROOT / TEST_VOLUME to fresh tmpdirs for each test."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.local_root = self.tmpdir / "demos"
        self.test_volume = self.tmpdir / "virtual-m8"
        self.patches = [
            mock.patch.object(sync, "LOCAL_ROOT", self.local_root),
            mock.patch.object(sync, "TEST_VOLUME", self.test_volume),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def make_local_demo(self, category, flavor, *, m8s_name=None, wavs=()):
        """Create tmp/demos/<category>/<flavor>/<demo>.m8s and optional samples."""
        d = self.local_root / category / flavor
        d.mkdir(parents=True, exist_ok=True)
        (d / (m8s_name or f"{flavor}.m8s")).write_bytes(b"\x00" * 16)
        if wavs:
            samples = d / "samples"
            samples.mkdir()
            for w in wavs:
                (samples / w).write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        return d

    def make_remote_demo(self, name):
        d = self.test_volume / sync.REMOTE_SUBPATH / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.m8s").write_bytes(b"\x00")
        return d


class TestM8Name(unittest.TestCase):
    """Pure function — path → M8-friendly name."""

    def test_two_levels(self):
        with mock.patch.object(sync, "LOCAL_ROOT", pathlib.Path("tmp/demos")):
            self.assertEqual(
                sync.m8_name(pathlib.Path("tmp/demos/acid_303/sampler")),
                "acid-303-sampler",
            )

    def test_underscores_to_hyphens(self):
        with mock.patch.object(sync, "LOCAL_ROOT", pathlib.Path("tmp/demos")):
            self.assertEqual(
                sync.m8_name(pathlib.Path("tmp/demos/euclid/midi")),
                "euclid-midi",
            )


class TestFindLocal(SyncTestBase):
    def test_returns_empty_when_root_missing(self):
        self.assertEqual(sync.find_local(), [])

    def test_finds_demos_with_m8s(self):
        self.make_local_demo("acid_303", "sampler")
        self.make_local_demo("euclid", "midi")
        # An empty dir without .m8s should be skipped
        (self.local_root / "ignored" / "empty").mkdir(parents=True)

        result = sync.find_local()
        names = [sync.m8_name(d) for d in result]
        self.assertEqual(sorted(names), ["acid-303-sampler", "euclid-midi"])

    def test_pattern_filter(self):
        self.make_local_demo("acid_303", "sampler")
        self.make_local_demo("acid_303", "midi")
        self.make_local_demo("euclid", "midi")

        names = [sync.m8_name(d) for d in sync.find_local("acid-303")]
        self.assertEqual(sorted(names), ["acid-303-midi", "acid-303-sampler"])

        names = [sync.m8_name(d) for d in sync.find_local("midi")]
        self.assertEqual(sorted(names), ["acid-303-midi", "euclid-midi"])


class TestFindRemote(SyncTestBase):
    def test_returns_empty_when_remote_missing(self):
        self.assertEqual(sync.find_remote(test_mode=True), [])

    def test_finds_remote_demos(self):
        self.make_remote_demo("acid-303-sampler")
        self.make_remote_demo("euclid-midi")
        result = sync.find_remote(test_mode=True)
        names = sorted(d.name for d in result)
        self.assertEqual(names, ["acid-303-sampler", "euclid-midi"])

    def test_pattern_filter(self):
        self.make_remote_demo("acid-303-sampler")
        self.make_remote_demo("acid-303-midi")
        self.make_remote_demo("euclid-midi")
        names = sorted(d.name for d in sync.find_remote(test_mode=True, pattern="acid"))
        self.assertEqual(names, ["acid-303-midi", "acid-303-sampler"])


class TestPush(SyncTestBase):
    def test_copies_m8s_and_samples(self):
        self.make_local_demo("acid_303", "sampler", wavs=["kick.wav", "snare.wav"])

        with contextlib.redirect_stdout(io.StringIO()):
            sync.push(pattern=None, force=True, test_mode=True)

        target = self.test_volume / sync.REMOTE_SUBPATH / "acid-303-sampler"
        self.assertTrue(target.exists())
        self.assertTrue((target / "sampler.m8s").exists())
        self.assertTrue((target / "samples" / "kick.wav").exists())
        self.assertTrue((target / "samples" / "snare.wav").exists())

    def test_skips_existing(self):
        self.make_local_demo("acid_303", "sampler")
        # Pre-existing remote entry should not be overwritten
        existing = self.make_remote_demo("acid-303-sampler")
        sentinel = existing / "sentinel.txt"
        sentinel.write_text("preserved")

        with contextlib.redirect_stdout(io.StringIO()) as out:
            sync.push(pattern=None, force=True, test_mode=True)
        self.assertIn("already on device", out.getvalue())
        self.assertTrue(sentinel.exists(), "push must not clobber existing target")

    def test_pattern_filter(self):
        self.make_local_demo("acid_303", "sampler")
        self.make_local_demo("euclid", "midi")

        with contextlib.redirect_stdout(io.StringIO()):
            sync.push(pattern="euclid", force=True, test_mode=True)

        self.assertFalse((self.test_volume / sync.REMOTE_SUBPATH / "acid-303-sampler").exists())
        self.assertTrue((self.test_volume / sync.REMOTE_SUBPATH / "euclid-midi").exists())


class TestCleanLocal(SyncTestBase):
    def test_removes_matched_demo_and_empty_parent(self):
        self.make_local_demo("acid_303", "sampler")
        self.make_local_demo("euclid", "midi")

        with contextlib.redirect_stdout(io.StringIO()):
            sync.clean_local(pattern="acid", force=True)

        # acid_303/sampler removed; parent dir acid_303 cleaned up too
        self.assertFalse((self.local_root / "acid_303" / "sampler").exists())
        self.assertFalse((self.local_root / "acid_303").exists())
        # euclid/midi untouched
        self.assertTrue((self.local_root / "euclid" / "midi").exists())


class TestCleanRemote(SyncTestBase):
    def test_removes_matched_remote_demo(self):
        self.make_remote_demo("acid-303-sampler")
        self.make_remote_demo("euclid-midi")

        with contextlib.redirect_stdout(io.StringIO()):
            sync.clean_remote(pattern="acid", force=True, test_mode=True)

        self.assertFalse((self.test_volume / sync.REMOTE_SUBPATH / "acid-303-sampler").exists())
        self.assertTrue((self.test_volume / sync.REMOTE_SUBPATH / "euclid-midi").exists())


class TestStatus(SyncTestBase):
    def test_diff_math(self):
        """status() prints the three sets: in_sync, local-only, remote-only."""
        self.make_local_demo("acid_303", "sampler")    # local only
        self.make_local_demo("euclid", "midi")          # in sync
        self.make_remote_demo("euclid-midi")            # in sync
        self.make_remote_demo("chords-midi")            # remote only

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sync.status(test_mode=True)
        text = out.getvalue()

        self.assertIn("acid-303-sampler", text)
        self.assertIn("euclid-midi", text)
        self.assertIn("chords-midi", text)
        # Verify the diff categories
        in_sync_line = next(l for l in text.splitlines() if "in sync" in l)
        local_only_line = next(l for l in text.splitlines() if "local-only" in l)
        remote_only_line = next(l for l in text.splitlines() if "remote-only" in l)
        self.assertIn("euclid-midi", in_sync_line)
        self.assertIn("acid-303-sampler", local_only_line)
        self.assertIn("chords-midi", remote_only_line)


class TestConfirm(unittest.TestCase):
    def test_force_skips_prompt(self):
        self.assertTrue(sync.confirm("anything? ", force=True))

    def test_non_tty_auto_confirms(self):
        """Piped/non-interactive stdin should auto-confirm — no input() to call."""
        with mock.patch.object(sync.sys.stdin, "isatty", return_value=False), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(sync.confirm("ok? ", force=False))

    def test_tty_yes_response(self):
        with mock.patch.object(sync.sys.stdin, "isatty", return_value=True), \
             mock.patch("builtins.input", return_value="yes"):
            self.assertTrue(sync.confirm("ok? ", force=False))

    def test_tty_no_response(self):
        with mock.patch.object(sync.sys.stdin, "isatty", return_value=True), \
             mock.patch("builtins.input", return_value=""):
            self.assertFalse(sync.confirm("ok? ", force=False))


if __name__ == "__main__":
    unittest.main()
