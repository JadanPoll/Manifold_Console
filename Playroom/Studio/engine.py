"""Pure, dependency-free signal primitives for rapid experiments."""
from collections import deque
import math

def clamp(value, lo=-1.0, hi=1.0):
    return min(hi, max(lo, value))

def oscillator(t, rate=1.0, waveform="sine"):
    p = (t * max(rate, 0.0)) % 1.0
    if waveform == "triangle":
        return 1.0 - 4.0 * abs(p - 0.5)
    if waveform == "square":
        return 1.0 if p < 0.5 else -1.0
    return math.sin(2.0 * math.pi * p)

class EMA:
    def __init__(self, alpha=0.35):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0,1]")
        self.alpha = alpha
        self.last = None

    def step(self, x):
        self.last = x if self.last is None else self.alpha * x + (1.0-self.alpha) * self.last
        return self.last

class Signal:
    def __init__(self, alpha=0.35, history=500):
        self.filter = EMA(alpha)
        self.raw = deque(maxlen=history)
        self.smooth = deque(maxlen=history)

    def step(self, value):
        self.raw.append(value)
        self.smooth.append(self.filter.step(value))

