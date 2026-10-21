import freenect, cv2, numpy as np

canvas = np.zeros((480, 640, 3), dtype=np.uint8)

while True:
    depth, _ = freenect.sync_get_depth()
    depth[depth == 0] = 2047 # Ignore errors
    
    # Find the coordinates of the absolute closest point to the camera
    y, x = np.unravel_index(np.argmin(depth), depth.shape)
    val = np.min(depth)
    
    # Display feed
    video, _ = freenect.sync_get_video()
    video = cv2.cvtColor(video, cv2.COLOR_RGB2BGR)
    
    # If something is within 'reach' (approx 1 meter), draw with it
    if val < 850:
        cv2.circle(canvas, (x, y), 8, (0, 255, 0), -1)
        cv2.circle(video, (x, y), 20, (0, 255, 255), 2)

    # Persist the drawing onto the video
    output = cv2.addWeighted(video, 0.5, canvas, 1.0, 0)
    
    cv2.imshow('3D Air Canvas (Press C to Clear)', output)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break
    elif key == ord('c'): canvas.fill(0)

freenect.sync_stop(); cv2.destroyAllWindows()
