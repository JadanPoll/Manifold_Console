# Compute–presentation separation

## Principle

Scientific processing owns its required computation, data integrity and sampling cadence. A UI is a **consumer of summarized state**, not the driver of the experiment. Presentation is optional and may skip intermediate states; results and essential data capture must not silently depend on display cadence.

## Two different kinds of work

- **Critical computation:** sensor acquisition, experiment updates, inputs requiring low latency, result capture. Must satisfy its real timing requirements.
- **Presentation:** visual interpretation, menus, previews, animation. May inspect the latest consistent scientific state less frequently or not at all.

Not all UI work is optional: immediate input feedback and critical warnings may be high priority. Conversely, some visualizations are scientific measurements, not decorations; do not discard their samples merely because their *rendering* is throttled.

## First native sketch

`observer_demo.c` runs sixty synthetic scientific updates and reports only every sixth update. It uses the native frame pool and read-only leased frame access. This illustrates separation **without a graphics dependency or timer**, not actual sixty-Hz processing or a GPU benchmark. The application still runs a single synchronous thread; slow presentation can block future updates. Real independence will require a bounded nonblocking observer, event loop or separate worker, but only when a concrete case needs it.

## Human experience (REM)

Prioritize continuity, timely input acknowledgment, clear loading/ready states, and the comprehensibility of scientific information; don't equate graphic detail with usefulness. Speculative asset loading and decorative animation should yield to critical compute and input responsiveness.

## Deferred

Renderer/toolkit choice; animation scheduling; GPU versus CPU bottleneck measurements; refresh-on-change cache; cross-thread or cross-process state snapshots; predictive UI prefetch. Do not build an entire UI infrastructure to solve a headless demonstration.

## Observed graphics failure and minimum response

On a Raspberry Pi 5, redundant Tk Canvas state updates caused stalls that reproduced in native X11 workloads. The GPU-accelerated shared display path could also delay independent X11 clients. Therefore:

- Publish state changes instead of reasserting unchanged display state; coalesce superseded updates.
- Keep scientific state authoritative and presentation disposable; skip stale views, never silently skip required samples.
- Treat graphics operations as potentially blocking, including seemingly asynchronous calls and deferred redraw.
- Measure *independent observer latency* as well as local frame timings when deciding whether shared rendering offers sufficient isolation.
- Do not infer that separate CPU threads/processes protect shared GPU or XWayland service latency.
- Do not introduce a custom renderer, compositor, cgroup manager, or permanent tracing agent without a reproduced requirement and comparison against existing capabilities.

These are observed risks and design constraints, **not** claims that the present single-threaded native demo enforces nonblocking presentation. The next concrete workload should test that property before adding concurrency mechanisms.
