import math
import unittest
from Lib.Signal import EMA, clamp

class TestSignal(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(3),1)
        self.assertEqual(clamp(-2),-1)
    def test_ema(self):
        s=EMA(.25)
        self.assertEqual(s.step(0),0)
        self.assertEqual(s.step(1),.25)
        s.reset()
        self.assertEqual(s.step(4),4)
    def test_bad_values(self):
        for alpha in (0,-1,2,float("nan")):
            with self.assertRaises(ValueError): EMA(alpha)
        with self.assertRaises(ValueError): EMA().step(math.inf)

if __name__=="__main__":
    unittest.main()
