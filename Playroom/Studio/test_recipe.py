import unittest
from recipe import validate

class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.good = dict(version=1, waveform="sine", frequency=1.0, gain=1.0, smoothing=0.3)

    def test_valid(self):
        self.assertEqual(validate(self.good)["waveform"], "sine")

    def test_reject_extra_fields(self):
        with self.assertRaises(ValueError):
            validate({**self.good, "command": "echo unsafe"})

    def test_reject_out_of_range(self):
        with self.assertRaises(ValueError):
            validate({**self.good, "frequency": 900})

    def test_reject_boolean_number(self):
        with self.assertRaises(ValueError):
            validate({**self.good, "gain": True})

if __name__ == "__main__":
    unittest.main()
