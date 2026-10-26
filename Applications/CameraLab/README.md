# Camera Lab

Start from **Manifold Home → Camera Lab**, or run:

```sh
cd ~/Desktop/Manifold_Console
python3 Applications/CameraLab/lab.py
```

Choose **Show Kinect depth** if you plugged in a Microsoft Kinect 1473.
Choose **Show my camera** for an ordinary USB/UVC webcam. The Kinect depth
camera is *not* webcam index 0, so those buttons are deliberately separate.

## What users see

- **Show Kinect depth**: live depth image with `1` distance, `2` boundaries,
  `3` movement, `S` save and `Q` close. This uses the existing working
  `freenect` + `numpy` environment, plus Tkinter; **no OpenCV required**.
- **Nearest point**: the previously working Kinect + native C example. This
  mode still requires `AppOS/Native/build/libmcdepth.so`.
- **Show my camera / Open video**: webcam or file preview with simple edge
  and motion modes. The Lab searches for an existing Python interpreter
  with OpenCV before launching, instead of blindly using `/usr/bin/python3`.
- **Track my body / Track a video**: optional MediaPipe pose add-on with
  a user-provided `.task` model file.
- **Check connection**: Kinect USB + software probe, no camera opened.
  Passing this does *not* mean a live capture has succeeded.

If regular webcam OpenCV is missing, the Lab offers **Set up camera
automatically**. This is an *explicit user action*. It creates a private
environment at `~/.venvs/manifold-camera`, attempts to install **prebuilt**
NumPy/OpenCV packages (never compiles them and never invokes sudo), and then
resumes the selected experiment if setup succeeds. On unsupported Pi builds
or disconnected networks, setup may fail; Kinect depth and the rest of
Manifold remain usable. You can also select an existing camera Python.

User-facing messages explain the consequence and next step. Technical logs
remain accessible through **Troubleshooting details** and **Copy details**;
they do not replace the actionable message.

The Lab accepts switching experiments without requiring a manual stop. It
first requests termination of the previous capture and only starts a new
capture after that child exits. Home supervision still owns the Camera Lab
process group. It is not a hardware broker; only one experiment is managed
by this Lab at a time.

### Developer entry points

```sh
python3 Applications/CameraLab/studio.py --camera 0 --mode edges
python3 Playroom/Kinect/Experiments/launch_kinect.py --mode depth
python3 Playroom/Kinect/Experiments/launch_kinect.py --check
python3 -m unittest Applications.CameraLab.test_camera_env
```

The source is checked in, but the **new GUI and NumPy/Tk Kinect rendering
path require validation on the Pi**. Avoid reinstalling or replacing the
historically working Kinect environment just to make OpenCV available.
