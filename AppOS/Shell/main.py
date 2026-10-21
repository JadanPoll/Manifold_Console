"""Minimal Wii-inspired app channel launcher, standard-library Tk GUI."""
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from AppOS.Runtime.catalog import discover
from AppOS.Latent.supervisor import Supervisor, host_memory

class Shell(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold Console · Dev Shell")
        self.geometry("920x580")
        self.configure(bg="#e8f1f8")
        self.apps=discover(ROOT)
        self.index=0
        self.children=[]
        self.latent=Supervisor()
        self.heading=tk.Label(self,text="MANIFOLD  /  CHANNELS",font=("Sans",22,"bold"),bg="#e8f1f8",fg="#19384d")
        self.heading.pack(pady=(32,8))
        tk.Label(self,text="Arrows to navigate  ·  Enter to launch  ·  R to refresh  ·  Escape to close",bg="#e8f1f8",fg="#47617b").pack()
        self.grid_frame=tk.Frame(self,bg="#e8f1f8")
        self.grid_frame.pack(expand=True,fill="both",padx=35,pady=30)
        self.status=tk.Label(self,text="",bg="#e8f1f8",fg="#47617b")
        self.status.pack(pady=12)
        bar=tk.Frame(self,bg="#e8f1f8")
        bar.pack(fill="x",padx=35)
        self.telemetry=tk.Label(bar,text="Latent: starting",bg="#e8f1f8",fg="#47617b")
        self.telemetry.pack(side="left",expand=True,fill="x")
        tk.Button(bar,text="Stop latest",command=lambda:self.stop_latest(False)).pack(side="right")
        tk.Button(bar,text="Kill latest",command=lambda:self.stop_latest(True)).pack(side="right")
        self.after(1000,self.refresh_latent)
        self.bind("<Left>",lambda _:self.move(-1))
        self.bind("<Right>",lambda _:self.move(1))
        self.bind("<Return>",lambda _:self.open_selected())
        self.bind("<r>",lambda _:self.refresh())
        self.bind("<Escape>",lambda _:self.destroy())
        self.draw()

    def refresh(self):
        self.apps=discover(ROOT)
        self.index=0
        self.draw()

    def move(self,delta):
        if self.apps:
            self.index=(self.index+delta)%len(self.apps)
            self.draw()

    def open_selected(self):
        if not self.apps:
            return
        app=self.apps[self.index]
        try:
            managed=self.latent.launch(app)
            self.children.append(managed)
            self.status.config(text=f"Launched {app['name']} (PID {managed.proc.pid}); lower priority, NOT sandboxed.")
        except (OSError,ValueError) as exc:
            messagebox.showerror("Launch failed",str(exc))

    def stop_latest(self, force):
        running=[item for item in self.children if item.proc.poll() is None]
        if running:
            running[-1].stop(force)
            self.status.config(text=("Killed " if force else "Requested stop of ")+running[-1].name)

    def refresh_latent(self):
        available,total=host_memory()
        memory=f"{available//1048576} MiB available" if available is not None else "memory unknown"
        running=[item.snapshot() for item in self.children if item.proc.poll() is None]
        report=", ".join("{} {} MiB".format(x["name"],(x["rss"] or 0)//1048576) for x in running)
        self.telemetry.config(text="Latent | "+memory+" | "+(report or "no managed apps"))
        self.after(1000,self.refresh_latent)

    def draw(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        if not self.apps:
            tk.Label(self.grid_frame,text="No apps found. Add an appos.json manifest.",bg="#e8f1f8").pack()
            return
        for i,app in enumerate(self.apps):
            border="#50a9dd" if i==self.index else "#c2d7e5"
            tile=tk.Frame(self.grid_frame,bg=border,padx=3,pady=3)
            tile.grid(row=i//3,column=i%3,padx=12,pady=12,sticky="nsew")
            btn=tk.Button(tile,text=app["name"]+"\n\n"+app["id"],font=("Sans",12,"bold"),
                          bg="#ffffff",fg="#19384d",wraplength=185,width=22,height=6,
                          command=lambda j=i:self.activate(j),relief="flat")
            btn.pack(fill="both",expand=True)
        for col in range(3):
            self.grid_frame.columnconfigure(col,weight=1)
    def activate(self,i):
        self.index=i
        self.open_selected()

if __name__=="__main__":
    Shell().mainloop()
