"""Pure scalar signal operations shared by Playroom and future inputs."""
import math

def clamp(value, lower=-1.0, upper=1.0):
    if not all(math.isfinite(v) for v in (value, lower, upper)):
        raise ValueError("non-finite number")
    if lower > upper:
        raise ValueError("lower bound exceeds upper bound")
    return min(upper, max(lower, value))

class EMA:
    """Exponential moving average; first sample initializes state."""
    def __init__(self, alpha=0.35):
        if not math.isfinite(alpha) or not 0 < alpha <= 1:
            raise ValueError("alpha must lie in (0,1]")
        self.alpha = alpha
        self.value = None

    def step(self, sample):
        if not math.isfinite(sample):
            raise ValueError("non-finite sample")
        self.value = sample if self.value is None else (
            self.alpha*sample+(1-self.alpha)*self.value
        )
        return self.value

    def reset(self):
        self.value = None
