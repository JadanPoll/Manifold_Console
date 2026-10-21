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
