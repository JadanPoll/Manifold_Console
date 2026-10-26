"""Manifold Camera Lab: start an experiment, not a dependency debugging session.

Each optional mode has an independent dependency check. Camera packages are
probed in a worker, never imported by the GUI. User-visible errors are short;
technical output is available on demand for copy/paste.
"""
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from camera_env import working_python, install_camera_tools

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "Applications/CameraLab/studio.py"
KINECT = ROOT / "Playroom/Kinect/Experiments/launch_kinect.py"
POSE = ROOT / "Packages/vision.pose.mediapipe/pose_viewer.py"
POSE_MODEL = Path.home() / ".local/share/manifold/models/pose_landmarker_lite.task"


class CameraLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold / Camera Lab")
        self.geometry("835x620")
        self.minsize(660, 490)
        self.proc = None
        self.proc_kind = None
        self.proc_name = None
        self.proc_log = []
        self.inbox = queue.Queue(maxsize=600)
        self.next_job = None
        self.pending_camera = None
        self.generation = 0
        self.setup_active = False
        self.logs_open = False
        self.camera = tk.StringVar(value="0")
        self.model = tk.StringVar(value=str(POSE_MODEL))
        self.status = tk.StringVar(value="Choose what you'd like to see. Connect a camera, or open a video.")
        self.make_ui()
        self.after(100, self.tick)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def make_ui(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="CAMERA LAB", font=("DejaVu Sans", 21, "bold")).pack(anchor="w")
        ttk.Label(root, text="Experiment immediately. Each mode works independently.").pack(anchor="w", pady=(0,12))

        video = ttk.LabelFrame(root, text="Regular camera or video file", padding=9)
        video.pack(fill="x", pady=4)
        line = ttk.Frame(video)
        line.pack(fill="x")
        ttk.Button(line, text="Show my camera", command=lambda:self.webcam("preview")).pack(side="left", padx=3)
        ttk.Button(line, text="Open video", command=self.video).pack(side="left", padx=3)
        ttk.Button(line, text="Edges", command=lambda:self.webcam("edges")).pack(side="left", padx=3)
        ttk.Button(line, text="Motion", command=lambda:self.webcam("motion")).pack(side="left", padx=3)
        ttk.Label(line, text="Camera #").pack(side="left", padx=(18,3))
        ttk.Spinbox(line, textvariable=self.camera, from_=0, to=20, width=4).pack(side="left")

        kinect = ttk.LabelFrame(root, text="Microsoft Kinect (depth camera; not an ordinary webcam)", padding=9)
        kinect.pack(fill="x", pady=4)
        line = ttk.Frame(kinect)
        line.pack(fill="x")
        ttk.Button(line, text="Show Kinect depth", command=lambda:self.kinect("depth")).pack(side="left", padx=3)
        ttk.Button(line, text="Depth edges", command=lambda:self.kinect("edges")).pack(side="left", padx=3)
        ttk.Button(line, text="Nearest point", command=lambda:self.kinect("point")).pack(side="left", padx=3)
        ttk.Button(line, text="Check connection", command=self.check_kinect).pack(side="left", padx=3)

        pose = ttk.LabelFrame(root, text="Full-body pose and dancing (optional add-on)", padding=9)
        pose.pack(fill="x", pady=4)
        line = ttk.Frame(pose)
        line.pack(fill="x")
        ttk.Button(line, text="Track my body", command=lambda:self.pose(False)).pack(side="left", padx=3)
        ttk.Button(line, text="Track a video", command=lambda:self.pose(True)).pack(side="left", padx=3)
        ttk.Button(line, text="Choose pose model…", command=self.pick_model).pack(side="left", padx=3)

        feedback = ttk.LabelFrame(root, text="What's happening", padding=12)
        feedback.pack(fill="x", pady=(12,5))
        ttk.Label(feedback, textvariable=self.status, font=("DejaVu Sans", 11),
                  wraplength=745, justify="left").pack(anchor="w", fill="x")

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(3,5))
        ttk.Button(buttons, text="Stop current experiment", command=self.stop).pack(side="left", padx=(0,5))
        self.fix_button = ttk.Button(buttons, text="Set up camera automatically", command=self.setup_camera)
        self.choose_button = ttk.Button(buttons, text="Use existing camera tools…", command=self.choose_python)
        ttk.Button(buttons, text="Troubleshooting details", command=self.toggle_logs).pack(side="right", padx=5)
        ttk.Button(buttons, text="Copy details", command=self.copy_logs).pack(side="right")

        self.details = ttk.LabelFrame(root, text="Technical details (optional)", padding=6)
        self.output = tk.Text(self.details, height=10, font=("DejaVu Sans Mono", 9),
                              wrap="word", bg="#fff", fg="#1b2a32")
        self.output.pack(fill="both", expand=True)
        self.record("Camera Lab opened. No camera has been accessed.")

        ttk.Label(root, text="Inside a viewer: 1 image · 2 edges · 3 motion · S save · Q close",
                  foreground="#576a75").pack(anchor="w", pady=(7,0))

    def record(self, line):
        self.output.insert("end", str(line).rstrip() + "\n")
        if int(self.output.index("end-1c").split(".")[0]) > 350:
            self.output.delete("1.0", "80.0")
        self.output.see("end")

    def toggle_logs(self):
        if self.logs_open:
            self.details.pack_forget()
        else:
            self.details.pack(fill="both", expand=True, pady=(2,4), before=self.master_last_label)
        self.logs_open = not self.logs_open

    @property
    def master_last_label(self):
        # The hint label is always the final child of the root container.
        return self.output.master.master.winfo_children()[-1]

    def copy_logs(self):
        self.clipboard_clear()
        self.clipboard_append(self.output.get("1.0", "end-1c"))
        self.status.set("Technical details copied. You can paste them into a message.")

    def offer(self, item):
        try:
            self.inbox.put_nowait(item)
        except queue.Full:
            try:
                self.inbox.get_nowait()
                self.inbox.put_nowait(item)
            except queue.Empty:
                pass

    def reader(self, proc):
        try:
            for line in proc.stdout:
                self.offer(("log", proc.pid, line.rstrip()))
        except (OSError, ValueError) as exc:
            self.offer(("log", proc.pid, "Log reader: " + str(exc)))

    def tick(self):
        try:
            while True:
                item = self.inbox.get_nowait()
                if item[0] == "log":
                    _, pid, line = item
                    self.record(f"[{pid}] {line}")
                    if self.proc and pid == self.proc.pid:
                        self.proc_log.append(line)
                        if len(self.proc_log)>100:
                            del self.proc_log[:40]
                elif item[0] == "probe":
                    _, gen, kind, name, args, python, tried = item
                    if gen != self.generation:
                        continue
                    if python:
                        self.record(f"Using an existing environment for {kind}: {python}")
                        self.fix_button.pack_forget()
                        self.choose_button.pack_forget()
                        script = STUDIO if kind == "camera" else POSE
                        self.start(name, [python, "-u", str(script), *args], kind)
                    elif kind == "camera":
                        self.pending_camera=(name,args)
                        self.status.set(
                            "I couldn't find the camera image tools on this Pi. "
                            "Your Kinect is a separate device: try 'Show Kinect depth' now, "
                            "or click 'Set up camera automatically' for a normal webcam."
                        )
                        self.record(f"Checked {tried} existing Python environment(s); OpenCV and NumPy not found together.")
                        self.fix_button.pack(side="left", padx=4)
                        self.choose_button.pack(side="left", padx=4)
                    else:
                        self.status.set(
                            "Body tracking needs the optional MediaPipe add-on. "
                            "You can still use camera preview, Kinect depth and other modes."
                        )
                        self.record(f"Checked {tried} Python environment(s); MediaPipe pose dependencies unavailable.")
                elif item[0] == "setup":
                    _, gen, ok, message, details = item
                    self.setup_active=False
                    self.record("Camera setup: " + message)
                    if details:
                        self.record(details[-8000:])
                    if gen != self.generation:
                        continue
                    self.status.set(message)
                    if ok and self.pending_camera:
                        name,args=self.pending_camera
                        self.camera_request(name,args)
        except queue.Empty:
            pass
        if self.proc and self.proc.poll() is not None:
            self.finished()
        if self.proc is None and self.next_job:
            name, command, kind = self.next_job
            self.next_job=None
            self.start(name,command,kind)
        if self.winfo_exists():
            self.after(100, self.tick)

    def finished(self):
        proc, kind, name = self.proc, self.proc_kind, self.proc_name
        code=proc.poll()
        lines="\n".join(self.proc_log).lower()
        self.record(f"FINISHED {name}: exit code {code}.")
        self.proc=None
        self.proc_kind=None
        self.proc_log=[]
        if self.next_job:
            return
        if kind == "preflight":
            if code == 0:
                self.status.set("Kinect connected and its software is available. "
                                "Choose 'Show Kinect depth' to see a live picture.")
            else:
                self.status.set("Kinect check couldn't finish. Check the cable, "
                                "then try 'Show Kinect depth' or open troubleshooting details.")
        elif code == 0:
            self.status.set(f"{name} closed. Choose another experiment.")
        elif "no module named 'cv2'" in lines or "opencv" in lines and "missing" in lines:
            self.status.set("Image tools are missing from the selected Python. "
                            "Try automatic camera setup; Kinect depth works separately.")
            self.fix_button.pack(side="left", padx=4)
        elif "libusb_error_busy" in lines or "unable to claim interface" in lines:
            self.status.set("Your Kinect is in use by another program. Close the other "
                            "Kinect viewer and try again.")
        elif kind == "camera" and ("could not open" in lines or "unable to open" in lines):
            self.status.set("Couldn't open that regular webcam. Check that it's plugged in "
                            "and not already in use. For Kinect, use the Kinect buttons above.")
        elif kind == "pose":
            self.status.set("Body tracking couldn't start. It needs a MediaPipe model and "
                            "a working Pose add-on. Other Camera Lab modes still work.")
        else:
            self.status.set(f"{name} couldn't start. Open 'Troubleshooting details' "
                            "to see why, or choose a different experiment.")

    def start(self, name, command, kind):
        if self.proc and self.proc.poll() is None:
            self.next_job=(name,command,kind)
            self.stop(switch=True)
            return
        self.next_job=None
        try:
            self.proc = subprocess.Popen(command, cwd=str(ROOT), text=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         bufsize=1, start_new_session=False)
        except OSError as exc:
            self.record(f"Start failed: {name}: {exc}")
            self.status.set(f"Couldn't start {name}. Try another experiment or view details.")
            return
        self.proc_name=name
        self.proc_kind=kind
        self.proc_log=[]
        threading.Thread(target=self.reader, args=(self.proc,), daemon=True).start()
        self.status.set(f"Opening {name}… Close its window to finish, or select another experiment.")
        self.record(f"START {name}: {' '.join(map(str, command))}")

    def stop(self, switch=False):
        if not self.proc or self.proc.poll() is not None:
            if not switch:
                self.status.set("Nothing is running. Choose an experiment.")
            return
        proc=self.proc
        try:
            proc.terminate()
            self.record(f"Stop requested: {self.proc_name}.")
            if not switch:
                self.status.set("Closing the current experiment…")
            else:
                self.status.set("Switching experiments…")
            self.after(1700, lambda: self.force_if_still_running(proc))
        except OSError as exc:
            self.record(f"Stop failed: {exc}")
            self.status.set("Couldn't close that window. See troubleshooting details.")

    def force_if_still_running(self, proc):
        if proc.poll() is None:
            try:
                proc.kill()
                self.record(f"Experiment unresponsive, ended PID {proc.pid}.")
            except OSError:
                pass

    def camera_id(self):
        try:
            index=int(self.camera.get())
            if 0<=index<=20:
                return index
        except ValueError:
            pass
        self.status.set("Choose a camera number from 0 to 20.")
        return None

    def camera_request(self, name, args):
        self.generation+=1
        gen=self.generation
        self.pending_camera=(name,args)
        self.status.set("Finding your existing camera tools…")
        self.record("Checking installed camera environments without installing anything.")
        def probe():
            python,tried=working_python()
            self.offer(("probe",gen,"camera",name,args,python,tried))
        threading.Thread(target=probe,daemon=True).start()

    def webcam(self, mode):
        index=self.camera_id()
        if index is not None:
            self.camera_request("Webcam "+mode, ["--camera",str(index),"--mode",mode])

    def video(self):
        file=filedialog.askopenfilename(parent=self, title="Select a video",
                    filetypes=[("Videos","*.mp4 *.avi *.mkv *.mov *.webm"),("All files","*")])
        if file:
            self.camera_request("Video preview", ["--video",file])

    def kinect(self, mode):
        self.generation+=1
        self.pending_camera=None
        self.start("Kinect "+("nearest point" if mode=="point" else mode),
                   [sys.executable,"-u",str(KINECT),"--mode",mode],"kinect")

    def check_kinect(self):
        self.generation+=1
        self.start("Kinect connection check",
                   [sys.executable,"-u",str(KINECT),"--check"],"preflight")

    def pick_model(self):
        file=filedialog.askopenfilename(parent=self, title="Choose a Pose Landmarker model",
                    filetypes=[("MediaPipe pose model","*.task"),("All files","*")])
        if file:
            self.model.set(file)
            self.status.set("Pose model selected. Choose 'Track my body' or 'Track a video'.")

    def pose(self, file_mode):
        model=Path(self.model.get()).expanduser()
        if not model.is_file():
            self.status.set("Body tracking needs a Pose Landmarker model file. "
                            "Choose 'Choose pose model…' to find it. "
                            "Other modes work without this file.")
            self.record("Pose model not found: "+str(model))
            return
        args=["--model",str(model)]
        if file_mode:
            file=filedialog.askopenfilename(parent=self, title="Select a dance video",
                 filetypes=[("Videos","*.mp4 *.avi *.mkv *.mov *.webm"),("All files","*")])
            if not file: return
            args.extend(["--video",file])
        else:
            index=self.camera_id()
            if index is None: return
            args.extend(["--camera",str(index)])
        self.generation+=1
        gen=self.generation
        self.status.set("Checking whether body tracking is ready…")
        def probe():
            python,tried=working_python(check=("mediapipe","cv2","numpy"))
            self.offer(("probe",gen,"pose","Body tracking",args,python,tried))
        threading.Thread(target=probe,daemon=True).start()

    def setup_camera(self):
        if self.setup_active:
            self.status.set("Camera setup is already running; other modes remain available.")
            return
        self.setup_active=True
        gen=self.generation
        self.status.set("Setting up camera image tools in a private Manifold folder. "
                        "Your Kinect setup and system Python are left alone.")
        self.record("User requested camera setup. Installing binary packages in ~/.venvs/manifold-camera only.")
        def work():
            ok,message,details=install_camera_tools()
            self.offer(("setup",gen,ok,message,details))
        threading.Thread(target=work,daemon=True).start()

    def choose_python(self):
        selected=filedialog.askopenfilename(parent=self, title="Select an existing Python with camera tools")
        if not selected: return
        os.environ["MANIFOLD_CAMERA_PYTHON"]=selected
        self.record("Selected existing camera Python: " + selected)
        if self.pending_camera:
            name,args=self.pending_camera
            self.camera_request(name,args)
        else:
            self.status.set("Existing camera environment selected. Choose a webcam or video mode.")

    def close(self):
        self.generation+=1
        self.next_job=None
        self.stop()
        self.destroy()


if __name__=="__main__":
    CameraLab().mainloop()
