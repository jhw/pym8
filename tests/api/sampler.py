"""Sampler-specific tests. Cross-cutting behaviour lives in instruments.py."""
import unittest

from m8.api.instruments.sampler import M8Sampler, M8PlayMode


class TestM8SamplerSpecifics(unittest.TestCase):
    def test_sample_path_field(self):
        s = M8Sampler(name="K", sample_path="/samples/kick.wav")
        self.assertEqual(s.sample_path, "/samples/kick.wav")

        s.sample_path = "/samples/snare.wav"
        round_tripped = M8Sampler.read(s.write())
        self.assertEqual(round_tripped.sample_path, "/samples/snare.wav")

    def test_sample_path_in_dict(self):
        s = M8Sampler(name="S", sample_path="/foo.wav")
        params = s.to_dict()
        self.assertEqual(params["params"]["sample_path"], "/foo.wav")

        reloaded = M8Sampler.from_dict(params)
        self.assertEqual(reloaded.sample_path, "/foo.wav")

    def test_play_mode_enum(self):
        s = M8Sampler()
        s.play_mode = M8PlayMode.FWDLOOP
        self.assertEqual(s.play_mode, int(M8PlayMode.FWDLOOP))
        self.assertEqual(s.to_dict()["params"]["play_mode"], "FWDLOOP")


if __name__ == "__main__":
    unittest.main()
