/* Deterministic recorded-landmark replay. No camera or external dependency.
 * CSV rows: timestamp_seconds, thumb_x,thumb_y, index_x,index_y, observed.
 * Timestamps must increase. Outputs semantic transitions (not input injection).
 */
#include "motion.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s path/to/landmarks.csv\n", argv[0]);
        return 2;
    }
    FILE *in = fopen(argv[1], "r");
    if (!in) { perror(argv[1]); return 2; }
    mc_pinch state={.close_threshold=0.10f,.open_threshold=0.16f,.min_frames=2};
    char row[512];
    double previous=-1;
    unsigned line=0, events=0;
    while (fgets(row, sizeof(row), in)) {
        ++line;
        if (row[0]=='#' || row[0]=='\n') continue;
        double stamp;
        float tx,ty,ix,iy;
        int observed;
        char extra;
        if (sscanf(row, " %lf , %f , %f , %f , %f , %d %c",
                   &stamp,&tx,&ty,&ix,&iy,&observed,&extra)!=6 ||
            !isfinite(stamp) || stamp<0 || stamp<=previous ||
            !isfinite(tx) || !isfinite(ty) ||
            !isfinite(ix) || !isfinite(iy) ||
            (observed!=0 && observed!=1)) {
            fprintf(stderr,"invalid recording at line %u\n",line);
            fclose(in);
            return 2;
        }
        previous=stamp;
        mc_landmark pts[]={{tx,ty,0,1,(uint8_t)observed},
                            {ix,iy,0,1,(uint8_t)observed}};
        mc_pose pose={pts,2,stamp};
        float distance=0;
        int valid=mc_distance(&pose,0,1,&distance)==0;
        mc_event event=mc_pinch_step(&state,valid,distance);
        if (event!=MC_NONE) {
            printf("%.3f,%s\n",stamp,event==MC_PINCH_DOWN?"PINCH_DOWN":"PINCH_UP");
            ++events;
        }
    }
    if (ferror(in)) {perror("read");fclose(in);return 2;}
    fclose(in);
    fprintf(stderr,"replay: %u rows; %u events\n",line,events);
    return 0;
}
