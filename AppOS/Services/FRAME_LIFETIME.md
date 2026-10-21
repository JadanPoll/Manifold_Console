# Frame lifetime and reclamation (prototype)

**Ownership:** one producer publishes immutable snapshots into a bounded pool. Multiple consumers lease the current snapshot, obtaining read-only views of the *same Python bytes object*. No per-consumer payload copy occurs. Each lease must be explicitly released; `detach(consumer)` releases every known lease belonging to a disconnected in-process consumer.

**Safety invariant:** a slot with an outstanding lease cannot be overwritten. If all slots are held, `publish` reports `PoolBusy`; callers must choose whether to wait, drop a new frame, or reduce acquisition rate. Never block the Console UI thread indefinitely.

**Limitations:** `publish` copies input to bytes; this is not DMA or IPC zero-copy. References are Python objects in one process. No thread synchronization or malicious-consumer defense. A native buffer ring needs generation checks, explicit lengths/formats, consumer liveness, and release on process death. For shared memory, choose between readonly mappings, slot reference accounting, and failure-safe reclamation. A dead process must not indefinitely pin a frame.

This model is intentionally separate from `switchboard.py`: it establishes one ownership invariant before imposing a cross-process protocol. Don't centralize mathematical operations merely because they consume a frame.
