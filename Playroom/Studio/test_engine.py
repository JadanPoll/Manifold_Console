import unittest
from engine import EMA, Signal, oscillator, clamp

class EngineTests(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(4),1.0)
        self.assertEqual(clamp(-3),-1.0)
    def test_ema(self):
        filt=EMA(0.5)
        self.assertEqual(filt.step(0),0)
        self.assertEqual(filt.step(1),0.5)
    def test_invalid_alpha(self):
        with self.assertRaises(ValueError):
            EMA(0)
    def test_waveforms(self):
        self.assertAlmostEqual(oscillator(0,1,"sine"),0)
        self.assertEqual(oscillator(0,1,"square"),1)
    def test_history(self):
        s=Signal(history=2)
        for n in (1,2,3):
            s.step(n)
        self.assertEqual(list(s.raw),[2,3])

if __name__ == "__main__":
    unittest.main()
