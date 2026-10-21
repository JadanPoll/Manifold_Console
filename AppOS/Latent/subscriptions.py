"""Cooperative update scheduling. Not resource isolation or a real-time scheduler."""
from dataclasses import dataclass
import math
import time

PROFILES=("foreground","background","constrained")

@dataclass(frozen=True)
class Range:
    minimum: float
    preferred: float
    maximum: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.minimum,self.preferred,self.maximum)):
            raise ValueError("non-finite rate")
        if not 0 < self.minimum <= self.preferred <= self.maximum <= 240:
            raise ValueError("require 0 < minimum <= preferred <= maximum <= 240")

@dataclass
class Subscription:
    name: str
    callback: object
    foreground: Range
    background: Range
    constrained: Range
    last_run: float | None = None

    def rate(self, profile):
        if profile not in PROFILES:
            raise ValueError("invalid profile")
        return getattr(self,profile).preferred

class Scheduler:
    def __init__(self, clock=time.monotonic):
        self.clock=clock
        self.profile="foreground"
        self.subscriptions={}
    def subscribe(self,name,callback,foreground,background,constrained):
        if not callable(callback) or not name or name in self.subscriptions:
            raise ValueError("invalid or duplicate subscription")
        sub=Subscription(name,callback,foreground,background,constrained)
        self.subscriptions[name]=sub
        return sub
    def set_profile(self,profile):
        if profile not in PROFILES:
            raise ValueError("invalid profile")
        self.profile=profile
    def tick(self):
        now=self.clock()
        for sub in self.subscriptions.values():
            rate=sub.rate(self.profile)
            if sub.last_run is None or now-sub.last_run>=1/rate:
                sub.last_run=now
                sub.callback()
    def inspect(self):
        return [{"name":s.name,"profile":self.profile,"target_hz":s.rate(self.profile)} for s in self.subscriptions.values()]
