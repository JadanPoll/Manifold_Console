import freenect, cv2, numpy as np

# Change these to 'slice' yourself out of the room
MIN_DIST, MAX_DIST = 500, 850 

while True:
    depth, _ = freenect.sync_get_depth()
    video, _ = freenect.sync_get_video()
    video = cv2.cvtColor(video, cv2.COLOR_RGB2BGR)

    # The 'Magic' Mask: 1 if inside the distance zone, 0 if outside
    mask = cv2.inRange(depth, MIN_DIST, MAX_DIST)
    
    # Apply the mask to the video: Reality disappears, only you remain
    hologram = cv2.bitwise_and(video, video, mask=mask)
    
    cv2.imshow('Kinect Hologram', hologram)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

freenect.sync_stop(); cv2.destroyAllWindows()
