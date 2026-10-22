"""Kinect 1473 live nearest-point viewer.

Kinect acquisition runs in a daemon worker; Tk observes only the most recent
summary. This avoids creating/deleting canvas resources per frame.
Requires the existing working freenect+numpy environment, not a new install.
"""
import ctypes
import queue
import threading
import tkinter as tk
from pathlib import Path
from time import monotonic

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "AppOS/Native/build/libmcdepth.so"


class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_uint32), ("y", ctypes.c_uint32),
                ("depth", ctypes.c_uint16), ("valid", ctypes.c_uint8)]


def acquire(stop, latest):
    try:
        import freenect
        import numpy as np
        if not NATIVE.is_file():
            raise RuntimeError("Native depth library missing. Run: make -C AppOS/Native")
        lib = ctypes.CDLL(str(NATIVE))
        func = lib.mc_nearest_depth
        func.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.c_size_t,
                         ctypes.c_size_t, ctypes.POINTER(Point)]
        func.restype = ctypes.c_int
        while not stop.is_set():
            frame, _timestamp = freenect.sync_get_depth()
            if frame is None:
                continue
            if frame.dtype != np.uint16 or not frame.flags.c_contiguous:
                frame = np.ascontiguousarray(frame, dtype=np.uint16)
            h, w = frame.shape
            point = Point()
            result = func(frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                          w, h, ctypes.byref(point))
            if result:
                raise RuntimeError("Invalid dimensions from Kinect depth stream")
            value = ("depth", monotonic(), int(w), int(h), int(point.x),
                     int(point.y), int(point.depth), bool(point.valid))
            # The observer gets the latest state only; stale views are discarded.
            try:
                latest.put_nowait(value)
            except queue.Full:
                try:
                    latest.get_nowait()
                except queue.Empty:
                    pass
                try:
                    latest.put_nowait(value)
                except queue.Full:
                    pass
    except Exception as exc:
        try:
            latest.put_nowait(("error", str(exc)))
        except queue.Full:
            pass
    finally:
        if "freenect" in locals():
            try:
                freenect.sync_stop()
            except Exception:
                pass


class Viewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold / Kinect depth")
        self.geometry("760x565")
        self.configure(bg="#edf4f8")
        self.stop = threading.Event()
        self.latest = queue.Queue(maxsize=1)
        self.last_state = None
        self._point_bounds = None
        self._point_visible = False
        self._cross_geometry = None
        self._last_message = None
        self.message = tk.StringVar(value="Connecting to Kinect 1473…")
        tk.Label(self, text="KINECT / DEPTH POINT", bg="#edf4f8",
                 fg="#183049", font=("Sans", 18, "bold")).pack(anchor="w", padx=18, pady=(16, 3))
        tk.Label(self, text="Nearest valid depth sample · headless C analysis · latest-state presentation",
                 bg="#edf4f8", fg="#37506a").pack(anchor="w", padx=18)
        self.canvas = tk.Canvas(self, bg="#112236", highlightthickness=0,
                                width=720, height=420)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=16)
        self.cross_x = self.canvas.create_line(0, 0, 0, 0, fill="#42677d")
        self.cross_y = self.canvas.create_line(0, 0, 0, 0, fill="#42677d")
        self.point_id = self.canvas.create_oval(0, 0, 0, 0,
                        fill="#f9cf72", outline="#ffffff", width=2, state="hidden")
        self.label = tk.Label(self, textvariable=self.message, bg="#edf4f8",
                              fg="#183049", font=("Sans", 11))
        self.label.pack(anchor="w", padx=18, pady=(0, 18))
        self.worker = threading.Thread(target=acquire, args=(self.stop, self.latest),
                                       daemon=True, name="kinect-depth")
        self.worker.start()
        self.after(200, self.update_display)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def show_message(self, text):
        if text != self._last_message:
            self.message.set(text)
            self._last_message = text

    def update_display(self):
        value = None
        try:
            while True:
                value = self.latest.get_nowait()
        except queue.Empty:
            pass
        if value is not None and value != self.last_state:
            self.last_state = value
            if value[0] == "error":
                self.show_message("Capture error: " + value[1])
            else:
                _, stamp, width, height, x, y, depth, valid = value
                cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
                cross = (cw, ch)
                if cross != self._cross_geometry:
                    self.canvas.coords(self.cross_x, cw // 2, 0, cw // 2, ch)
                    self.canvas.coords(self.cross_y, 0, ch // 2, cw, ch // 2)
                    self._cross_geometry = cross
                if valid:
                    px, py = round(x * cw / width), round(y * ch / height)
                    bounds = (px-9, py-9, px+9, py+9)
                    if bounds != self._point_bounds:
                        self.canvas.coords(self.point_id, *bounds)
                        self._point_bounds = bounds
                    if not self._point_visible:
                        self.canvas.itemconfigure(self.point_id, state="normal")
                        self._point_visible = True
                    self.show_message(f"Nearest point ({x}, {y}) · raw depth {depth} · {monotonic()-stamp:.1f}s latency")
                else:
                    if self._point_visible:
                        self.canvas.itemconfigure(self.point_id, state="hidden")
                        self._point_visible = False
                    self.show_message("No valid depth sample")
        if self.winfo_exists():
            self.after(200, self.update_display)

    def close(self):
        self.stop.set()
        # USB read can block: do not stall the GUI while waiting for it.
        self.destroy()


if __name__ == "__main__":
    Viewer().mainloop()
