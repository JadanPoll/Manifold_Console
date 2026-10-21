#include "frame.h"
#include <string.h>

McStatus mc_pool_init(McPool *pool, unsigned count, unsigned char **buffers, const size_t *capacities) {
    unsigned i;
    if (!pool || !buffers || !capacities || count == 0 || count > MC_FRAME_MAX_SLOTS) return MC_INVALID;
    memset(pool, 0, sizeof(*pool));
    pool->newest = -1;
    for (i = 0; i < count; ++i) {
        if (!buffers[i] || capacities[i] == 0) return MC_INVALID;
        pool->slots[i].bytes = buffers[i];
        pool->slots[i].capacity = capacities[i];
    }
    pool->slots_count = count;
    return MC_OK;
}

McStatus mc_publish(McPool *pool, const void *src, size_t n, uint64_t timestamp_ns) {
    unsigned i;
    int selected = -1;
    McSlot *s;
    if (!pool || !src || n == 0 || pool->slots_count == 0) return MC_INVALID;
    /* Prefer an unleased slot other than the most recent one. */
    for (i = 0; i < pool->slots_count; ++i) {
        if ((int)i != pool->newest && pool->slots[i].readers == 0 && pool->slots[i].capacity >= n) {
            selected = (int)i;
            break;
        }
    }
    if (selected < 0 && pool->newest >= 0) {
        s = &pool->slots[pool->newest];
        if (s->readers == 0 && s->capacity >= n) selected = pool->newest;
    }
    if (selected < 0) return MC_BUSY;
    s = &pool->slots[selected];
    memcpy(s->bytes, src, n);
    s->length = n;
    s->timestamp_ns = timestamp_ns;
    s->generation = ++pool->generation;
    pool->newest = selected;
    return MC_OK;
}

McStatus mc_acquire(McPool *pool, McFrame *out) {
    McSlot *s;
    if (!pool || !out) return MC_INVALID;
    if (pool->newest < 0 || pool->slots_count == 0) return MC_EMPTY;
    s = &pool->slots[pool->newest];
    if (s->readers == UINT32_MAX) return MC_BUSY;
    ++s->readers;
    *out = (McFrame){s->bytes, s->length, s->generation, s->timestamp_ns, (unsigned)pool->newest};
    return MC_OK;
}

McStatus mc_release(McPool *pool, McFrame *frame) {
    McSlot *s;
    if (!pool || !frame || !frame->data || frame->slot >= pool->slots_count) return MC_INVALID;
    s = &pool->slots[frame->slot];
    if (s->generation != frame->generation || s->bytes != frame->data || s->readers == 0)
        return MC_STALE;
    --s->readers;
    *frame = (McFrame){0};
    return MC_OK;
}
