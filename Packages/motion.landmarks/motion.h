#ifndef MC_MOTION_H
#define MC_MOTION_H
#include <stddef.h>
#include <stdint.h>

/* Normalized coordinates are in the camera image's coordinate system.
 * Detectors own landmark inference; this library never opens a camera. */
typedef struct {float x, y, z; float confidence; uint8_t valid;} mc_landmark;
typedef struct {const mc_landmark *points; size_t count; double timestamp_s;} mc_pose;
typedef struct {float x, y, z;} mc_vec3;
typedef struct {float alpha; mc_vec3 value; uint8_t initialized;} mc_ema;
typedef struct {
    float close_threshold, open_threshold;
    unsigned min_frames, consecutive;
    uint8_t down;
} mc_pinch;
typedef enum {MC_NONE=0, MC_PINCH_DOWN=1, MC_PINCH_UP=2} mc_event;

/* Return -1 if missing/invalid landmarks; never silently substitute zero. */
int mc_distance(const mc_pose *pose, size_t a, size_t b, float *result);
int mc_angle(const mc_pose *pose, size_t a, size_t pivot, size_t b, float *radians);
int mc_ema_step(mc_ema *filter, mc_vec3 input, mc_vec3 *result);
/* observed=0 denotes tracking loss; it emits release if previously down. */
mc_event mc_pinch_step(mc_pinch *state, int observed, float distance);
void mc_pinch_reset(mc_pinch *state);
#endif
