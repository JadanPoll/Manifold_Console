import freenect, cv2, numpy as np

print(">>> LASER GRID REVEAL: See the 'Light Coding' pattern.")

while True:
    # Capture the 10-bit Raw IR
    ir, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
    
    # High-pass filter: Ignore large areas of light, keep the sharp 'dots'
    ir_8 = (ir >> 2).astype(np.uint8)
    laplacian = cv2.Laplacian(ir_8, cv2.CV_8U)
    
    # Threshold to make the dots glow like a starry night
    _, dots = cv2.threshold(laplacian, 10, 255, cv2.THRESH_BINARY)
    
    # Colorize the lasers cyan (Matrix style)
    glow = cv2.cvtColor(dots, cv2.COLOR_GRAY2BGR)
    glow[dots > 0] = [255, 255, 0]
    
    cv2.imshow('Structured Light Grid', glow)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

freenect.sync_stop(); cv2.destroyAllWindows()
