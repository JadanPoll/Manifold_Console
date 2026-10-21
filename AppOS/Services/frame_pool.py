"""Bounded in-process frame pool with explicit consumer leases.

A slot is immutable *by convention* while referenced; read-only memoryviews
protect readers from accidental writes through the exposed handle. This is
not process isolation, and a producer holding its own mutable buffer can still
violate the convention. A real IPC broker needs OS-managed buffer ownership.
"""
from dataclasses import dataclass
from time import monotonic

class PoolBusy(Exception):
    pass

class InvalidLease(Exception):
    pass

@dataclass
class _Slot:
    payload: bytes = b""
    generation: int = 0
    timestamp: float = 0.0
    refs: int = 0

class Lease:
    def __init__(self, pool, slot_index, generation, consumer):
        self._pool = pool
        self._index = slot_index
        self._generation = generation
        self.consumer = consumer
        self._closed = False

    @property
    def data(self):
        if self._closed:
            raise InvalidLease("lease closed")
        slot = self._pool._slots[self._index]
        if slot.generation != self._generation:
            raise InvalidLease("stale frame generation")
        return memoryview(slot.payload)

    @property
    def timestamp(self):
        if self._closed:
            raise InvalidLease("lease closed")
        return self._pool._slots[self._index].timestamp

    def close(self):
        if not self._closed:
            self._pool._release(self)
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

class FramePool:
    """Finite pool; producer never replaces a slot while consumers retain leases."""
    def __init__(self, capacity=3):
        if type(capacity) is not int or not 1 <= capacity <= 64:
            raise ValueError("capacity must be 1..64")
        self._slots = [_Slot() for _ in range(capacity)]
        self._current = None
        self._generation = 0
        self._leases = {}

    def publish(self, frame, timestamp=None):
        # This initial implementation deliberately copies into immutable bytes.
        # It trades copy overhead for sound ownership behavior.
        free = next((i for i, s in enumerate(self._slots) if s.refs == 0 and i != self._current), None)
        if free is None:
            free = next((i for i, s in enumerate(self._slots) if s.refs == 0), None)
        if free is None:
            raise PoolBusy("all frame buffers leased; producer must drop or defer")
        payload = bytes(frame)
        slot = self._slots[free]
        self._generation += 1
        slot.payload, slot.generation, slot.timestamp = payload, self._generation, monotonic() if timestamp is None else timestamp
        self._current = free
        return self._generation

    def acquire(self, consumer):
        if not consumer or self._current is None:
            raise InvalidLease("missing consumer or frame")
        slot = self._slots[self._current]
        slot.refs += 1
        lease = Lease(self, self._current, slot.generation, consumer)
        self._leases.setdefault(consumer, set()).add(lease)
        return lease

    def _release(self, lease):
        slot = self._slots[lease._index]
        if slot.generation != lease._generation or slot.refs <= 0:
            raise InvalidLease("invalid frame lease")
        slot.refs -= 1
        held = self._leases.get(lease.consumer)
        if held is not None:
            held.discard(lease)
            if not held:
                self._leases.pop(lease.consumer, None)

    def detach(self, consumer):
        """Release all in-process leases belonging to a disconnected consumer."""
        for lease in tuple(self._leases.get(consumer, ())):
            lease.close()

    def status(self):
        return {"capacity": len(self._slots), "generation": self._generation,
                "held": sum(s.refs for s in self._slots),
                "owners": sorted(self._leases),
                "free": sum(s.refs == 0 for s in self._slots)}
