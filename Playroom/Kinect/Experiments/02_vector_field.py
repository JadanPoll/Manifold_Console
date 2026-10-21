import freenect, cv2, numpy as np

while True:
    depth, _ = freenect.sync_get_depth()
    
    # Normalize and smooth the 'terrain' of the room
    depth_8 = (np.clip(depth, 400, 1000) / 1000.0 * 255).astype(np.uint8)
    blurred = cv2.GaussianBlur(depth_8, (15, 15), 0)
    
    # Calculate 'Slope' (Sobel derivatives) to find the 3D curves of your body
    sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=5)
    sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=5)
    
    # Combine slopes into a high-contrast 'Vector Map'
    mag = np.sqrt(sobelx**2 + sobely**2)
    mag = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # Apply a psychedelic colormap to the 3D data
    vectors = cv2.applyColorMap(mag, cv2.COLORMAP_JET)
    
    cv2.imshow('3D Vector Topography', vectors)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

freenect.sync_stop(); cv2.destroyAllWindows()
