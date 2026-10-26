#!/usr/bin/env python3
"""Build/install the Manifold MediaPipe pose backend in user space.

No sudo. No system package changes. Expensive source compilation happens only
when explicitly invoked by the user.
"""
from pathlib import Path
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import hashlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PIN = (HERE / "PINNED_MEDIAPIPE.txt").read_text().splitlines()[-1].strip()
CACHE = Path.home() / ".cache/manifold/mediapipe-src"
INSTALL = Path.home() / ".local/lib/manifold"
INCLUDE = Path.home() / ".local/include/manifold"
MODEL = Path.home() / ".local/share/manifold/models/pose_landmarker_lite.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_lite/float16/1/pose_landmarker_lite.task")
BAZELISK_VERSION = "v1.30.0"

def run(argv, cwd=None):
    print("+", " ".join(map(str, argv)), flush=True)
    return subprocess.run(list(map(str, argv)), cwd=cwd, check=False)

def command(name):
    return shutil.which(name)

def ensure_bazelisk():
    existing = command("bazelisk") or command("bazel")
    if existing:
        return existing
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("aarch64", "arm64") else "amd64" if machine in ("x86_64", "amd64") else None
    if not arch:
        raise SystemExit("Native Pose does not yet have an automatic Bazelisk setup for " + machine)
    bindir = Path.home() / ".local/bin"
    bindir.mkdir(parents=True, exist_ok=True)
    target = bindir / "bazelisk"
    base = f"https://github.com/bazelbuild/bazelisk/releases/download/{BAZELISK_VERSION}/bazelisk-linux-{arch}"
    print("Preparing the user-space build tool…", flush=True)
    with urllib.request.urlopen(base + ".sha256", timeout=30) as response:
        expected = response.read().decode().strip().split()[0]
    tmp = target.with_suffix(".part")
    try:
        urllib.request.urlretrieve(base, tmp)
        actual = hashlib.sha256(tmp.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit("Downloaded Bazelisk checksum did not match.")
        tmp.chmod(0o755)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return str(target)

def ensure_source():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not (CACHE / ".git").is_dir():
        if CACHE.exists():
            raise SystemExit("MediaPipe cache exists but is not a Git checkout: " + str(CACHE))
        if run(["git", "clone", "https://github.com/google-ai-edge/mediapipe.git", CACHE]).returncode:
            raise SystemExit("Could not download MediaPipe source.")
    if run(["git", "fetch", "--depth", "1", "origin", PIN], CACHE).returncode:
        raise SystemExit("Could not fetch pinned MediaPipe revision.")
    if run(["git", "checkout", "--detach", PIN], CACHE).returncode:
        raise SystemExit("Could not select pinned MediaPipe revision.")

def install_overlay():
    target = CACHE / "manifold"
    target.mkdir(exist_ok=True)
    shutil.copy2(HERE / "include/manifold_pose.h", target / "manifold_pose.h")
    shutil.copy2(HERE / "src/manifold_pose.cc", target / "manifold_pose.cc")
    shutil.copy2(HERE / "overlay/BUILD.bazel", target / "BUILD.bazel")

def ensure_model(download):
    if MODEL.is_file():
        return
    if not download:
        print("Pose model not installed yet:", MODEL)
        return
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    tmp = MODEL.with_suffix(".task.part")
    print("Downloading the official Pose Landmarker Lite model…", flush=True)
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp)
        tmp.replace(MODEL)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise SystemExit("Could not download pose model: " + str(exc))

def build():
    bazel = ensure_bazelisk()
    result = run([
        bazel, "build",
        "--define", "MEDIAPIPE_DISABLE_GPU=1",
        "--copt=-O3",
        "//manifold:libmanifold_pose.so"
    ], CACHE)
    if result.returncode:
        raise SystemExit("MediaPipe build stopped with an error above.")
    product = CACHE / "bazel-bin/manifold/libmanifold_pose.so"
    if not product.is_file():
        raise SystemExit("Build reported success but libmanifold_pose.so was not found.")

    INSTALL.mkdir(parents=True, exist_ok=True)
    INCLUDE.mkdir(parents=True, exist_ok=True)
    shutil.copy2(product, INSTALL / product.name)
    shutil.copy2(HERE / "include/manifold_pose.h", INCLUDE / "manifold_pose.h")
    state = {
        "backend": "mediapipe",
        "upstream_revision": PIN,
        "architecture": platform.machine(),
        "library": str(INSTALL / product.name),
        "header": str(INCLUDE / "manifold_pose.h"),
        "model": str(MODEL) if MODEL.is_file() else None,
    }
    state_path = INSTALL / "pose_backend.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print("\nNative Pose backend installed.")
    print("Library:", state["library"])
    if state["model"]:
        print("Model:", state["model"])
    else:
        print("Backend is built; model can be downloaded separately.")

def status():
    lib = INSTALL / "libmanifold_pose.so"
    print("Native Pose backend:", "ready" if lib.is_file() else "not built")
    print("Pose model:", "ready" if MODEL.is_file() else "not downloaded")
    print("Pinned MediaPipe:", PIN)
    print("Source cache:", CACHE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--download-model", action="store_true")
    parser.add_argument("--source-only", action="store_true",
                        help="fetch pinned source and install Manifold overlay, but do not compile")
    args = parser.parse_args()
    if args.status:
        status()
        return
    if not command("git"):
        raise SystemExit("Git is required to obtain MediaPipe source.")
    ensure_source()
    install_overlay()
    ensure_model(args.download_model)
    if not args.source_only:
        build()

if __name__ == "__main__":
    main()
