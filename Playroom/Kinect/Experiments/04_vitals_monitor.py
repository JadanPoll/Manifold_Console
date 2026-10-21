import freenect, cv2, numpy as np

print(">>> VITALS MONITOR: Stay perfectly still. Tracking facial blood flow...")

def get_video():
    array, _ = freenect.sync_get_video()
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)

# Buffer to hold the last 50 frames of face data
buffer = []

while True:
    frame = get_video()
    # Focus on the center of the screen (where the face should be)
    roi = frame[150:330, 250:390]
    
    # Calculate the average 'Redness' of the skin
    avg_red = np.mean(roi[:,:,2])
    buffer.append(avg_red)
    if len(buffer) > 50: buffer.pop(0)

    # If we have enough data, amplify the signal
    if len(buffer) == 50:
        # Find the "Pulse" (variance in the red channel)
        pulse = (avg_red - np.mean(buffer)) * 10 
        # Tint the screen red in sync with the pulse
        roi[:,:,2] = np.clip(roi[:,:,2] + pulse, 0, 255)

    cv2.rectangle(frame, (250, 150), (390, 330), (0, 255, 0), 2)
    cv2.imshow('Invisible Vitals (Amplified)', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'): break

freenect.sync_stop(); cv2.destroyAllWindows()
