# Latent (early prototype)

Purpose: preserve host responsiveness, make application costs and mitigations visible, and eventually allocate resources across workloads.

The initial implementation supervises **only direct children launched through the AppOS Shell**. Linux /proc gives approximate RSS and available memory. Each newly launched app gets lower CPU scheduling priority (nice +10); users can Stop or Kill it from the Shell. This is not CPU throttling, memory containment, process-tree containment or a security sandbox. Directly launched apps bypass Latent, and child programs can fork.

Future: enforce cgroup v2 resource ceilings and process-group lifecycle, monitor responsiveness, define opt-in quality of service subscriptions (FPS, resolution, model complexity), show policy recommendations and implement deliberate downscaling. GPU utilization and window responsiveness are not currently measured.

The first priority is to fix the costly Tk Canvas draw loop in Playroom Studio rather than masking it with a manager.
