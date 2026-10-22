#ifndef MANIFOLD_SOBEL_H
#define MANIFOLD_SOBEL_H
#include <stddef.h>
#include <stdint.h>
/* Immutable input and caller-owned output. Strides measured in bytes.
   Returns 0 on success, -1 on invalid parameters. */
int mc_sobel_gray8(const uint8_t *src, size_t src_stride,
                   uint8_t *dst, size_t dst_stride,
                   size_t width, size_t height);
#endif
