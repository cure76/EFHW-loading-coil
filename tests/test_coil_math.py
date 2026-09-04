# tests/test_coil_math.py
import unittest
from coil_math import derived, petv2_od, wire_od_eff


class TestCoilMath(unittest.TestCase):
    def test_petv2_1mm(self):
        self.assertAlmostEqual(petv2_od(1.0), 1.093, places=6)
        self.assertAlmostEqual(wire_od_eff(1.0, 0), 1.093, places=6)
        self.assertAlmostEqual(wire_od_eff(1.0, 1.12), 1.12, places=6)

    def test_defaults_wheeler(self):
        d = derived(100, 55, 1.0, 0, 2, 14.5, 0.5)
        self.assertEqual(d["N"], 51)
        self.assertAlmostEqual(d["N_exact"], 51.21, places=2)
        self.assertAlmostEqual(d["winding_len"], 56.836, places=3)
        self.assertAlmostEqual(d["L_actual"], 99.46, places=2)
        self.assertAlmostEqual(d["flange_od"], 58.186, places=3)
        self.assertAlmostEqual(d["length"], 85.836, places=3)
        self.assertAlmostEqual(d["inner_d"], 51.0, places=3)
        self.assertAlmostEqual(d["lead_d"], 1.5, places=3)
        self.assertAlmostEqual(d["m4_d"], 4.4, places=3)
        self.assertAlmostEqual(d["shrink_id_min"], 60.186, places=3)
        self.assertAlmostEqual(d["rib_t"], 1.0, places=3)
        self.assertAlmostEqual(d["rib_w"], 14.142, places=3)
        self.assertGreater(d["rib_w"], d["m4_d"])
        self.assertAlmostEqual(d["channel_after_rib"], 50.0, places=3)
        self.assertAlmostEqual(d["lead_flange_gap"], 0.3, places=3)
        self.assertFalse(d["use_mid_leads"])
        self.assertAlmostEqual(d["lead_z"], 27.368, places=3)
        self.assertTrue(d["ok"])

    def test_L50_fewer_turns(self):
        d = derived(50, 55, 1.0, 0, 2, 14.5, 0.5)
        self.assertEqual(d["N"], 31)
        self.assertLess(d["length"], 85.836)

    def test_measured_wire_od(self):
        d = derived(100, 55, 1.0, 1.12, 2, 14.5, 0.5)
        self.assertAlmostEqual(d["pitch"], 1.12, places=6)
        self.assertAlmostEqual(d["lead_d"], 1.5, places=6)
        self.assertGreater(d["flange_od"], 58.186)

    def test_bad_wall(self):
        d = derived(100, 55, 1.0, 0, 30, 14.5, 0.5)
        self.assertFalse(d["ok"])

    def test_rib_too_thick(self):
        d = derived(100, 55, 1.0, 0, 2, 14.5, 0.5, rib_t=30)
        self.assertFalse(d["ok"])


if __name__ == "__main__":
    unittest.main()
