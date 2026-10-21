"""Interactive low-cost gravitational field playground. Tkinter + stdlib only.

Drag an attractor to move it, click empty space to add one. Space pauses.
The simulation is bounded deliberately for Raspberry Pi use.
"""
import math
import random
import tkinter as tk

W, H = 760, 500
DT = 0.035
MAX_PARTICLES = 48
MAX_ATTRACTORS = 5
FPS_MS = 40

class Playground(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold / Gravity Playground")
        self.resizable(False, False)
        self.canvas = tk.Canvas(self, width=W, height=H, bg="#0d1724", highlightthickness=0)
        self.canvas.pack()
        self.controls = tk.Frame(self)
        self.controls.pack(fill="x")
        self.strength = tk.Scale(self.controls, from_=100, to=2400, orient="horizontal",
                                 label="Attraction", length=220)
        self.strength.set(850)
        self.strength.pack(side="left")
        self.paused = False
        self.info = tk.Label(self.controls, text="Drag suns · Click empty space to add · Space pause · R reset · C clear trails")
        self.info.pack(side="left", padx=10)
        self.attractors = [[W * 0.5, H * 0.5]]
        self.dragging = None
        self.particles = []
        self.trails = []
        self.rng = random.Random(42)
        self.reset()
        # Allocate Canvas items once; move them instead of delete/create per frame.
        self.trail_ids = [
            self.canvas.create_line(0, 0, 0, 0, fill="#274d68", width=1, state="hidden")
            for _ in range(MAX_PARTICLES)
        ]
        self.particle_ids = [
            self.canvas.create_oval(0, 0, 0, 0, fill="#9de5fd", outline="")
            for _ in range(MAX_PARTICLES)
        ]
        self.attractor_ids = [
            self.canvas.create_oval(0, 0, 0, 0, fill="#ffbd5e",
                                    outline="#fff1b3", width=2, state="hidden")
            for _ in range(MAX_ATTRACTORS)
        ]
        self.status_id = self.canvas.create_text(
            10, 12, anchor="nw", fill="#a9bbc7", text="")
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "dragging", None))
        self.bind("<space>", self.toggle_pause)
        self.bind("r", lambda e: self.reset())
        self.bind("c", lambda e: self.clear_trails())
        self.after(FPS_MS, self.tick)

    def reset(self):
        self.attractors = [[W * 0.5, H * 0.5]]
        self.particles = []
        for i in range(MAX_PARTICLES):
            theta = self.rng.random() * 2 * math.pi
            radius = self.rng.uniform(65, 205)
            x = W * 0.5 + radius * math.cos(theta)
            y = H * 0.5 + radius * math.sin(theta)
            speed = math.sqrt(850 * 85 / max(30, radius))
            self.particles.append([x, y, -math.sin(theta) * speed, math.cos(theta) * speed])
        self.clear_trails()

    def clear_trails(self):
        self.trails = [[] for _ in self.particles]

    def toggle_pause(self, _event):
        self.paused = not self.paused

    def press(self, event):
        for i, (x, y) in enumerate(self.attractors):
            if (event.x - x) ** 2 + (event.y - y) ** 2 < 26 ** 2:
                self.dragging = i
                return
        if len(self.attractors) < MAX_ATTRACTORS:
            self.attractors.append([event.x, event.y])
            self.dragging = len(self.attractors) - 1

    def drag(self, event):
        if self.dragging is not None:
            self.attractors[self.dragging][:] = [max(0, min(W, event.x)),
                                                max(0, min(H, event.y))]

    def tick(self):
        if not self.winfo_exists():
            return
        if not self.paused:
            force = self.strength.get()
            for i, p in enumerate(self.particles):
                ax = ay = 0.0
                for sx, sy in self.attractors:
                    dx, dy = sx - p[0], sy - p[1]
                    r2 = dx * dx + dy * dy + 22 * 22
                    inv = force / (r2 * math.sqrt(r2))
                    ax += dx * inv
                    ay += dy * inv
                p[2] = (p[2] + ax * DT * 700) * 0.999
                p[3] = (p[3] + ay * DT * 700) * 0.999
                p[0] += p[2] * DT
                p[1] += p[3] * DT
                if p[0] < 3 or p[0] > W-3:
                    p[2] *= -0.8
                    p[0] = max(3, min(W-3, p[0]))
                if p[1] < 3 or p[1] > H-3:
                    p[3] *= -0.8
                    p[1] = max(3, min(H-3, p[1]))
                track = self.trails[i]
                track.append((p[0], p[1]))
                if len(track) > 7:
                    track.pop(0)
        for i, track in enumerate(self.trails):
            if len(track) > 1:
                self.canvas.coords(self.trail_ids[i], *(v for xy in track for v in xy))
                self.canvas.itemconfigure(self.trail_ids[i], state="normal")
            else:
                self.canvas.itemconfigure(self.trail_ids[i], state="hidden")
        for i, (sx, sy) in enumerate(self.attractors):
            self.canvas.coords(self.attractor_ids[i], sx-15, sy-15, sx+15, sy+15)
            self.canvas.itemconfigure(self.attractor_ids[i], state="normal")
        for i in range(len(self.attractors), MAX_ATTRACTORS):
            self.canvas.itemconfigure(self.attractor_ids[i], state="hidden")
        for i, (x, y, vx, vy) in enumerate(self.particles):
            self.canvas.coords(self.particle_ids[i], x-2, y-2, x+2, y+2)
        self.canvas.itemconfigure(
            self.status_id,
            text=f"{len(self.particles)} particles · {len(self.attractors)} attractors" +
                 (" · PAUSED" if self.paused else ""))
        self.after(FPS_MS, self.tick)

if __name__ == "__main__":
    Playground().mainloop()
