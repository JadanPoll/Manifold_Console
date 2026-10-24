# Recursive Combinatorial Exploration — Manifold Vision Boundary

**Scope:** current Home application-manifest discovery, optional Research
checkouts, the optional MediaPipe pose viewer, independently tested native
motion kernel, and the **not-yet-implemented** Connect runtime.

This is a **model of code structure and admissible behavior**, not hardware
execution, a vulnerability exploit, or performance measurement.

## 1. Abstraction and scope justification (depth 0)

See [model.py](model.py) for the explicit eight-node inventory (English
labels, local states and responsibilities) and the full **8 × 8** ordered-pair
audit. The audit is executable and generates
[`matrix_depth0.csv`](matrix_depth0.csv). Labels mean:

- **A:** directly admissible in reviewed code;
- **C:** conditional on another state, a user action or device behavior;
- **I:** no such direct transition in the reviewed code and scoped model;
- **U:** insufficient evidence, deliberately omitted from any conclusion.

The nodes are Operator (U), Research checkout (R), manifest scanner (C),
Home supervisor (H), device source (D), Pose viewer (P), native motion kernel
(M) and Connect (X). This selection spans discovery, execution, sensing,
interpretation and composition. It excludes Voice, game-specific control,
kernel drivers, unrelated applications and the rest of the repository.

**Dependency/higher-order relationship:** execution of an unreviewed
Research manifest requires the **conjunction** of (i) a checkout containing
`appos.json`, (ii) recursive scanner admission, (iii) a user's selection,
and (iv) launch of the selected command. The pairwise matrix alone does not
establish this reachable path.

Evidence:
- [AppOS/Runtime/catalog.py](../../AppOS/Runtime/catalog.py): recursive
  `rglob("appos.json")`, filters after path discovery. Previously ignored
  dot-prefixed paths but not the Research `external` tree.
- [Playroom/Research_Campus/sync_research.py](../../Playroom/Research_Campus/sync_research.py):
  cloned source checkouts are placed below `external/`.
- [AppOS/Shell/home.py](../../AppOS/Shell/home.py) and
  [AppOS/Latent/supervisor.py](../../AppOS/Latent/supervisor.py):
  a user-selected manifest supplies a child command. No sandbox guarantee.
- [Packages/vision.pose.mediapipe/pose_viewer.py](../../Packages/vision.pose.mediapipe/pose_viewer.py):
  acquisition, `detect_for_video`, drawing and `imshow/waitKey` are
  synchronous in one process, launched via CLI rather than Home.
- [Packages/motion.landmarks/motion.c](../../Packages/motion.landmarks/motion.c):
  independent C11 kernel not called by pose viewer.
- [AppOS/Contracts/CAPABILITY_CHAPTERS.md](../../AppOS/Contracts/CAPABILITY_CHAPTERS.md):
  Connect runtime and interprocess routing explicitly not implemented.

The source fixes below were made after identifying the first path. The
model's `legacy` mode describes the earlier scanner admission behavior;
the second mode includes the new exclusion.

## 2. Refinement and stopping decisions

For **every** depth-0 node the source records a refine/stop decision in
`STOP`. Pose viewer **P** is refined one level:

```text
P
├── Acq: OpenCV acquisition
├── Infer: synchronous MediaPipe Tasks inference
└── Draw: skeleton overlay and UI event pumping
```

The complete depth-1 **3 × 3** ordered-pair matrix is generated as
[`matrix_pose_depth1.csv`](matrix_pose_depth1.csv). The stop boundary is the
application thread: MediaPipe calculator internals, GPU, and camera drivers
are not modeled; their implementation details are unnecessary to establish
that this top-level call sequence is synchronous. Further refinement would
be required before claiming a MediaPipe-internal or driver-specific cause.

## 3. States, events and knowledge

The executable model stores a finite tuple:

`(research, catalog, operator_belief, app, device, inference, view, age)`.

