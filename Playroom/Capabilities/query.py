"""Headless discovery of the same capabilities shown in Playroom's GUI.

Examples:
  python3 Playroom/Capabilities/query.py list
  python3 Playroom/Capabilities/query.py search "motion game"
  python3 Playroom/Capabilities/query.py show vision.nearest_depth_point

Outputs JSON only. Never executes commands, imports a device SDK, or opens a GUI.
"""
import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).with_name("catalog.json")
SEARCH_FIELDS = ("id", "name", "summary", "use_when", "keywords", "domain", "inputs", "outputs")
DETAIL_FIELDS = ("id", "name", "status", "summary", "use_when", "inputs", "outputs",
                 "requires", "reference", "source", "run_command", "notes")

def load():
    obj = json.loads(CATALOG.read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1 or not isinstance(obj.get("capabilities"), list):
        raise ValueError("Unsupported capability catalog")
    return obj["capabilities"]

def index(capabilities):
    return [{"id": c["id"], "name": c["name"], "status": c["status"],
             "use_when": c.get("use_when", c["summary"])} for c in capabilities]

def search(capabilities, words):
    # Match all query terms, in any order, across semantic descriptions.
    terms = words.casefold().split()
    return [c for c in capabilities if all(
        term in json.dumps({k: c.get(k) for k in SEARCH_FIELDS}, ensure_ascii=False).casefold()
        for term in terms)]

def detail(c):
    return {key: c[key] for key in DETAIL_FIELDS if key in c}

def main():
    parser = argparse.ArgumentParser(description="Discover Manifold capabilities; no execution")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("list")
    commands.add_parser("search").add_argument("terms")
    commands.add_parser("show").add_argument("id")
    args = parser.parse_args()
    capabilities = load()
    if args.action == "list":
        result = index(capabilities)
    elif args.action == "search":
        result = index(search(capabilities, args.terms))
    else:
        match = next((c for c in capabilities if c["id"] == args.id), None)
        if match is None:
            parser.error("unknown capability id: " + args.id)
        result = detail(match)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
