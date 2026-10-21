#ifndef MC_DEPTH_H
#define MC_DEPTH_H
#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint32_t x;
    uint32_t y;
    uint16_t depth;
    uint8_t valid;
} McDepthPoint;

/* 11-bit raw depth, zero=invalid. Nonzero return means invalid arguments.
 * Input is contiguous row-major uint16_t samples, width*height samples.
 * Reads one frame, writes one summary. No allocation, mutation, or graphics.
 */
int mc_nearest_depth(const uint16_t *data, size_t width, size_t height, McDepthPoint *out);

#endif
