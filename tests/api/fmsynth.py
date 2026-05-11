"""FMSynth-specific tests. Cross-cutting behaviour lives in instruments.py."""
import unittest

from m8.api.instruments.fmsynth import (
    M8FMSynth, M8FMAlgo, M8FMWave, M8FMOperatorModDest,
)


class TestM8FMSynthSpecifics(unittest.TestCase):
    def test_all_four_operators_independent(self):
        fm = M8FMSynth()
        fm.op_a_shape = M8FMWave.SIN
        fm.op_b_shape = M8FMWave.TRI
        fm.op_c_shape = M8FMWave.SAW
        fm.op_d_shape = M8FMWave.SQR

        params = fm.to_dict()["params"]
        self.assertEqual(params["op_a_shape"], "SIN")
        self.assertEqual(params["op_b_shape"], "TRI")
        self.assertEqual(params["op_c_shape"], "SAW")
        self.assertEqual(params["op_d_shape"], "SQR")

    def test_operator_mod_routing(self):
        fm = M8FMSynth()
        fm.op_a_mod_a = M8FMOperatorModDest.MOD2_PIT
        fm.op_b_mod_b = M8FMOperatorModDest.MOD3_LEV
        round_tripped = M8FMSynth.read(fm.write())
        self.assertEqual(round_tripped.op_a_mod_a, int(M8FMOperatorModDest.MOD2_PIT))
        self.assertEqual(round_tripped.op_b_mod_b, int(M8FMOperatorModDest.MOD3_LEV))

    def test_algo_enum(self):
        fm = M8FMSynth()
        fm.algo = M8FMAlgo.AB_C_D
        self.assertEqual(fm.to_dict()["params"]["algo"], "AB_C_D")


if __name__ == "__main__":
    unittest.main()
