"""Explore qualified Manifold capabilities without loading device SDKs."""
import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
import webbrowser

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).with_name("catalog.json")
STATUSES = ("All", "working", "hardware-verified", "research", "idea")

def read_catalog(path=CATALOG):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1 or not isinstance(obj.get("capabilities"), list):
        raise ValueError("Unsupported catalog")
    ids = set()
    for c in obj["capabilities"]:
        if c["id"] in ids or c["status"] not in STATUSES[1:]:
            raise ValueError("Duplicate id or unknown status")
        if c["demo"].get("kind") not in ("none", "local", "manual"):
            raise ValueError("Unknown demo kind")
        ids.add(c["id"])
    return obj["capabilities"]

def search(capabilities, query="", status="All"):
    needle = query.casefold().strip()
    return [c for c in capabilities if
            (status == "All" or c["status"] == status) and
            needle in " ".join(str(c.get(k,"")) for k in ("name","summary","domain","id","use_when","keywords","inputs","outputs")).casefold()]

def agent_context(c):
    fields = ("id","name","status","summary","use_when","keywords","inputs","outputs","requires","reference","source","run_command","notes")
    return json.dumps({k:c[k] for k in fields if k in c}, indent=2)

class Browser(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manifold / Capability Browser")
        self.geometry("1030x650")
        self.configure(bg="#e8f1f8")
        self.capabilities = read_catalog()
        self.entries = []
        self.selected = None
        header = ttk.Frame(self, padding=14)
        header.pack(fill="x")
        ttk.Label(header,text="CAPABILITIES",font=("Sans",19,"bold")).pack(anchor="w")
        ttk.Label(header,text="Search by problem, purpose, or technique. Select a capability to recover how to use it.").pack(anchor="w")
        filters = ttk.Frame(self,padding=(14,0,14,12))
        filters.pack(fill="x")
        self.query=tk.StringVar()
        ttk.Entry(filters,textvariable=self.query,width=42).pack(side="left",padx=(0,10))
        self.status=tk.StringVar(value="All")
        ttk.Combobox(filters,textvariable=self.status,values=STATUSES,state="readonly",width=20).pack(side="left")
        self.query.trace_add("write",lambda *_:self.populate())
        self.status.trace_add("write",lambda *_:self.populate())
        content=ttk.Panedwindow(self,orient="horizontal")
        content.pack(fill="both",expand=True,padx=14,pady=8)
        left=ttk.Frame(content,padding=8)
        right=ttk.Frame(content,padding=8)
        content.add(left,weight=2)
        content.add(right,weight=3)
        self.listbox=tk.Listbox(left,font=("Sans",12),exportselection=False)
        self.listbox.pack(fill="both",expand=True)
        self.listbox.bind("<<ListboxSelect>>",self.select)
        self.details=tk.Text(right,wrap="word",font=("Sans",11),height=20)
        self.details.pack(fill="both",expand=True)
        buttons=ttk.Frame(right,padding=(0,12))
        buttons.pack(fill="x")
        ttk.Button(buttons,text="Copy LLM reference",command=self.copy_reference).pack(side="left",padx=4)
        ttk.Button(buttons,text="Copy run command",command=self.copy_command).pack(side="left",padx=4)
        ttk.Button(buttons,text="Open source",command=self.open_source).pack(side="left",padx=4)
        ttk.Button(buttons,text="Launch demo",command=self.launch_demo).pack(side="left",padx=4)
        self.populate()

    def populate(self):
        self.entries=search(self.capabilities,self.query.get(),self.status.get())
        self.listbox.delete(0,tk.END)
        for c in self.entries:
            self.listbox.insert(tk.END,f"{c['name']}  [{c['status']}]")
        self.selected=None
        self.details.delete("1.0",tk.END)
        if self.entries:
            self.listbox.selection_set(0)
            self.select()

    def select(self,event=None):
        picks=self.listbox.curselection()
        if not picks:
            return
        self.selected=self.entries[picks[0]]
        c=self.selected
        lines=[c["name"],c["status"].upper(),"",c["summary"],"",
               "Use when: "+c.get("use_when", "Explore this capability"),"",
               "Domains: "+", ".join(c["domain"]),
               "Inputs: "+", ".join(c["inputs"]),
               "Outputs: "+", ".join(c["outputs"]),
               "Needs: "+(", ".join(c["requires"]) or "None"),"",
               "Source: "+c["source"],
               "Reference: "+c["reference"],"",
               "How to run: "+self.run_instructions(c),"",
               "Limitations: "+c["notes"]]
        self.details.delete("1.0",tk.END)
        self.details.insert("1.0","\n".join(lines))

    @staticmethod
    def run_instructions(c):
        command = c.get("run_command")
        if command:
            return command
        if c["demo"]["kind"] == "local":
            return "Use Launch demo (if available)."
        if c["demo"]["kind"] == "manual":
            return "See reference for hardware-specific setup."
        return "No runnable demonstration yet."

    def copy_command(self):
        if self.selected is None: return
        command = self.selected.get("run_command")
        if not command:
            messagebox.showinfo("Run command", "No documented run command for this capability.")
            return
        self.clipboard_clear()
        self.clipboard_append(command)

    def copy_reference(self):
        if self.selected is None:return
        self.clipboard_clear()
        self.clipboard_append(agent_context(self.selected))
        messagebox.showinfo("LLM context","Compact capability reference copied.")

    def open_source(self):
        if self.selected is None:return
        source=self.selected["source"]
        if source.startswith("https://github.com/"):
            webbrowser.open(source)
        else:
            local = (ROOT / source).resolve()
            if not local.is_relative_to(ROOT) or not local.is_file():
                messagebox.showerror("Source unavailable", "Local source is missing or outside the repository.")
                return
            webbrowser.open(local.as_uri())

    def launch_demo(self):
        if self.selected is None:return
        demo=self.selected["demo"]
        if demo["kind"] != "local":
            messagebox.showinfo("Not launchable","This capability is documented, but no browser-run demo is available.")
            return
        # Only exact hardcoded commands in the trusted checked-in catalog;
        # never run instructions pasted from a model or external research entry.
        allowed = {
            "signal.synthetic": ("Playroom/Studio/main.py", ["python3", "Playroom/Studio/main.py"]),
            "play.gravity_field": ("Playroom/Playground/gravity.py", ["python3", "Playroom/Playground/gravity.py"]),
        }
        expected = allowed.get(self.selected["id"])
        if expected is None or demo["command"] != expected[1]:
            messagebox.showerror("Blocked","Demo command is not in the local allowlist.")
            return
        try:
            subprocess.Popen([sys.executable, str(ROOT / expected[0])], cwd=ROOT)
        except OSError as exc:
            messagebox.showerror("Launch failed",str(exc))

if __name__=="__main__":
    Browser().mainloop()
