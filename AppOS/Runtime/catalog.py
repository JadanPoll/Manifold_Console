"""Discover applications from explicit manifests. No imports or execution during discovery."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "appos.json"

def discover(root=ROOT):
    found = []
    for path in sorted(Path(root).rglob(MANIFEST)):
        parts = path.relative_to(root).parts
        # Research checkouts are source references, not installed AppOS apps.
        # Their manifests must never enter Home's executable catalog.
        if any(part.startswith(".") for part in parts):
            continue
        if parts[:3] == ("Playroom", "Research_Campus", "external"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("schema_version") != 1:
                raise ValueError("unsupported schema_version")
            for key in ("id", "name", "entry"):
                if key not in data:
                    raise ValueError(f"missing {key}")
            cmd = data["entry"].get("command")
            if not isinstance(cmd, list) or not cmd or not all(isinstance(s, str) and s for s in cmd):
                raise ValueError("entry.command must be nonempty list of strings")
            if not isinstance(data["id"], str) or not data["id"]:
                raise ValueError("invalid id")
            if not isinstance(data["name"], str) or not data["name"]:
                raise ValueError("invalid name")
            data["_directory"] = str(path.parent)
            data["_manifest"] = str(path)
            found.append(data)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            print(f"Skipping {path}: {exc}")
    seen = set()
    unique = []
    for app in found:
        if app["id"] in seen:
            print(f"Skipping duplicate app id: {app['id']}")
            continue
        seen.add(app["id"])
        unique.append(app)
    return unique

if __name__ == "__main__":
    for app in discover():
        print(f"{app['id']}: {app['name']}")
