"""Fetch optional legacy research repositories; never run their code or pip installs.

No submodules: clones belong to a local ignored working directory.
"""
import argparse
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "projects.json"
WORKTREES = HERE / "external"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true",
                        help="clone absent repos or fast-forward existing repos")
    args = parser.parse_args()
    data = json.loads(SOURCES.read_text(encoding="utf-8"))
    for project in data["projects"]:
        target = WORKTREES / project["directory"]
        if not args.fetch:
            status = "cloned" if (target / ".git").is_dir() else "not cloned"
            print(f'{project["name"]}: {status} ({target})')
            continue
        WORKTREES.mkdir(parents=True, exist_ok=True)
        if (target / ".git").is_dir():
            subprocess.run(["git", "-C", str(target), "pull", "--ff-only"], check=True)
        elif target.exists():
            raise SystemExit(f"Refusing to overwrite non-git directory: {target}")
        else:
            subprocess.run(["git", "clone", "--", project["repository"], str(target)], check=True)
        print(f'Synced: {project["name"]}')
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
