# Switchboard — architectural reference

**Problem:** multiple games, experiments and agents may demand the same devices, streams, or derived data. Reopening devices, conflicting ownership, duplicate computation, and inconsistent error interpretation can waste both compute and developer attention.

## Minimum distinction

- **Lib:** cheap stateless computation remains callable directly, without mandatory messages.
- **AppOS Services / Switchboard:** own expensive or exclusive resources, publish reusable streams, provide common lifecycle and error semantics.
- **AppOS / Latent:** decide whether and when a resource grant fits workload policy; do not duplicate the switchboard's acquisition/data routing.
- **Playroom / Axioms:** expose high-level demonstrable capabilities through the same interfaces.

The first Python module is deliberately an **in-process simulation**, not an actual background daemon, camera broker, security boundary, or scheduler. Run it with `python3 -m AppOS.Services.switchboard_demo` if desired.

## Contracts worth preserving

1. One producer may publish timestamped frames to multiple consumers; consumers have independent sampling preferences.
2. Shared acquisition and exclusive device control are distinct. Explicitly release shared subscribers before requesting an exclusive lease in this first version (no hidden preemption).
3. Latest-only delivery bounds memory and does **not** guarantee every frame arrives. Lossless sampling and frame retention need different contracts.
4. Errors have stable codes such as DEVICE_BUSY and NOT_OWNER, plus plain-language explanations. Do not interpret all USB failures as contention.
5. Consumers identify themselves. Future cross-process versions must authenticate identities and clean up leases on crash or disconnect.
6. Shared derived computation is optional: only deduplicate compatible models, modes, timing, and calibration.

## Deferred on purpose

Actual IPC/zero-copy buffers; lease queues, durations and fairness; process crash cleanup; hardware drivers; CPU/memory budgets; permissions; recorded compatibility evidence; remote control. These require real consumers and are not solved by this reference model.

**REM criterion:** prefer local direct calls unless avoided setup, contention, duplication or maintenance exceeds the cost of messaging, copies, arbitration and common-mode failures.
