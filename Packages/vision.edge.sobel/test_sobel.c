#include "sobel.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    uint8_t blank[25] = {0}, dst[25];
    assert(mc_sobel_gray8(blank, 5, dst, 5, 5, 5) == 0);
    for (size_t i = 0; i < 25; ++i) assert(dst[i] == 0);
    uint8_t step[25];
    for (size_t y = 0; y < 5; ++y)
        for (size_t x = 0; x < 5; ++x)
            step[y*5+x] = (uint8_t)(x >= 2 ? 255 : 0);
    assert(mc_sobel_gray8(step, 5, dst, 5, 5, 5) == 0);
    assert(dst[2*5+1] == 255 && dst[2*5+2] == 255);
    assert(dst[2*5+3] == 0);
    assert(dst[0] == 0 && dst[24] == 0);
    assert(mc_sobel_gray8(NULL, 5, dst, 5, 5, 5) == -1);
    assert(mc_sobel_gray8(step, 2, dst, 5, 5, 5) == -1);
    puts("sobel: all tests passed");
    return 0;
}
