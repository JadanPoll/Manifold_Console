#include "frame.h"
#include "timing.h"
#include <inttypes.h>
#include <stdio.h>

#define FRAME_BYTES 256
static unsigned char storage[3][FRAME_BYTES];

static unsigned long sum_pixels(const McFrame *frame) {
    size_t i;
    unsigned long sum = 0;
    for (i = 0; i < frame->length; ++i) sum += frame->data[i];
    return sum;
}
static unsigned long count_bright(const McFrame *frame) {
    size_t i;
    unsigned long count = 0;
    for (i = 0; i < frame->length; ++i) count += frame->data[i] > 127;
    return count;
}

int main(void) {
    McPool pool;
    McFrame game = {0}, research = {0};
    unsigned char incoming[FRAME_BYTES];
    unsigned char *buffers[] = {storage[0], storage[1], storage[2]};
    size_t sizes[] = {FRAME_BYTES, FRAME_BYTES, FRAME_BYTES};
    size_t i;
    for (i = 0; i < FRAME_BYTES; ++i) incoming[i] = (unsigned char)i;
    if (mc_pool_init(&pool, 3, buffers, sizes) != MC_OK) return 1;
    MC_TICK(total);
    if (mc_publish(&pool, incoming, sizeof incoming, 1) != MC_OK) return 2;
    if (mc_acquire(&pool, &game) != MC_OK || mc_acquire(&pool, &research) != MC_OK) return 3;
    MC_TICK(consumers);
    printf("shared address: %s\n", game.data == research.data ? "yes" : "no");
    printf("game sum: %lu; research bright count: %lu; generation: %" PRIu64 "\n",
           sum_pixels(&game), count_bright(&research), game.generation);
    MC_TOCK(consumers);
    if (mc_release(&pool, &game) != MC_OK || mc_release(&pool, &research) != MC_OK) return 4;
    MC_TOCK(total);
    return 0;
}
