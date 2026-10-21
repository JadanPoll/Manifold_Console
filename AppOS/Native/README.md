# Native AppOS foundation (C11)

A deliberately small **single-threaded** shared-frame path. One producer copies an incoming synthetic frame into caller-owned bounded storage. Several consumers acquire const pointers to the exact same slot and call ordinary native functions; releasing leases permits slot reuse. There is no heap allocation in the core hot path, no messages, no threads and no C++.

```sh
cd AppOS/Native
make
./build/demo
./build/observer_demo
make clean
make TIMING=1
MC_TIMING=1 ./build/demo
```

`TIMING=1` compiles instrumentation, and `MC_TIMING=1` enables runtime logging to stderr; without the build flag checkpoints compile out. If toggling the Makefile variable after a previous build, run `make clean` first. The frame demo has been compiled and run successfully on a Raspberry Pi; the newer observer demonstration is not yet verified there.

## Scope/limits
- This reference is not a true DMA zero-copy design: `mc_publish` copies incoming bytes into the pool once. Linux/driver buffer integration may eventually remove that copy while preserving ownership guarantees.
- Pointer lifetime lasts only until `mc_release`. Leases cannot be retained or reused after release; clients must not copy handles and double-release.
- No concurrency protection: use on one thread only. Independently running agent code must be isolated or synchronized appropriately.
- Slots use caller-provided memory (currently three static byte arrays in the demo). No device access, UI launch integration, file-system replacement or scheduling layer yet.
- The public C data types and ABI are **provisional**; do not treat this as a stable plugin interface.
- Error codes are returned for consequential ownership/availability faults, not blanket exception infrastructure.

The [observation policy](OBSERVATION_POLICY.md) documents the distinction between compute cadence and optional presentation. The headless observer demo performs 60 synthetic compute updates and outputs 10 snapshots; it does not yet ensure independent execution if presentation blocks.

Next: connect a real safe native source and consumer, then only add threading or shared-memory mechanisms when concrete workload requirements demand them.
