#include "manifold_pose.h"

#include <cstring>
#include <memory>
#include <string>

#include "mediapipe/framework/formats/image.h"
#include "mediapipe/framework/formats/image_frame.h"
#include "mediapipe/tasks/cc/core/base_options.h"
#include "mediapipe/tasks/cc/vision/core/running_mode.h"
#include "mediapipe/tasks/cc/vision/pose_landmarker/pose_landmarker.h"

namespace mp_pose = mediapipe::tasks::vision::pose_landmarker;
namespace mp_core = mediapipe::tasks::vision::core;

struct mf_pose {
    std::unique_ptr<mp_pose::PoseLandmarker> task;
    std::string error;
    uint64_t last_timestamp = 0;
    bool has_timestamp = false;
};

static int fail(mf_pose *ctx, const std::string &message) {
    if (ctx) ctx->error = message;
    return -1;
}

extern "C" mf_pose *mf_pose_create(const char *model_path) {
    auto *ctx = new mf_pose;
    if (!model_path || !*model_path) {
        ctx->error = "Pose model path is empty.";
        return ctx;
    }

    auto options = std::make_unique<mp_pose::PoseLandmarkerOptions>();
    options->base_options.model_asset_path = model_path;
    options->running_mode = mp_core::RunningMode::VIDEO;
    options->num_poses = 1;
    options->output_segmentation_masks = false;

    auto created = mp_pose::PoseLandmarker::Create(std::move(options));
    if (!created.ok()) {
        ctx->error = created.status().ToString();
        return ctx;
    }
    ctx->task = std::move(created.value());
    return ctx;
}

extern "C" int mf_pose_process_rgb(mf_pose *ctx,
                                     const uint8_t *rgb,
                                     int width,
                                     int height,
                                     int stride_bytes,
                                     uint64_t timestamp_ms,
                                     mf_pose_frame *out) {
    if (!ctx || !out) return -1;
    out->count = 0;
    out->timestamp_ms = timestamp_ms;
    if (!ctx->task) return fail(ctx, ctx->error.empty() ? "Pose backend is not ready." : ctx->error);
    if (!rgb || width <= 0 || height <= 0 || stride_bytes < width * 3)
        return fail(ctx, "Invalid RGB frame.");
    if (ctx->has_timestamp && timestamp_ms <= ctx->last_timestamp)
        return fail(ctx, "Frame timestamps must increase.");

    auto frame = std::make_shared<mediapipe::ImageFrame>(
        mediapipe::ImageFormat::SRGB, width, height,
        mediapipe::ImageFrame::kDefaultAlignmentBoundary);

    for (int y = 0; y < height; ++y) {
        std::memcpy(frame->MutablePixelData() + y * frame->WidthStep(),
                    rgb + y * stride_bytes, static_cast<size_t>(width) * 3);
    }

    mediapipe::Image image(frame);
    auto detected = ctx->task->DetectForVideo(std::move(image),
                                               static_cast<int64_t>(timestamp_ms));
    if (!detected.ok()) return fail(ctx, detected.status().ToString());

    ctx->last_timestamp = timestamp_ms;
    ctx->has_timestamp = true;
    ctx->error.clear();

    const auto &result = detected.value();
    if (result.pose_landmarks.empty()) return 0;
    const auto &landmarks = result.pose_landmarks.front().landmarks;
    const size_t n = landmarks.size() < MF_POSE_LANDMARKS
                         ? landmarks.size()
                         : MF_POSE_LANDMARKS;
    for (size_t i = 0; i < n; ++i) {
        const auto &p = landmarks[i];
        out->landmarks[i].x = p.x;
        out->landmarks[i].y = p.y;
        out->landmarks[i].z = p.z;
        out->landmarks[i].visibility = p.visibility.value_or(0.0f);
        out->landmarks[i].presence = p.presence.value_or(0.0f);
    }
    out->count = static_cast<uint32_t>(n);
    return 0;
}

extern "C" const char *mf_pose_last_error(const mf_pose *ctx) {
    return ctx ? ctx->error.c_str() : "Pose context is null.";
}

extern "C" void mf_pose_destroy(mf_pose *ctx) {
    if (!ctx) return;
    if (ctx->task) ctx->task->Close().IgnoreError();
    delete ctx;
}
