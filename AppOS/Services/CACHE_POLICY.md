# Cache policy — RSM/REM decision record

## Question
Given scarce RAM, storage bandwidth and CPU time, what minimal machinery lets apps reuse file contents and derived states without redundant disk reads, copies, or recomputation?

## Existing baseline (Linux)
- Ordinary file I/O uses the Linux page cache. Repeated reads do not imply repeated SD-card access.
- File-backed `mmap` lets processes access the same cached physical file pages, subject to mapping semantics and pressure.
- `posix_fadvise(POSIX_FADV_WILLNEED)` and readahead provide **advisory**, not guaranteed, prefetching; `madvise` advises mapped regions.
- Bounded `tmpfs` holds transient files in virtual memory and may swap. Avoid `ramfs` for untrusted or unconstrained workloads.
- Never duplicate the page cache just to avoid ordinary OS calls.

## AppOS-specific opportunity
The OS knows access history. AppOS knows navigation intent and the expensive *derived* representation:
1. Predictively prefetch source pages/assets before an imminent screen or capability transition, if cheap and memory permits.
2. Retain decoded textures, parsed models, calibration, or compiled/transformed state **only** when recomputation cost, sharing and memory pressure justify it.
3. Share read-only immutable state across compatible consumers; define versions and invalidation when source/config changes.
4. Bound every optional cache and let foreground responsiveness outrank speculative work.

## Representation and ownership
**Distinguish** source-file page-cache residency, decoded/derived object caches, device/DMA frame buffers, and CPU L1/L2/L3 caches. These are distinct resources. The page cache does not guarantee CPU-cache residency.

Default route:
- Read-only file data: OS-backed file mapping / page cache.
- Reused derived state: optional small AppOS-owned cache keyed by (source identity, version, configuration).
- Live device frames: finite producer-controlled buffers, with valid lifetimes.
- Local math: direct `Lib` calls.

## Rival approaches / failure boundaries
- Blindly copying every asset to a private in-memory filesystem doubles memory use and may evict valuable page-cache pages.
- Cache locking/pinning can starve more important consumers. Don't promise guaranteed residency without paying for it.
- Prefetch can be counterproductive under pressure or inaccurate prediction.
- Sharing mutable or version-mismatched state risks inconsistent results.
- A globally centralized cache introduces locking, contention, invalidation and lifecycle cost.

## Current decision
**Do not implement a custom filesystem.** Keep a minimal cache-policy layer in AppOS that can later use existing Linux mechanisms. First native C proof-of-concept should consume mapped read-only assets, while the separate producer-owned live frame path uses explicit buffer lifetimes.

No benchmark or hardware tests requested at this stage. This document is an architectural hypothesis, not a claim of measured speedup.
