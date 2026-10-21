#ifndef MC_FRAME_H
#define MC_FRAME_H
#include <stddef.h>
#include <stdint.h>

#define MC_FRAME_MAX_SLOTS 8
#define MC_FRAME_MAX_READERS 16

/* Single-threaded reference implementation. No hardware DMA or IPC. */
typedef enum {
    MC_OK = 0, MC_EMPTY = 1, MC_BUSY = 2,
    MC_INVALID = 3, MC_STALE = 4
} McStatus;

typedef struct {
    unsigned char *bytes;
    size_t capacity;
    size_t length;
    uint64_t generation;
    uint64_t timestamp_ns;
    uint32_t readers;
} McSlot;

typedef struct {
    McSlot slots[MC_FRAME_MAX_SLOTS];
    unsigned slots_count;
    int newest;
    uint64_t generation;
} McPool;

typedef struct {
    const unsigned char *data;
    size_t length;
    uint64_t generation;
    uint64_t timestamp_ns;
    unsigned slot;
} McFrame;

/* Slots use caller-provided backing storage; no heap allocation in this library. */
McStatus mc_pool_init(McPool *pool, unsigned count, unsigned char **buffers, const size_t *capacities);
McStatus mc_publish(McPool *pool, const void *src, size_t n, uint64_t timestamp_ns);
McStatus mc_acquire(McPool *pool, McFrame *out);
McStatus mc_release(McPool *pool, McFrame *frame);

#endif
