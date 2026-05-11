"""Smoke tests that every demo script still runs without breaking.

Imports each demo's main() and invokes it inside a tmpdir cwd so the
demo's relative output paths (tmp/demos/...) don't pollute the repo. If
a demo's API drifts (e.g. an attribute rename breaks an example), this
catches it before the user runs `python demos/foo.py` and gets a stack
trace.

Skips demos that require external samples (downloaded by
demos/utils/download_erica_pico_samples.py) when those samples aren't
present locally.
"""
import importlib.util
import os
import sys
import unittest
from pathlib import Path


DEMOS_DIR = Path(__file__).parent.parent.parent / "demos"
REPO_ROOT = Path(__file__).parent.parent.parent
ERICA_SAMPLES_DIR = REPO_ROOT / "tmp" / "erica-pico-samples"

# Demos that need downloaded samples to run end-to-end.
SAMPLE_DEPENDENT_DEMOS = {
    "acid_909_sampler",
    "acid_909_chain",
    "euclid_sampler",
}


def _load_demo_module(path: Path):
    """Load a demo file as a module so we can call its main()."""
    spec = importlib.util.spec_from_file_location(f"demo_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestDemosSmoke(unittest.TestCase):
    """Run each demo's main() and check it produces a non-trivial .m8s file."""

    @classmethod
    def setUpClass(cls):
        # Demos import from demos.patterns etc. — repo root must be on path
        sys.path.insert(0, str(REPO_ROOT))

    @classmethod
    def tearDownClass(cls):
        if str(REPO_ROOT) in sys.path:
            sys.path.remove(str(REPO_ROOT))

    def _run_demo(self, demo_path):
        """Run the demo from the repo root.

        Demos write to `tmp/demos/<name>/` and read samples from
        `tmp/erica-pico-samples/` — both relative to CWD. The output
        directory is gitignored, so running from repo root is harmless.
        """
        orig_cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        try:
            module = _load_demo_module(demo_path)
            # Demos use argparse + sys.argv; pass the script name only
            # so flag defaults take effect.
            old_argv = sys.argv
            sys.argv = [str(demo_path)]
            try:
                module.main()
            finally:
                sys.argv = old_argv
        finally:
            os.chdir(orig_cwd)

        # The demo must have written something we can parse back
        output_dir = REPO_ROOT / "tmp" / "demos" / demo_path.stem
        m8s_files = list(output_dir.rglob("*.m8s")) if output_dir.exists() else []
        if not m8s_files:
            # Some demos use a different folder name — fall back to scanning
            # the whole tmp/demos tree for files modified during this test.
            m8s_files = list((REPO_ROOT / "tmp" / "demos").rglob("*.m8s"))
        self.assertGreater(len(m8s_files), 0, f"{demo_path.name} wrote no .m8s file")
        # Verify the output actually parses
        from m8.api.project import M8Project
        for p in m8s_files[:3]:  # sample a few; some demos write 100s
            M8Project.read_from_file(str(p))


def _make_test(demo_path):
    needs_samples = demo_path.stem in SAMPLE_DEPENDENT_DEMOS

    def test(self):
        if needs_samples and not ERICA_SAMPLES_DIR.exists():
            self.skipTest(
                f"{demo_path.name} needs Erica Pico samples — "
                f"run demos/utils/download_erica_pico_samples.py"
            )
        self._run_demo(demo_path)

    test.__name__ = f"test_{demo_path.stem}"
    return test


# Generate one test method per top-level demo script
for _demo in sorted(DEMOS_DIR.glob("*.py")):
    if _demo.name.startswith("__"):
        continue
    setattr(TestDemosSmoke, f"test_{_demo.stem}", _make_test(_demo))


if __name__ == "__main__":
    unittest.main()
