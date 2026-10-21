import freenect
import numpy as np
import cv2

print(">>> DIRECT USB AUDIO SNIPER: Initializing 1473 Phased Array...")

# Global storage for the shift
current_shift = 0

def audio_cb(dev, data, timestamp):
    global current_shift
    # The 1473 sends 164-byte packets of 4-channel, 16-bit audio
    audio_data = np.frombuffer(data, dtype=np.int16)
    
    # Isolate Mic 0 (Left) and Mic 3 (Right)
    # Slicing every 4th sample starting at index 0 and 3
    left = audio_data[0::4]
    right = audio_data[3::4]
    
    # Phased Array Math: Cross-correlation to find the delay
    if len(left) > 0 and len(right) > 0:
        correlation = np.correlate(left.astype(float), right.astype(float), "same")
        current_shift = np.argmax(correlation) - (len(left) // 2)

def body_cb(dev, ctx):
    global current_shift
    display = np.zeros((300, 640, 3), dtype=np.uint8)
    
    # Calculate screen position from the acoustic shift
    # Shift is usually between -10 and 10; we amplify it for the UI
    target_x = int(320 + (current_shift * 30))
    target_x = np.clip(target_x, 50, 590)
    
    # Draw the sound source
    cv2.circle(display, (target_x, 150), 40, (0, 255, 0), -1)
    cv2.putText(display, "SOUND ORIGIN", (target_x-70, 220), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow('Kinect 1473 Acoustic Tracker', display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        # This is the proper way to break the freenect loop
        return freenect.kill_helper(dev)

# This is the ONLY way the runloop accepts the audio callback in this wrapper
freenect.runloop(audio=audio_cb, body=body_cb)
