"""In-process reference-counted shared state with independent consumer cursors.

A view is a reference, not a copy of the payload. Producer must treat published
payload as immutable. This is NOT shared memory between processes.
"""
from dataclasses import dataclass
from time import monotonic

@dataclass(frozen=True)
class Snapshot:
    generation: int
    timestamp: float
    payload: object

class Resource:
    def __init__(self, name):
        self.name=name
        self._snapshot=None
        self._generation=0
        self._consumers=set()

    def attach(self, consumer):
        if not consumer or consumer in self._consumers:
            raise ValueError("invalid or duplicate consumer")
        self._consumers.add(consumer)
        return View(self,consumer)

    def publish(self, payload, timestamp=None):
        self._generation+=1
        self._snapshot=Snapshot(self._generation,monotonic() if timestamp is None else timestamp,payload)
        return self._snapshot

    def describe(self):
        return {"resource":self.name,"consumers":len(self._consumers),
                "generation":self._generation,"has_state":self._snapshot is not None}

class View:
    def __init__(self, resource, consumer):
        self._resource=resource
        self.consumer=consumer
        self._seen=0
        self._closed=False

    def latest(self):
        if self._closed:
            raise RuntimeError("view closed")
        shot=self._resource._snapshot
        if shot is None or shot.generation==self._seen:
            return None
        self._seen=shot.generation
        return shot

    def close(self):
        if not self._closed:
            self._resource._consumers.discard(self.consumer)
            self._closed=True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
