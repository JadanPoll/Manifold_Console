# Latent (early prototype)

Purpose: preserve host responsiveness, make application costs and mitigations visible, and eventually allocate resources across workloads.

The initial implementation supervises **only direct children launched through the AppOS Shell**. Linux /proc gives approximate RSS and available memory. Each newly launched app gets lower CPU scheduling priority (nice +10); users can Stop or Kill it from the Shell. This is not CPU throttling, memory containment, process-tree containment or a security sandbox. Directly launched apps bypass Latent, and child programs can fork.

Future: enforce cgroup v2 resource ceilings and process-group lifecycle, monitor responsiveness, define opt-in quality of service subscriptions (FPS, resolution, model complexity), show policy recommendations and implement deliberate downscaling. GPU utilization and window responsiveness are not currently measured.

The first priority is to fix the costly Tk Canvas draw loop in Playroom Studio rather than masking it with a manager.

## Cooperative subscriptions (implemented, opt-in)

`subscriptions.py` provides `Scheduler` and validated `Range(minimum, preferred, maximum)`. Each app registers callbacks with foreground, background, and constrained ranges; a caller drives `tick()` in its own event loop and can choose an explicit profile. This is voluntary update scheduling only. It neither limits CPU use outside callbacks nor adapts automatically to host pressure; values are declared by the app. No real-time guarantees.

Try `python3 -m AppOS.Latent.example` and `python3 -m unittest AppOS.Latent.test_subscriptions` from repository root.

## Opt-in diagnosis (implemented)

From the repository root:

```sh
python3 -m AppOS.Latent.diagnose snapshot
python3 -m AppOS.Latent.diagnose run --seconds 10 -- python3 Playroom/Playground/gravity.py
```

One ZIP contains version/display context, compositor/XWayland thread wait snapshots, and, for a managed command, monotonic-timestamped process samples, stdout, stderr, and an exit record. No sudo, daemon, modified kernel, or mandatory library dependency. The collector attempts to terminate its own child process group on timeout; it cannot recover a frozen kernel or guarantee termination of grandchildren that detach. Archives can contain sensitive process details; review before sharing. This is **not** a GPU-frame profiler, renderer isolation, or proof of fault ownership.

### Evidence from the Pi graphics investigation

A tiny Tk Canvas animation caused large interactive stalls despite low CPU use. The same class of pathology reproduced through native X11 drawing, was strongly dependent on XWayland GLAMOR acceleration, and implicated V3D buffer-wait timeout behavior. Unrelated X11 clients experienced latency spikes under drawing stress. A source-supported zero-timeout kernel defect was identified, but its correction has **not** been shown to remove every desktop symptom. Preserve the distinction between reproduced observations, source hypotheses, and completed causal interventions.

**Responsibility boundary:** Latent diagnoses and recommends; AppOS Runtime/Services must eventually implement any enforceable budgets or confinement. Do not place blocking diagnostic instrumentation in the presentation hot path. Enable expensive tracers only when justified by a specific causal question. Reuse existing tools (strace, gdb, protocol tracers, upstream regression tests), not a mandatory in-house trace engine. The absence of a privileged trace is an explicit limit, not proof of healthy graphics.

The first practical mitigation remains to avoid redundant Canvas visibility updates and avoid tying critical work to drawing cadence. A per-app nice level or watchdog does **not** guarantee isolation from a shared X server or GPU queue.
