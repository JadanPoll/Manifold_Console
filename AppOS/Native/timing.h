#ifndef MC_TIMING_H
#define MC_TIMING_H
/* Compile with -DMC_TIMING=1, then enable output with MC_TIMING=1.
 * When compiled out, macros do not evaluate their arguments. */
#if defined(MC_TIMING) && MC_TIMING
#include <stdint.h>
uint64_t mc_time_ns(void);
int mc_timing_enabled(void);
void mc_timing_report(const char *name, uint64_t start_ns);
#define MC_TICK(name) uint64_t name = mc_timing_enabled() ? mc_time_ns() : 0
#define MC_TOCK(name) do { if (mc_timing_enabled()) mc_timing_report(#name, name); } while (0)
#else
#define MC_TICK(name) ((void)0)
#define MC_TOCK(name) ((void)0)
#endif
#endif
