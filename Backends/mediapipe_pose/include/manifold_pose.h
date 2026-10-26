#ifndef MANIFOLD_POSE_H
#define MANIFOLD_POSE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MF_POSE_LANDMARKS 33

typedef struct {
    float x, y, z;
    float visibility;
    float presence;
} mf_pose_landmark;

typedef struct {
    uint64_t timestamp_ms;
    uint32_t count; /* 0 or 33 in v1 */
    mf_pose_landmark landmarks[MF_POSE_LANDMARKS];
} mf_pose_frame;

typedef struct mf_pose mf_pose;

/* Stable Manifold-facing ABI. MediaPipe is an implementation detail. */
mf_pose *mf_pose_create(const char *model_path);
int mf_pose_process_rgb(mf_pose *ctx,
                        const uint8_t *rgb,
                        int width,
                        int height,
                        int stride_bytes,
                        uint64_t timestamp_ms,
                        mf_pose_frame *out);
const char *mf_pose_last_error(const mf_pose *ctx);
void mf_pose_destroy(mf_pose *ctx);

#ifdef __cplusplus
}
#endif
#endif
