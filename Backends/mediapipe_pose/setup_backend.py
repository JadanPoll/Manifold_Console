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
import signal
import time

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
RULES_JAVA_COMPAT = "7.12.2"
_ACTIVE = None

def _stop_child(_signum=None, _frame=None):
    global _ACTIVE
    child = _ACTIVE
    if child and child.poll() is None:
        try:
            os.killpg(child.pid, signal.SIGTERM)
            child.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    raise SystemExit(130)

signal.signal(signal.SIGTERM, _stop_child)
signal.signal(signal.SIGINT, _stop_child)

def run(argv, cwd=None):
    global _ACTIVE
    print("+", " ".join(map(str, argv)), flush=True)
    child = subprocess.Popen(list(map(str, argv)), cwd=cwd, start_new_session=True)
    _ACTIVE = child
    try:
        return subprocess.CompletedProcess(argv, child.wait())
    finally:
        _ACTIVE = None

def lock_holder(lock):
    """Return PID currently holding this exact lock file, if visible in /proc."""
    try:
        target = lock.resolve()
    except OSError:
        return None
    proc = Path("/proc")
    if not proc.is_dir():
        return None
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        fd_dir = entry / "fd"
        try:
            fds = list(fd_dir.iterdir())
        except OSError:
            continue
        for fd in fds:
            try:
                if fd.resolve() == target:
                    return int(entry.name)
            except OSError:
                continue
    return None

def recover_git_lock():
    lock = CACHE / ".git/index.lock"
    if not lock.exists():
        return
    holder = lock_holder(lock)
    if holder:
        print("A previous MediaPipe download is still finishing; waiting for it to release the source tree…", flush=True)
        for _ in range(30):
            time.sleep(1)
            if not lock.exists():
                return
            if lock_holder(lock) is None:
                break
        if lock.exists() and lock_holder(lock):
            raise SystemExit(
                "The previous MediaPipe setup is still using the source tree. "
                "Close that setup or wait a moment, then press Set up body tracking again."
            )
    if lock.exists():
        print("Recovering from an interrupted earlier setup…", flush=True)
        lock.unlink()

def command(name):
    return shutil.which(name)

def capture(argv, cwd=None):
    return subprocess.check_output(list(map(str, argv)), cwd=cwd, text=True).strip()


def atomic_install(source, target, mode):
    """Replace a Bazel artifact without inheriting Bazel's read-only mode."""
    source = Path(source)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".installing")
    tmp.unlink(missing_ok=True)
    try:
        shutil.copyfile(source, tmp)
        tmp.chmod(mode)
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)

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
    recover_git_lock()
    if run(["git", "fetch", "--depth", "1", "origin", PIN], CACHE).returncode:
        raise SystemExit("Could not fetch pinned MediaPipe revision.")
    if run(["git", "checkout", "--detach", PIN], CACHE).returncode:
        raise SystemExit("Could not select pinned MediaPipe revision.")

def apply_build_compatibility_patches():
    """Minimal build-only compatibility patches for the pinned upstream tree."""
    module = CACHE / "MODULE.bazel"
    text = module.read_text(encoding="utf-8")
    old = 'bazel_dep(name = "rules_java", version = "7.10.0")'
    old_override = 'module_name = "rules_java",\n    version = "7.10.0",'
    if old in text:
        print("Applying Bazel Java-toolchain compatibility fix (rules_java 7.10.0 -> "
              + RULES_JAVA_COMPAT + ")…", flush=True)
        text = text.replace(old,
            'bazel_dep(name = "rules_java", version = "' + RULES_JAVA_COMPAT + '")')
        text = text.replace(old_override,
            'module_name = "rules_java",\n    version = "' + RULES_JAVA_COMPAT + '",')
        module.write_text(text, encoding="utf-8")


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

def patch_litert_for_gcc(bazel):
    """Keep the existing GCC build cache; patch LiteRT's Clang-style ARM target."""
    # Materialize external repositories without compiling.
    fetched = run([bazel, "fetch", "//manifold:libmanifold_pose.so"], CACHE)
    if fetched.returncode:
        raise SystemExit("Could not prepare MediaPipe dependencies for compilation.")

    output_base = Path(capture([bazel, "info", "output_base"], CACHE))
    candidates = list((output_base / "external").glob(
        "*litert*/tflite/kernels/internal/optimized/4bit/neon_fully_connected_*_sdot.cc"
    ))
    if not candidates:
        raise SystemExit(
            "LiteRT source was prepared, but the ARM dot-product kernel could not be located."
        )

    changed = 0
    for source in candidates:
        text = source.read_text(encoding="utf-8")
        old = '__attribute__((target("dotprod")))'
        new = '__attribute__((target("+dotprod")))'
        if old in text:
            source.write_text(text.replace(old, new), encoding="utf-8")
            changed += 1
    if changed:
        print("Applied ARM/GCC compatibility fix to LiteRT dot-product kernel.", flush=True)
    else:
        print("LiteRT ARM/GCC compatibility fix already present.", flush=True)


