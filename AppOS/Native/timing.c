#define _POSIX_C_SOURCE 200809L
#include "timing.h"
#if defined(MC_TIMING) && MC_TIMING
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

uint64_t mc_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}
int mc_timing_enabled(void) {
    static int cached = -1;
    if (cached < 0) {
        const char *value = getenv("MC_TIMING");
        cached = value && (strcmp(value, "1") == 0 || strcmp(value, "true") == 0);
    }
    return cached;
}
void mc_timing_report(const char *name, uint64_t start_ns) {
    uint64_t now = mc_time_ns();
    if (start_ns && now >= start_ns)
        fprintf(stderr, "[mc-timing] %s %.3f ms\n", name, (double)(now - start_ns) / 1000000.0);
}
#endif

#if !defined(MC_TIMING) || !(MC_TIMING)
typedef int mc_timing_disabled_translation_unit;
#endif
