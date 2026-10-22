#include "sobel.h"
#include <limits.h>
#include <string.h>
#include <stdint.h>

int mc_sobel_gray8(const uint8_t *src, size_t src_stride,
                   uint8_t *dst, size_t dst_stride,
                   size_t width, size_t height) {
    if (!src || !dst || width < 3 || height < 3 ||
        width > src_stride || width > dst_stride ||
        src_stride > SIZE_MAX / height || dst_stride > SIZE_MAX / height)
        return -1;
    for (size_t y = 0; y < height; ++y)
        memset(dst + y * dst_stride, 0, width);
    for (size_t y = 1; y + 1 < height; ++y) {
        const uint8_t *a = src + (y - 1) * src_stride;
        const uint8_t *b = src + y * src_stride;
        const uint8_t *c = src + (y + 1) * src_stride;
        for (size_t x = 1; x + 1 < width; ++x) {
            int gx = -(int)a[x-1] + (int)a[x+1]
                     - 2*(int)b[x-1] + 2*(int)b[x+1]
                     - (int)c[x-1] + (int)c[x+1];
            int gy = -(int)a[x-1] - 2*(int)a[x] - (int)a[x+1]
                     + (int)c[x-1] + 2*(int)c[x] + (int)c[x+1];
            /* L1 gradient magnitude, saturated into uint8. */
            int m = (gx < 0 ? -gx : gx) + (gy < 0 ? -gy : gy);
            dst[y * dst_stride + x] = (uint8_t)(m > 255 ? 255 : m);
        }
    }
    return 0;
}
