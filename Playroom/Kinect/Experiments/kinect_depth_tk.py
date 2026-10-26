"""Kinect v1 depth playground with only freenect, NumPy and Tkinter.

No OpenCV, Internet connection, package installation or native C build.
The producer owns the Kinect. Tk reads only the latest rendered frame.
Keys: 1 depth image, 2 depth edges, 3 depth motion, S save PPM, Q/ESC exit.
"""
import argparse
from datetime import datetime
from pathlib import Path
import queue
import sys
import threading
import time
import tkinter as tk


def produce(stop, out, mode):
    try:
        import freenect
        import numpy as np
        previous = None
        last_render = 0.0
        while not stop.is_set():
            frame, stamp = freenect.sync_get_depth(format=freenect.DEPTH_MM)
            if frame is None:
                raise RuntimeError("The Kinect is connected but is not delivering depth images.")
            now = time.monotonic()
            if now - last_render < .10:
                continue
            last_render = now
            # Reduce to 320x240 before preparing a Tk image.
            gray_depth = frame[::2, ::2].astype(np.float32)
            valid = (gray_depth >= 500) & (gray_depth <= 4000)
            gray = np.where(valid, np.clip((4000 - gray_depth) * (255/3500), 0, 255), 0).astype(np.uint8)
            selected = mode[0]
            if selected == "edges":
                arr = gray.astype(np.int16)
                gradient = abs(arr[:, 1:] - arr[:, :-1])
                contour = np.zeros_like(gray)
                contour[:, 1:] = np.where(gradient > 18, 255, 0).astype(np.uint8)
                image = contour
            elif selected == "motion":
                image = np.zeros_like(gray) if previous is None else np.where(
                    abs(gray.astype(np.int16) - previous.astype(np.int16)) > 15, 255, 0
                ).astype(np.uint8)
            else:
                image = gray
            previous = gray.copy()
            h, w = image.shape
            rgb = np.repeat(image[:, :, None], 3, axis=2)
            ppm = f"P6\n{w} {h}\n255\n".encode("ascii") + rgb.tobytes()
            packet = ("image", selected, ppm, now)
            try:
                out.put_nowait(packet)
            except queue.Full:
                try:
                    out.get_nowait()
                except queue.Empty:
                    pass
                try:
                    out.put_nowait(packet)
                except queue.Full:
                    pass
    except Exception as exc:
        error = ("error", f"{type(exc).__name__}: {exc}")
        try:
            out.get_nowait()
        except queue.Empty:
            pass
        try:
            out.put_nowait(error)
        except queue.Full:
            pass
    finally:
        if "freenect" in locals():
            try:
                freenect.sync_stop()
            except Exception:
                pass


class Viewer(tk.Tk):
    def __init__(self, initial):
        super().__init__()
        self.title("Manifold / Kinect Depth Explorer")
        self.configure(bg="#edf4f8")
        self.geometry("710x580")
        self.stop_flag = threading.Event()
        self.latest = queue.Queue(maxsize=1)
        self.mode = [initial]
        self.image_bytes = None
        self.frame_id = None
        self.photo = tk.PhotoImage(width=320, height=240)
        tk.Label(self, text="KINECT DEPTH", font=("Sans", 19, "bold"),
                 bg="#edf4f8", fg="#183049").pack(anchor="w", padx=18, pady=(15, 3))
        tk.Label(self, text="1 Distance image  ·  2 Edges  ·  3 Motion  ·  S Save  ·  Q Close",
                 bg="#edf4f8", fg="#345268").pack(anchor="w", padx=18)
        self.canvas = tk.Canvas(self, bg="#142434", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=14)
        self.frame_id = self.canvas.create_image(0, 0, image=self.photo, anchor="center")
        self.canvas.bind("<Configure>", self.center_image)
        self.status = tk.StringVar(value="Starting your Kinect depth camera…")
        tk.Label(self, textvariable=self.status, bg="#edf4f8", fg="#183049",
                 font=("Sans", 11)).pack(anchor="w", padx=18, pady=(0, 16))
        self.bind("<Key>", self.on_key)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.worker = threading.Thread(target=produce,
                     args=(self.stop_flag, self.latest, self.mode),
                     daemon=True, name="kinect-depth-producer")
        self.worker.start()
        self.after(100, self.refresh)

    def center_image(self, _event=None):
        self.canvas.coords(self.frame_id, self.canvas.winfo_width() // 2,
                           self.canvas.winfo_height() // 2)

    def on_key(self, event):
        if event.keysym in ("Escape", "q", "Q"):
            self.close()
        elif event.char in "123":
            self.mode[0] = {"1": "depth", "2": "edges", "3": "motion"}[event.char]
            self.status.set("Showing " + self.mode[0] + ".")
        elif event.char.lower() == "s" and self.image_bytes:
            output = Path.home() / "Pictures" / "Manifold"
            output.mkdir(parents=True, exist_ok=True)
            target = output / ("kinect_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".ppm")
            target.write_bytes(self.image_bytes)
            self.status.set("Saved image: " + str(target))
            print("Saved image: " + str(target), flush=True)

    def refresh(self):
        newest = None
        try:
            while True:
                newest = self.latest.get_nowait()
        except queue.Empty:
            pass
        if newest:
            if newest[0] == "error":
                self.status.set("The Kinect cannot show an image. Check the details in Camera Lab.")
                print("Kinect depth error: " + newest[1], file=sys.stderr, flush=True)
            else:
                _, mode, ppm, created = newest
                self.image_bytes = ppm
                try:
                    self.photo.configure(data=ppm, format="PPM")
                    self.status.set("Live " + mode + "  ·  frame age " +
                                    str(round(1000 * (time.monotonic() - created))) + " ms")
                except tk.TclError as exc:
                    self.status.set("Image display problem. See Camera Lab details.")
                    print("Kinect display error: " + str(exc), file=sys.stderr, flush=True)
        if self.winfo_exists():
            self.after(100, self.refresh)

    def close(self):
        self.stop_flag.set()
        self.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("depth", "edges", "motion"), default="depth")
    args = parser.parse_args(argv)
    Viewer(args.mode).mainloop()


if __name__ == "__main__":
    main()