def patch_kleidiai_for_gcc(bazel):
    """Work around a GCC 12 AArch64 vectorizer ICE in one KleidiAI BF16 packer."""
    if platform.machine().lower() not in ("aarch64", "arm64"):
        return
    gcc = command("gcc")
    if not gcc:
        return
    try:
        version = capture([gcc, "-dumpfullversion"])
    except (OSError, subprocess.CalledProcessError):
        version = ""
    if not version.startswith("12."):
        return

    output_base = Path(capture([bazel, "info", "output_base"], CACHE))
    matches = list((output_base / "external").glob(
        "KleidiAI*/kai/ukernels/matmul/pack/kai_lhs_quant_pack_qai8dxp_bf16_neon.c"
    ))
    for source in matches:
        text = source.read_text(encoding="utf-8")
        pragma = '#pragma GCC optimize("no-tree-vectorize")\n'
        if pragma not in text:
            source.write_text(pragma + text, encoding="utf-8")
            print("Applied Raspberry Pi GCC 12 compatibility fix to KleidiAI BF16 packer.", flush=True)
        else:
            print("KleidiAI GCC 12 compatibility fix already present.", flush=True)


def patch_compile_time_string_for_gcc():
    """GCC 12 needs the structural NTTP object to be copy-constructible."""
    if platform.machine().lower() not in ("aarch64", "arm64"):
        return
    gcc = command("gcc")
    if not gcc:
        return
    try:
        version = capture([gcc, "-dumpfullversion"])
    except (OSError, subprocess.CalledProcessError):
        return
    if not version.startswith("12."):
        return

    source = CACHE / "mediapipe/framework/deps/compile_time_string.h"
    if not source.is_file():
        return
    text = source.read_text(encoding="utf-8")
    old = "CompileTimeString(const CompileTimeString&) = delete;"
    new = "constexpr CompileTimeString(const CompileTimeString&) = default;"
    if old in text:
        source.write_text(text.replace(old, new), encoding="utf-8")
        print("Applied GCC 12 compatibility fix to MediaPipe compile-time strings.", flush=True)
    elif new in text:
        print("MediaPipe compile-time string compatibility fix already present.", flush=True)


def patch_opencv_soname():
    """MediaPipe's OpenCV 4.10 source rule expects .so.4.10; OpenCV emits .so.410."""
    build_file = CACHE / "third_party/BUILD"
    if not build_file.is_file():
        return
    text = build_file.read_text(encoding="utf-8")
    old = 'OPENCV_SO_VERSION = "4.10"'
    new = 'OPENCV_SO_VERSION = "410"'
    if old in text:
        build_file.write_text(text.replace(old, new), encoding="utf-8")
        print("Corrected OpenCV 4.10 Linux SONAME expectation (.so.410).", flush=True)
    elif new in text:
        print("OpenCV SONAME compatibility fix already present.", flush=True)


def build():
    bazel = ensure_bazelisk()
    patch_litert_for_gcc(bazel)
    patch_kleidiai_for_gcc(bazel)
    patch_compile_time_string_for_gcc()
    patch_opencv_soname()
    result = run([
        bazel, "build",
        "--define", "MEDIAPIPE_DISABLE_GPU=1",
        "--define", "OPENCV=source",
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
    atomic_install(product, INSTALL / product.name, 0o755)

    # The OPENCV=source build produces private runtime libraries inside Bazel.
    # Install them beside libmanifold_pose.so so Manifold does not depend on
    # system-wide OpenCV development/runtime packages.
    opencv_libdir = CACHE / "bazel-bin/third_party/opencv_cmake/lib"
    copied_opencv = []
    if opencv_libdir.is_dir():
        for source in sorted(opencv_libdir.glob("libopencv_*.so*")):
            if source.is_file() or source.is_symlink():
                target = INSTALL / source.name
                atomic_install(source.resolve(), target, 0o755)
                copied_opencv.append(str(target))
    if not copied_opencv:
        raise SystemExit(
            "Native Pose built, but its private OpenCV runtime libraries were not found."
        )

    atomic_install(HERE / "include/manifold_pose.h", INCLUDE / "manifold_pose.h", 0o644)
    state = {
        "backend": "mediapipe",
        "upstream_revision": PIN,
        "architecture": platform.machine(),
        "library": str(INSTALL / product.name),
        "header": str(INCLUDE / "manifold_pose.h"),
        "model": str(MODEL) if MODEL.is_file() else None,
        "runtime_libraries": copied_opencv,
    }
    state_path = INSTALL / "pose_backend.json"
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print("\nNative Pose backend installed.")
    print("Library:", state["library"])
    print("Bundled OpenCV runtime:", len(copied_opencv), "library file(s)")
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
    apply_build_compatibility_patches()
    install_overlay()
    ensure_model(args.download_model)
    if not args.source_only:
        build()

if __name__ == "__main__":
    main()
