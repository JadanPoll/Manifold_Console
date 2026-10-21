
import freenect
import time

MIN_ANGLE = -25
MAX_ANGLE = 25
STEP = 2

print("Connecting to Kinect...")

ctx = freenect.init()
if ctx is None:
    raise RuntimeError("Failed to initialize libfreenect")

dev = freenect.open_device(ctx, 0)
if dev is None:
    freenect.shutdown(ctx)
    raise RuntimeError("Could not open Kinect")

angle = 0

print("""
KINECT MOTOR CONTROL

  u       Raise head by 2 degrees
  d       Lower head by 2 degrees
  0       Return to center
  s       Read current tilt angle
  q       Quit

Allowed range: -25 to +25 degrees
""")

try:
    while True:
        command = input("Command > ").strip().lower()

        if command == "q":
            break

        elif command == "u":
            angle = min(angle + STEP, MAX_ANGLE)

        elif command == "d":
            angle = max(angle - STEP, MIN_ANGLE)

        elif command == "0":
            angle = 0

        elif command == "s":
            result = freenect.update_tilt_state(dev)
            state = freenect.get_tilt_state(dev)
            measured = freenect.get_tilt_degs(state)
            print(f"Measured angle: {measured:.1f}°")
            continue

        else:
            print("Unknown command")
            continue

        print(f"Requesting angle: {angle}°")
        freenect.set_tilt_degs(dev, angle)
        time.sleep(0.5)

finally:
    freenect.close_device(dev)
    freenect.shutdown(ctx)
    print("Kinect disconnected.")
