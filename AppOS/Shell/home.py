"""Manifold development shell: discover, launch, inspect and stop local applications.

Run from the repository root: python3 -m AppOS.Shell.home
This is an ordinary Tk window, not a compositor or security sandbox.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from AppOS.Runtime.catalog import discover
from AppOS.Latent.supervisor import Supervisor

BG = "#101923"
PANEL = "#1b2b3a"
FG = "#eaf3f7"
ACCENT = "#9de5fd"


class Home(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold / Console")
        self.geometry("930x590")
        self.minsize(740, 460)
        self.configure(bg=BG)
        self.supervisor = Supervisor()
        self.catalog = []
        self.selected_id = None
        self._last_status = None
        self._build()
        self.refresh_catalog()
        self.after(700, self.refresh_status)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _label(self, parent, text, size=12, color=FG):
        return tk.Label(parent, text=text, font=("DejaVu Sans", size),
                        bg=parent.cget("bg"), fg=color, anchor="w")

    def _build(self):
        top = tk.Frame(self, bg=BG, padx=24, pady=18)
        top.pack(fill="x")
        self._label(top, "MANIFOLD", 23, ACCENT).pack(anchor="w")
        self._label(top, "Home  /  Apps and capabilities", 11, "#a6b8c5").pack(anchor="w")
        body = tk.Frame(self, bg=BG, padx=24, pady=8)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=PANEL, padx=14, pady=14)
        left.pack(side="left", fill="both", expand=True)
        self._label(left, "AVAILABLE", 13, ACCENT).pack(anchor="w")
        self.app_list = tk.Listbox(left, bg=PANEL, fg=FG, selectbackground="#315874",
                                   selectforeground="#ffffff", relief="flat",
                                   highlightthickness=0, font=("DejaVu Sans", 13),
                                   exportselection=False)
        self.app_list.pack(fill="both", expand=True, pady=12)
        self.app_list.bind("<<ListboxSelect>>", self.choose)
        right = tk.Frame(body, bg=BG, padx=20)
        right.pack(side="left", fill="both", expand=True)
        self.detail = self._label(right, "Choose an application", 16)
        self.detail.pack(fill="x", pady=(20, 12))
        self.meta = self._label(right, "", 10, "#b7c9d4")
        self.meta.pack(fill="x")
        self.launch_btn = tk.Button(right, text="Launch selected", command=self.launch,
                                    bg="#315874", fg="white", relief="flat",
                                    padx=20, pady=12, state="disabled")
        self.launch_btn.pack(fill="x", pady=(30, 12))
        tk.Button(right, text="Rescan applications", command=self.refresh_catalog,
                  bg=PANEL, fg=FG, relief="flat", pady=9).pack(fill="x")
        self._label(right, "RUNNING", 13, ACCENT).pack(anchor="w", pady=(28, 5))
        self.running_list = tk.Listbox(right, bg=PANEL, fg=FG, selectbackground="#315874",
                                       exportselection=False, relief="flat", height=5,
                                       font=("DejaVu Sans", 11))
        self.running_list.pack(fill="both", expand=True)
        controls = tk.Frame(right, bg=BG)
        controls.pack(fill="x", pady=8)
        tk.Button(controls, text="Stop", command=lambda: self.stop(False),
                  bg=PANEL, fg=FG, relief="flat", padx=12).pack(side="left")
        tk.Button(controls, text="Force stop", command=lambda: self.stop(True),
                  bg=PANEL, fg=FG, relief="flat", padx=12).pack(side="left", padx=8)
        self.status = self._label(self, "Ready", 10, "#a6b8c5")
        self.status.configure(padx=24, pady=12)
        self.status.pack(fill="x")
        self.bind("<F5>", lambda _event: self.refresh_catalog())

    def refresh_catalog(self):
        self.catalog = discover()
        old = self.selected_id
        self.app_list.delete(0, "end")
        for app in self.catalog:
            self.app_list.insert("end", app["name"])
        index = next((i for i, app in enumerate(self.catalog) if app["id"] == old), None)
        if index is None and self.catalog:
            index = 0
        if index is not None:
            self.app_list.selection_set(index)
            self.app_list.activate(index)
        self.choose()
        self.status.configure(text=f"{len(self.catalog)} applications discovered  ·  F5 rescans")

    def choose(self, _event=None):
        selection = self.app_list.curselection()
        if not selection:
            self.selected_id = None
            self.detail.configure(text="No applications found")
            self.meta.configure(text="Add an appos.json manifest to a local app directory.")
            self.launch_btn.configure(state="disabled")
            return
        app = self.catalog[selection[0]]
        self.selected_id = app["id"]
        self.detail.configure(text=app["name"])
        self.meta.configure(text=f"{app['id']}\n{app.get('ui', {}).get('category', 'Application')}")
        self.launch_btn.configure(state="normal")

    def launch(self):
        match = next((a for a in self.catalog if a["id"] == self.selected_id), None)
        if match is None:
            return
        try:
            item = self.supervisor.launch(match)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Launch failed", str(exc), parent=self)
            return
        self.status.configure(text=f"Launched {item.name} (PID {item.proc.pid})")
        self.refresh_status()

    def _running_items(self):
        return [item for item in self.supervisor.apps if item.proc.poll() is None]

    def refresh_status(self):
        current = self._running_items()
        signature = tuple((item.proc.pid, item.name) for item in current)
        if signature != self._last_status:
            self.running_list.delete(0, "end")
            for item in current:
                self.running_list.insert("end", f"{item.name} · PID {item.proc.pid}")
            self._last_status = signature
        self.after(700, self.refresh_status)

    def stop(self, force):
        selection = self.running_list.curselection()
        current = self._running_items()
        if not selection or selection[0] >= len(current):
            return
        item = current[selection[0]]
        try:
            item.stop(force=force)
        except OSError as exc:
            messagebox.showerror("Stop failed", str(exc), parent=self)
            return
        self.status.configure(text=f"{'Killed' if force else 'Stop requested'}: {item.name}")
        self._last_status = None
        self.refresh_status()

    def close(self):
        running = self._running_items()
        if running:
            answer = messagebox.askyesnocancel(
                "Exit Manifold",
                f"{len(running)} app(s) still running.\n"
                "Yes: stop them and exit.\nNo: leave them running.\nCancel: stay.",
                parent=self)
            if answer is None:
                return
            if answer:
                for item in running:
                    item.stop()
        self.destroy()


def main():
    Home().mainloop()


if __name__ == "__main__":
    main()
