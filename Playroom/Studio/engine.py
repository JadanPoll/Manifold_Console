"""Small signal demo built on reusable Lib primitives."""
from collections import deque
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from Lib.Signal import EMA, clamp as _clamp

def clamp(value, lo=-1.0, hi=1.0):
    return _clamp(value, lo, hi)

def oscillator(t, rate=1.0, waveform="sine"):
    p = (t * max(rate, 0.0)) % 1.0
    if waveform == "triangle":
        return 1.0 - 4.0 * abs(p - 0.5)
    if waveform == "square":
        return 1.0 if p < 0.5 else -1.0
    return math.sin(2.0 * math.pi * p)

class Signal:
    def __init__(self, alpha=0.35, history=500):
        self.filter = EMA(alpha)
        self.raw = deque(maxlen=history)
        self.smooth = deque(maxlen=history)

    def step(self, value):
        self.raw.append(value)
        self.smooth.append(self.filter.step(value))
