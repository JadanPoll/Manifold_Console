"""Manifold Camera Lab: one-click source experiments, optional dependencies only.

Run: python3 Applications/CameraLab/lab.py
"""
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "Applications/CameraLab/studio.py"
KINECT = ROOT / "Playroom/Kinect/Experiments/launch_kinect.py"
POSE = ROOT / "Packages/vision.pose.mediapipe/pose_viewer.py"
POSE_PYTHON = Path.home() / ".venvs/manifold-pose/bin/python"
POSE_MODEL = Path.home() / ".local/share/manifold/models/pose_landmarker_lite.task"


class CameraLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold / Camera Lab")
        self.geometry("810x640")
        self.minsize(680, 520)
        self.configure(bg="#edf4f8")
        self.proc = None
        self.messages = queue.Queue(maxsize=500)
        self.status = tk.StringVar(value="Choose an experiment; cameras are opened only when you click Start.")
        self.camera = tk.StringVar(value="0")
        self.model = tk.StringVar(value=str(POSE_MODEL))
        self.build()
        self.after(100, self.tick)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        heading = tk.Frame(self, bg="#edf4f8", padx=20, pady=16)
        heading.pack(fill="x")
        tk.Label(heading, text="CAMERA LAB", bg="#edf4f8", fg="#162d41",
                 font=("DejaVu Sans", 20, "bold")).pack(anchor="w")
        tk.Label(heading, text="Webcam experiments  /  Kinect depth  /  Pose Tracking",
                 bg="#edf4f8", fg="#36576a").pack(anchor="w")

        actions = ttk.Frame(self, padding=(20, 0, 20, 12))
        actions.pack(fill="x")
        ttk.Label(actions, text="Video index:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Spinbox(actions, textvariable=self.camera, from_=0, to=20, width=5).grid(
            row=0, column=1, sticky="w", padx=8)
        ttk.Button(actions, text="Start webcam studio", command=lambda: self.webcam("preview")).grid(
            row=0, column=2, sticky="ew", padx=5)
        ttk.Button(actions, text="Open a video file", command=self.video).grid(
            row=0, column=3, sticky="ew", padx=5)

        ttk.Label(actions, text="Vision tools:").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Button(actions, text="Edges", command=lambda: self.webcam("edges")).grid(
            row=1, column=2, sticky="ew", padx=5)
        ttk.Button(actions, text="Motion", command=lambda: self.webcam("motion")).grid(
            row=1, column=3, sticky="ew", padx=5)

        ttk.Label(actions, text="Kinect 1473:").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Button(actions, text="Check Kinect (no capture)", command=self.check_kinect).grid(
            row=2, column=2, sticky="ew", padx=5)
        ttk.Button(actions, text="Kinect depth point", command=self.kinect).grid(
            row=2, column=3, sticky="ew", padx=5)

        ttk.Label(actions, text="Kinect image:").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Button(actions, text="Depth image", command=lambda: self.kinect_image("depth")).grid(
            row=3, column=2, sticky="ew", padx=5)
        ttk.Button(actions, text="Depth edges", command=lambda: self.kinect_image("edges")).grid(
            row=3, column=3, sticky="ew", padx=5)

        ttk.Label(actions, text="Pose model:").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(actions, textvariable=self.model, width=50).grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=7)
        ttk.Button(actions, text="Browse…", command=self.pick_model).grid(
            row=4, column=3, sticky="ew", padx=5)
        ttk.Label(actions, text="Body tracking:").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Button(actions, text="Pose with webcam", command=lambda: self.pose(False)).grid(
            row=5, column=2, sticky="ew", padx=5)
        ttk.Button(actions, text="Pose with video", command=lambda: self.pose(True)).grid(
            row=5, column=3, sticky="ew", padx=5)

        actions.columnconfigure(2, weight=1)
        actions.columnconfigure(3, weight=1)

        management = ttk.Frame(self, padding=(20, 0, 20, 8))
        management.pack(fill="x")
        ttk.Button(management, text="Stop active experiment", command=self.stop).pack(side="left")
        ttk.Button(management, text="Copy diagnostics", command=self.copy_logs).pack(side="left", padx=8)
        ttk.Label(management, text="Studio: 1 preview · 2 edges · 3 motion · S save · Q exit").pack(side="right")

        ttk.Label(self, textvariable=self.status, wraplength=730,
                  padding=(20, 7, 20, 7)).pack(fill="x")
        container = ttk.Frame(self, padding=(20, 3, 20, 18))
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Diagnostics (selectable and copyable)").pack(anchor="w")
        self.output = tk.Text(container, height=14, wrap="word", font=("DejaVu Sans Mono", 10),
                              bg="#fff", fg="#182d3c")
        self.output.pack(fill="both", expand=True, pady=5)
        self.record("Ready. No devices have been opened.")

    def record(self, message):
        self.output.insert("end", message.rstrip() + "\n")
        if int(self.output.index("end-1c").split(".")[0]) > 300:
            self.output.delete("1.0", "60.0")
        self.output.see("end")

    def log_stream(self, process):
        if process.stdout is None:
            return
        for line in process.stdout:
            try:
                self.messages.put_nowait((process.pid, line))
            except queue.Full:
                # Diagnostic queue is bounded. Do not block the child process.
                try:
                    self.messages.get_nowait()
                    self.messages.put_nowait((process.pid, line))
                except queue.Empty:
                    pass

    def tick(self):
        try:
            while True:
                pid, message = self.messages.get_nowait()
                self.record(f"[{pid}] {message}")
        except queue.Empty:
            pass
        if self.proc and self.proc.poll() is not None:
            self.status.set(f"Experiment exited (code {self.proc.returncode}). Choose another.")
            self.proc = None
        self.after(100, self.tick)

    def start(self, title, command):
        if self.proc and self.proc.poll() is None:
            self.status.set("An experiment is already active. Click Stop to release its camera, then start another.")
            self.record("Already running PID " + str(self.proc.pid) + "; not starting a second capture.")
            return
        try:
            self.proc = subprocess.Popen(command, cwd=str(ROOT), text=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         bufsize=1, start_new_session=False)
            # Inherit Camera Lab's group so Home's group stop also terminates
            # child capture processes; don't create an escape session.
        except OSError as exc:
            self.record(f"Cannot start {title}: {exc}")
            self.status.set(f"Start failed: {exc}")
            return
        threading.Thread(target=self.log_stream, args=(self.proc,), daemon=True).start()
        self.status.set(f"{title} running (PID {self.proc.pid}). Close the experiment window or click Stop.")
        self.record(f"START {title}: {' '.join(map(str, command))}")

    def camera_id(self):
        try:
            num = int(self.camera.get())
            if not 0 <= num <= 20:
                raise ValueError
            return num
        except ValueError:
            self.status.set("Camera index must be between 0 and 20.")
            return None

    def webcam(self, mode):
        idx = self.camera_id()
        if idx is not None:
            self.start(f"Webcam ({mode})", [sys.executable, "-u", str(STUDIO), "--camera", str(idx),
                                           "--mode", mode])

    def video(self):
        chosen = filedialog.askopenfilename(parent=self, title="Select a video to examine",
                                            filetypes=[("Videos", "*.mp4 *.avi *.mkv *.mov *.webm"),("All files","*")])
        if chosen:
            self.start("Video studio", [sys.executable, "-u", str(STUDIO), "--video", chosen])

    def check_kinect(self):
        if self.proc and self.proc.poll() is None:
            self.record("Kinect check skipped: stop active experiment first.")
            self.status.set("Stop the current experiment to run the Kinect preflight.")
            return
        self.start("Kinect preflight", [sys.executable, "-u", str(KINECT), "--check"])

    def kinect(self):
        self.start("Kinect depth", [sys.executable, "-u", str(KINECT)])

    def kinect_image(self, mode):
        self.start("Kinect depth image (" + mode + ")", 
                   [sys.executable, "-u", str(KINECT), "--mode", mode])

    def pick_model(self):
        selected = filedialog.askopenfilename(parent=self, title="Select MediaPipe Pose Landmarker .task model",
                                              filetypes=[("MediaPipe model", "*.task"),("All files","*")])
        if selected:
            self.model.set(selected)

    def pose(self, file_mode):
        if self.proc and self.proc.poll() is None:
            self.status.set("Stop the active experiment before opening another camera.")
            return
        model = Path(self.model.get()).expanduser()
        if not model.is_file():
            self.status.set("Pose model missing. Browse to a local pose_landmarker*.task model first.")
            self.record(f"Missing pose model: {model}. See Packages/vision.pose.mediapipe/README.md")
            return
        python = str(POSE_PYTHON) if POSE_PYTHON.is_file() else sys.executable
        command = [python, "-u", str(POSE), "--model", str(model)]
        if file_mode:
            video = filedialog.askopenfilename(parent=self, title="Select a pose video",
                                                filetypes=[("Videos", "*.mp4 *.avi *.mkv *.mov *.webm"),("All files","*")])
            if not video:
                return
            command += ["--video", video]
        else:
            idx = self.camera_id()
            if idx is None:
                return
            command += ["--camera", str(idx)]
        self.start("Pose tracking", command)

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            self.status.set("No experiment is running.")
            return
        pid = self.proc.pid
        try:
            self.proc.terminate()  # Only this child; Home owns the app process group.
            self.record(f"Stop requested for PID {pid}.")
            self.status.set("Stop requested; the camera should be released when the process exits.")
        except ProcessLookupError:
            pass
        except OSError as exc:
            self.status.set(f"Stop failed: {exc}")
            self.record(f"Stop failed: {exc}")

    def copy_logs(self):
        self.clipboard_clear()
        self.clipboard_append(self.output.get("1.0", "end-1c"))
        self.status.set("Diagnostics copied.")

    def close(self):
        self.stop()
        self.destroy()


if __name__ == "__main__":
    CameraLab().mainloop()
