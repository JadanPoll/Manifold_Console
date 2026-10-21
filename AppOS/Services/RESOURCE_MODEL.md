# Resource ownership model — first principles

**Precondition:** Linux has delegated usable execution time and device access to Console processes. Manifold cannot create additional CPU cycles or guarantee that a busy hardware device is useful to everyone.

## Two independent objectives

**A. Useful CPU work per unit of granted compute:** prefer efficient representations, contiguous/batched operations, low allocation overhead, SIMD/vectorized or native kernels where relevant, and avoid unnecessary copies/messages. The kernel schedules threads and processes; we do not implement another CPU scheduler. Latent can request cooperative reduced work or enforce resource ceilings using OS facilities later.

**B. Useful reuse of expensive hardware state:** one owner opens/configures a scarce device; compatible consumers attach lightweight views of an immutable, versioned snapshot or shared stream. Do not repeatedly initialize, recalibrate or acquire the same state. Consumer cursors track what each has seen, independently of the producer. Where consumers require different incompatible modes, prefer explicit exclusive leases or deliberate mode changes.

## Mechanism and caveats

- `resource_views.py` is the **minimal in-process reference model**: one authoritative snapshot, versioned generation, multiple consumer views, independent read cursors and explicit detach. It does not physically clone device state.
- If a mutable frame buffer is reused by the driver, handing out its reference is unsafe: publish an immutable snapshot or use properly managed buffers with lifetime/refcounts. The current reference model relies on this contract but does **not** enforce immutability.
- Across processes, raw Python object references cannot be shared. Future options include shared-memory ring buffers and refcounted slots, with only control messages sent over IPC; but those require correct reclamation, permissions and crashed-client cleanup.
- Latest-only snapshots are right for interactive previews; recording or lossless sensor capture require a different bounded queue and explicit backpressure policy.
- Multiple readers do **not** entail multiple hardware executions. Simultaneous use may be impossible if a hardware mode is exclusive or the physical device cannot support aggregate requested throughput.
- No automatic hardware utilization maximization: doing unnecessary work to keep a device busy wastes energy and can degrade the primary user experience.

## Implementation selection (REM)

Use direct Lib calls for cheap local computation. Share acquisition, expensive initialization, calibration, immutable frames and compatible derived outputs only when redundant work or contention makes coordination worthwhile. When in doubt, retain the simpler representation and do not insert IPC.

See `switchboard.py` for the separate subscription/exclusive-lease reference; the two small models are **not yet integrated**.
