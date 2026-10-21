"""Constrained, declarative recipe validation. No eval(), exec(), or external effects."""
import json
from pathlib import Path

ALLOWED_WAVES = ("sine", "square", "triangle")

def validate(data):
    if not isinstance(data, dict) or set(data) != {"version", "waveform", "frequency", "gain", "smoothing"}:
        raise ValueError("recipe fields must be exactly version, waveform, frequency, gain, smoothing")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("unsupported version")
    if data["waveform"] not in ALLOWED_WAVES:
        raise ValueError("unknown waveform")
    for key,lo,hi in (("frequency",0.05,4.0),("gain",0.1,3.0),("smoothing",0.05,1.0)):
        value=data[key]
        if type(value) not in (int,float) or not lo<=value<=hi:
            raise ValueError(f"{key} outside allowed range [{lo}, {hi}]")
    return data

def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