There is one **actual** Research/catalog/application state, distinct from
the operator's possibly false belief that a listing is trusted. The model
includes normal launch, benign and manifest-bearing checkouts, catalog
rescan, explicit user selection, forgetting, dependency failure, pose capture,
inference delay/completion, application error, exit/retry and stop.

Environment-dependent events are alternatives, **not observations**:
the cloned checkout may or may not contain a manifest; the pose runtime may
or may not have working model and camera dependencies. Delays are modeled as
zero, one or two logical ticks, not elapsed seconds. Nondeterminism is
intentional. Physical USB ownership, multiprocessing and camera contention
are unresolved and excluded from the claims.

## 4. Obligations and failure sets

**F1 — unreviewed manifest executed:** the Research folder is for source
inspection, not installation. For this scope, a nested `appos.json` in an
external Research checkout should not be admitted to Home's executable
catalog. This is a **conditional trust-boundary defect** in old discovery
behavior, not evidence of automatic remote code execution or root access.
The actor must explicitly launch a discovered command.

**F2 — blocking inference over budget:** the proposed v1 temporal-independence
axiom requires slow computation not to stall acquisition/presentation.
The present pose viewer is a standalone synchronous demo and makes no such
guarantee. Therefore this is a **v1 architectural gap**, *not* proof of
a runtime fault or observed latency violation. The two logical delay
ticks are symbolic, not a calibrated deadline.

**Not failures:** absent MediaPipe dependencies, a manually stopped app,
failed camera access, or Connect being listed as research-only. They are
allowed operating states, not violations of existing contracts.

## 5. Actually computed reachability and shortest traces

The breadth-first search runs on **abstract state labels**, not Manifold APIs.
Each distinct state is enqueued once. A predecessor pointer records the
first discovery of each state. With a 100,000-state safety limit:

| Audit | Reachable states | Checked labeled transitions | Max shortest depth | Witnesses |
|---|---:|---:|---:|---|
| Original external-folder admission | 44 | 172 | 7 | F1, F2 |
| Exclude Research external folder | 42 | 167 | 7 | F2 only |

Shortest witnesses measured in **event transitions**:

```text
F1 (4): initial
  → clone:contains_appos_manifest
  → rescan_catalog
  → user_sees_listing_as_trusted
  → user_launches_external_manifest [unreviewed command runs]

F2 (4): initial
  → cli_pose:available
  → next_frame_begin_inference
  → inference_delay_tick
  → inference_delay_tick [viewer remains blocked]
```

F1 needs both the manifest-bearing clone and voluntary launch; it is not
unconditional. F2 demonstrates that **the synchronous topology permits**
a stall if inference is delayed, not its probability, physical duration or
severity on a particular device.

The inspected test implementation uses Python `deque` breadth-first search
and reconstruction via predecessors. To regenerate the explicit CSV matrices
and state-by-state witness JSON:

```sh
python3 Investigations/vision_boundary/model.py
python3 -m unittest AppOS.Runtime.test_catalog
```

## 6. Correction, rerun and what remains

**Correction committed:** the app manifest scanner now omits
`Playroom/Research_Campus/external/**`; regression tests confirm intended
inclusions/exclusions once run. The same abstract graph with this admission
rule disallows F1. No changes were made to the live pose processing path.

Next for F2: only after running the viewer on the Pi, time inference and
display independently; then evaluate capture/compute/display separation
against a concrete latency budget. It would be premature to install
a universal threading architecture on the basis of this abstract witness.

**Coverage limitations:** depth-0 nodes: 8; matrix: 64/64 classified.
Pose refinement: 3; matrix: 9/9 classified. The reachability search is
exhaustive **within the listed finite states and rules**, not across actual
Linux processes, all possible Python input, user actions, dependencies,
or device timing. Excluded alternate relations have not been proven
impossible. A changed abstraction requires rerunning the audit.
