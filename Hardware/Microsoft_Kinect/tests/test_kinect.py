import freenect
import cv2
import numpy as np

print("Kinect Test: Press 'ESC' to exit.")

def get_depth():
    # Returns a numpy array of 11-bit depth values
    depth, _ = freenect.sync_get_depth()
    # Normalize to 8-bit (0-255) so we can actually see it in a window
    depth_view = (depth / 2047.0 * 255).astype(np.uint8)
    return depth_view

while True:
    # 1. Grab a frame
    frame = get_depth()

    # 2. Display it
    cv2.imshow('Kinect Live Depth', frame)

    # 3. Exit on ESC key
    if cv2.waitKey(10) == 27:
        break

freenect.sync_stop()
cv2.destroyAllWindows()
