#include "motion.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
int main(void) {
    mc_landmark pts[3]={{1,0,0,1,1},{0,0,0,1,1},{0,1,0,1,1}};
    mc_pose p={pts,3,0};
    float r=0;
    assert(mc_distance(&p,0,1,&r)==0 && fabsf(r-1)<1e-5f);
    assert(mc_angle(&p,0,1,2,&r)==0 && fabsf(r-1.5707963f)<1e-5f);
    assert(mc_angle(&p,0,0,2,&r)==-1);
    pts[2].valid=0;
    assert(mc_distance(&p,1,2,&r)==-1);
    mc_ema f={.alpha=0.5f};
    mc_vec3 out;
    assert(mc_ema_step(&f,(mc_vec3){0,0,0},&out)==0);
    assert(mc_ema_step(&f,(mc_vec3){1,0,0},&out)==0 && fabsf(out.x-.5f)<1e-6f);
    mc_pinch s={.close_threshold=.10f,.open_threshold=.16f,.min_frames=2};
    const float trace[]={.3f,.09f,.08f,.13f,.17f,.18f,.09f,.08f};
    const mc_event expected[]={0,0,MC_PINCH_DOWN,0,0,MC_PINCH_UP,0,MC_PINCH_DOWN};
    for (size_t i=0;i<sizeof(trace)/sizeof(trace[0]);i++)
        assert(mc_pinch_step(&s,1,trace[i])==expected[i]);
    assert(mc_pinch_step(&s,0,0)==MC_PINCH_UP);
    assert(mc_pinch_step(&s,0,0)==MC_NONE);
    puts("motion: all tests passed");
    return 0;
}
