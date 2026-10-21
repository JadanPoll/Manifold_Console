#include "depth.h"
#include <stdint.h>
#include <stddef.h>

int mc_nearest_depth(const uint16_t *data, size_t width, size_t height, McDepthPoint *out) {
    size_t n, i, best_index = 0;
    uint16_t best = UINT16_MAX;
    if (!data || !out || !width || !height || width > SIZE_MAX / height ||
        width > UINT32_MAX || height > UINT32_MAX) return -1;
    n = width * height;
    *out = (McDepthPoint){0};
    for (i = 0; i < n; ++i) {
        uint16_t d = data[i];
        if (d != 0 && d < best) {
            best = d;
            best_index = i;
        }
    }
    if (best != UINT16_MAX) {
        out->x = (uint32_t)(best_index % width);
        out->y = (uint32_t)(best_index / width);
        out->depth = best;
        out->valid = 1;
    }
    return 0;
}
