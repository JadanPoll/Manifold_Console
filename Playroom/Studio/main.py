"""No-code signal Playroom: visualize synthetic input, filtering, and pointer mapping."""
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import Signal, oscillator, clamp
from recipe import load as load_recipe, validate as validate_recipe
import json

class Playroom(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold · Playroom Studio")
        self.geometry("860x580")
        self.configure(bg="#eef4fa")
        self.wave = tk.StringVar(value="sine")
        self.rate = tk.DoubleVar(value=0.7)
        self.alpha = tk.DoubleVar(value=0.35)
        self.gain = tk.DoubleVar(value=1.0)
        self.running = True
        self.started = monotonic()
        self.signal = Signal()
        self.last = 0
        top = ttk.Frame(self, padding=14)
        top.pack(fill="x")
        ttk.Label(top, text="PLAYROOM / SIGNAL LAB", font=("Sans", 17, "bold")).pack(anchor="w")
        ttk.Label(top, text="No hardware needed. Change signal and filtering live; use the pointer below to test normalization.").pack(anchor="w")
        controls = ttk.Frame(self, padding=(14, 4))
        controls.pack(fill="x")
        ttk.Label(controls, text="Waveform").grid(row=0,column=0)
        ttk.Combobox(controls,textvariable=self.wave,values=("sine","square","triangle"),state="readonly",width=12).grid(row=1,column=0,padx=8)
        for col, (title, var, low, high) in enumerate((("Frequency",self.rate,.05,4),("EMA alpha",self.alpha,.05,1),("Gain",self.gain,.1,3)),start=1):
            ttk.Label(controls,text=title).grid(row=0,column=col)
            ttk.Scale(controls,variable=var,from_=low,to=high,orient="horizontal",length=155).grid(row=1,column=col,padx=8)
        ttk.Button(controls, text="Load Recipe", command=self.load_recipe_dialog).grid(row=1,column=4,padx=8)
        ttk.Button(controls, text="Paste Recipe", command=self.paste_recipe).grid(row=1,column=5,padx=8)
        ttk.Button(controls, text="Copy LLM Context", command=self.copy_context).grid(row=1,column=6,padx=8)
        self.canvas=tk.Canvas(self,bg="#101f34",height=290,highlightthickness=0)
        self.canvas.pack(fill="both",expand=True,padx=14,pady=10)
        self.canvas.bind("<Motion>",self.pointer)
        self.status=ttk.Label(self,text="Move pointer over the plot to inspect normalized input.",padding=14)
        self.status.pack(fill="x")
        self.protocol("WM_DELETE_WINDOW",self.destroy)
        self.after(33,self.frame)

    def paste_recipe(self):
        from tkinter import messagebox
        try:
            content = self.clipboard_get()
            if len(content.encode("utf-8")) > 8192:
                raise ValueError("Recipe exceeds 8 KiB")
            recipe = validate_recipe(json.loads(content))
            self.apply_recipe(recipe)
        except (ValueError, OSError, tk.TclError) as exc:
            messagebox.showerror("Invalid pasted recipe", str(exc))

    def copy_context(self):
        context = (
            "Generate ONLY a JSON object for Manifold Playroom Studio; no Markdown or code. "
            "Required exact fields: version=1 (integer), waveform one of sine/square/triangle, "
            "frequency number 0.05..4.0, gain number 0.1..3.0, smoothing number 0.05..1.0. "
            "Example: "
            + json.dumps(dict(version=1,waveform=self.wave.get(),frequency=round(self.rate.get(),3),
                              gain=round(self.gain.get(),3),smoothing=round(self.alpha.get(),3)))
            + " This recipe controls a synthetic signal only; it cannot access devices or execute code."
        )
        self.clipboard_clear()
        self.clipboard_append(context)
        self.status.config(text="LLM recipe context copied. Paste into chat; copy the returned JSON and select Paste Recipe.")

    def load_recipe_dialog(self):
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(title="Open Playroom recipe", filetypes=[("JSON recipe", "*.json")])
        if not path:
            return
        try:
            self.apply_recipe(load_recipe(path))
        except (ValueError, OSError) as exc:
            messagebox.showerror("Invalid recipe", str(exc))

    def apply_recipe(self, recipe):
        self.wave.set(recipe["waveform"])
        self.rate.set(recipe["frequency"])
        self.gain.set(recipe["gain"])
        self.alpha.set(recipe["smoothing"])
        self.signal = Signal(alpha=self.alpha.get())
        self.started = monotonic()
        self.status.config(text="Loaded validated recipe: " + recipe["waveform"])

    def pointer(self,e):
        width=max(1,self.canvas.winfo_width())
        height=max(1,self.canvas.winfo_height())
        self.status.config(text=f"Pointer: x={clamp(2*e.x/width-1):+.3f}  y={clamp(1-2*e.y/height):+.3f}  |  raw={self.last:+.3f}")

    def frame(self):
        if not self.winfo_exists():
            return
        now=monotonic()-self.started
        value=clamp(self.gain.get()*oscillator(now,self.rate.get(),self.wave.get()))
        if self.signal.filter.alpha!=self.alpha.get():
            self.signal.filter.alpha=self.alpha.get()
        self.signal.step(value)
        self.last=value
        c=self.canvas
        c.delete("all")
        w=max(100,c.winfo_width()); h=max(100,c.winfo_height())
        c.create_line(0,h/2,w,h/2,fill="#47617b",dash=(3,5))
        for series,color in ((self.signal.raw,"#77d8ff"),(self.signal.smooth,"#fbd36e")):
            samples=list(series)
            if len(samples)>1:
                coords=[]
                for i,v in enumerate(samples):
                    coords.extend((i*w/499.0, (1-clamp(v))*h/2))
                c.create_line(*coords,fill=color,width=2,smooth=False)
        c.create_text(14,15,text="BLUE: raw    GOLD: EMA-filtered",fill="white",anchor="w")
        self.after(33,self.frame)

if __name__=="__main__":
    Playroom().mainloop()
