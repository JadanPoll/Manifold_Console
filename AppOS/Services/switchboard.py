"""In-process reference model for shared streams and exclusive device leases.

No hardware I/O, IPC, privilege enforcement or scheduling claims. Integrations
can later put a process boundary behind this interface without changing clients.
"""
from dataclasses import dataclass
from collections import deque
from enum import Enum
from time import monotonic

class Code(str, Enum):
    BUSY = "DEVICE_BUSY"
    UNKNOWN = "DEVICE_UNKNOWN"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_OWNER = "NOT_OWNER"
    INCOMPATIBLE = "MODE_INCOMPATIBLE"

class SwitchboardError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

@dataclass(frozen=True)
class Frame:
    sequence: int
    timestamp: float
    payload: object

@dataclass
class Subscription:
    consumer: str
    every_n_frames: int
    latest: Frame | None = None
    delivered: int = 0

class Stream:
    """A producer publishes once; each subscriber keeps only its newest frame.

    This deliberate latest-only policy bounds queue growth but drops frames.
    Consumers needing lossless recording need a different contract.
    """
    def __init__(self, name):
        self.name = name
        self.subscribers = {}
        self.sequence = 0
        self.exclusive = None
        self.mode = "shared"

    def subscribe(self, consumer, every_n_frames=1):
        if self.exclusive is not None:
            raise SwitchboardError(Code.BUSY, "exclusive lease active")
        if not consumer or type(every_n_frames) is not int or every_n_frames < 1:
            raise SwitchboardError(Code.BAD_REQUEST, "invalid subscription")
        sub = Subscription(consumer, every_n_frames)
        self.subscribers[consumer] = sub
        return sub

    def unsubscribe(self, consumer):
        self.subscribers.pop(consumer, None)

    def publish(self, payload, timestamp=None):
        if self.exclusive is not None:
            raise SwitchboardError(Code.BUSY, "shared stream suspended for exclusive owner")
        self.sequence += 1
        frame = Frame(self.sequence, monotonic() if timestamp is None else timestamp, payload)
        for sub in self.subscribers.values():
            if self.sequence % sub.every_n_frames == 0:
                sub.latest = frame
                sub.delivered += 1
        return frame

    def take_latest(self, consumer):
        if consumer not in self.subscribers:
            raise SwitchboardError(Code.NOT_OWNER, "no subscription for consumer")
        sub = self.subscribers[consumer]
        frame, sub.latest = sub.latest, None
        return frame

    def acquire_exclusive(self, consumer):
        if self.exclusive is not None or self.subscribers:
            raise SwitchboardError(Code.BUSY, "release shared subscribers before exclusive lease")
        if not consumer:
            raise SwitchboardError(Code.BAD_REQUEST, "missing lease holder")
        self.exclusive = consumer

    def release_exclusive(self, consumer):
        if self.exclusive != consumer:
            raise SwitchboardError(Code.NOT_OWNER, "only lease holder can release")
        self.exclusive = None

    def status(self):
        return {"name": self.name, "mode": "exclusive" if self.exclusive else "shared",
                "exclusive_owner": self.exclusive, "subscribers": list(self.subscribers),
                "sequence": self.sequence}

class Switchboard:
    def __init__(self):
        self.streams = {}

    def register(self, resource_id):
        if not resource_id or resource_id in self.streams:
            raise SwitchboardError(Code.BAD_REQUEST, "invalid or duplicate resource")
        self.streams[resource_id] = Stream(resource_id)
        return self.streams[resource_id]

    def get(self, resource_id):
        if resource_id not in self.streams:
            raise SwitchboardError(Code.UNKNOWN, "resource not registered: " + resource_id)
        return self.streams[resource_id]
