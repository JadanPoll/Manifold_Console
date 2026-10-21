/* Computation owns its cadence; presentation observes only when needed.
 * Entirely headless: prints a snapshot, does not render actual graphics.
 */
#include "frame.h"
#include "timing.h"
#include <stdint.h>
#include <stdio.h>

enum { FRAME_BYTES = 256, STEPS = 60, DISPLAY_EVERY = 6 };
static unsigned char buffer[2][FRAME_BYTES];

typedef struct {
    uint64_t updates;
    uint64_t total_brightness;
    uint64_t last_generation;
} ScientificState;

static void scientific_step(ScientificState *state, const McFrame *frame) {
    size_t i;
    uint64_t sum = 0;
    for (i = 0; i < frame->length; ++i) sum += frame->data[i];
    state->total_brightness += sum;
    state->updates++;
    state->last_generation = frame->generation;
}

static void present_snapshot(const ScientificState *state) {
    printf("view: samples=%llu latest=%llu average_brightness=%.2f\n",
           (unsigned long long)state->updates,
           (unsigned long long)state->last_generation,
           (double)state->total_brightness / (double)state->updates / FRAME_BYTES);
}

int main(void) {
    McPool pool;
    McFrame frame = {0};
    ScientificState state = {0};
    unsigned char *slots[] = {buffer[0], buffer[1]};
    size_t capacities[] = {FRAME_BYTES, FRAME_BYTES};
    unsigned char incoming[FRAME_BYTES];
    unsigned t;
    if (mc_pool_init(&pool, 2, slots, capacities) != MC_OK) return 1;
    MC_TICK(work);
    for (t = 0; t < STEPS; ++t) {
        size_t i;
        for (i = 0; i < FRAME_BYTES; ++i) incoming[i] = (unsigned char)(t + i);
        if (mc_publish(&pool, incoming, FRAME_BYTES, (uint64_t)t) != MC_OK) return 2;
        if (mc_acquire(&pool, &frame) != MC_OK) return 3;
        scientific_step(&state, &frame);
        if (mc_release(&pool, &frame) != MC_OK) return 4;
        /* Presentation does not retain the frame and is free to skip updates. */
        if ((t + 1) % DISPLAY_EVERY == 0) present_snapshot(&state);
    }
    MC_TOCK(work);
    printf("finished: %llu compute steps, %u view updates\n",
           (unsigned long long)state.updates, STEPS / DISPLAY_EVERY);
    return 0;
}
