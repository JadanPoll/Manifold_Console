# Capability chapters and Connect workspace (v1 design)

Users navigate **chapters**, not a flat list of algorithms or packages.

- **Camera & Vision** — cameras, depth, edges, segmentation, features, tracking
- **Audio & Signals** — microphones, synthesis, filtering, transforms
- **Hardware** — Kinect, GPIO, FPGA, ESP, device diagnostics
- **Interaction & Play** — gestures, controls, visual playgrounds
- **Development** — native kernels, performance, inspection, diagnostics

A chapter is navigational metadata, **not** an installation unit or dependency.
Each capability remains separately buildable/installable. One capability has one
primary chapter, can carry multiple searchable tags, and can appear in queries
regardless of the selected chapter.

## Connect: the orthogonal composition surface

Do not nest compositions inside chapter menus. The user's second operation is
**Connect**: inspect outputs, choose a compatible input, and wire together
capabilities from any chapters. An initial example:

    Camera/Kinect depth -> Vision/Depth-to-gray -> Vision/Sobel edges -> Viewer

Each connector endpoint must eventually declare:
- data type and schema version (e.g., image/gray8 v1)
- dimensions/stride/encoding or sample rate, as applicable
- lifetime/ownership: borrowed, copied, or immutable shared frame
- update semantics: latest state, queued events, or timed stream
- bounded capacity and overload behavior
- device ownership, if any

**No implicit format conversion.** A connector can join two endpoints directly
only when their declared types/versions and ownership rules match. Otherwise,
show an explicit adapter node with its own capability package.

For v1, start with a small explicit graph stored as readable declarative data.
Do not promise arbitrary graphs, automatic AI wiring, sandboxing, or a stable
plugin ABI yet. A package manifest is not an executable command to be trusted
from an unreviewed repository.

The existing capability browser now offers chapter filtering; the graphical
Connect editor and actual interprocess routing are **not yet implemented**.
