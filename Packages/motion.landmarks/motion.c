#include "motion.h"
#include <math.h>

static int point(const mc_pose *p, size_t i) {
    return p && p->points && i < p->count && p->points[i].valid &&
           isfinite(p->points[i].x) && isfinite(p->points[i].y) &&
           isfinite(p->points[i].z);
}
int mc_distance(const mc_pose *p, size_t a, size_t b, float *out) {
    if (!out || !point(p,a) || !point(p,b)) return -1;
    float dx=p->points[a].x-p->points[b].x;
    float dy=p->points[a].y-p->points[b].y;
    float dz=p->points[a].z-p->points[b].z;
    *out=hypotf(hypotf(dx,dy),dz);
    return isfinite(*out)?0:-1;
}
int mc_angle(const mc_pose *p, size_t a, size_t pivot, size_t b, float *out) {
    if (!out || !point(p,a) || !point(p,pivot) || !point(p,b)) return -1;
    float ux=p->points[a].x-p->points[pivot].x;
    float uy=p->points[a].y-p->points[pivot].y;
    float uz=p->points[a].z-p->points[pivot].z;
    float vx=p->points[b].x-p->points[pivot].x;
    float vy=p->points[b].y-p->points[pivot].y;
    float vz=p->points[b].z-p->points[pivot].z;
    float nu=hypotf(hypotf(ux,uy),uz), nv=hypotf(hypotf(vx,vy),vz);
    if (!(nu>1e-8f) || !(nv>1e-8f)) return -1;
    float cosv=(ux*vx+uy*vy+uz*vz)/(nu*nv);
    if (!isfinite(cosv)) return -1;
    if (cosv>1) cosv=1;
    if (cosv< -1) cosv=-1;
    *out=acosf(cosv);
    return 0;
}
int mc_ema_step(mc_ema *f, mc_vec3 input, mc_vec3 *out) {
    if (!f || !out || !isfinite(f->alpha) ||
        f->alpha<=0 || f->alpha>1 ||
        !isfinite(input.x) || !isfinite(input.y) || !isfinite(input.z))
        return -1;
    if (!f->initialized) {f->value=input; f->initialized=1;}
    else {
        f->value.x += f->alpha*(input.x-f->value.x);
        f->value.y += f->alpha*(input.y-f->value.y);
        f->value.z += f->alpha*(input.z-f->value.z);
    }
    *out=f->value;
    return 0;
}
void mc_pinch_reset(mc_pinch *s) {
    if (s) {s->down=0; s->consecutive=0;}
}
mc_event mc_pinch_step(mc_pinch *s, int observed, float distance) {
    if (!s) return MC_NONE;
    /* Invalid geometry / tracking loss releases active controls immediately. */
    if (!observed || !isfinite(distance) || distance<0 ||
        !isfinite(s->close_threshold) || !isfinite(s->open_threshold) ||
        !(s->close_threshold<s->open_threshold)) {
        int was_down=s->down;
        mc_pinch_reset(s);
        return was_down?MC_PINCH_UP:MC_NONE;
    }
    int crossed=s->down ? distance>=s->open_threshold :
                          distance<=s->close_threshold;
    if (!crossed) {s->consecutive=0; return MC_NONE;}
    if (++s->consecutive < (s->min_frames ? s->min_frames : 1))
        return MC_NONE;
    s->consecutive=0;
    s->down=!s->down;
    return s->down?MC_PINCH_DOWN:MC_PINCH_UP;
}
