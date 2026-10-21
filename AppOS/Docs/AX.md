# AX / Agent Experience for Manifold

Goal: tiny, fast, inspectable LLM context and safe experiment turnaround. AX means agents can discover precise operations, constraints, state and outcomes instead of relying on screenshots of the Wii-inspired GUI. See Microsoft's October 2026 AX introduction and agentexperience.ax.

Read in order: `AppOS/README.md` → `AppOS/Contracts/capabilities.json` → relevant app's `appos.json` → code of requested capability. Capability declarations do not grant permissions.

## Experiment path

1. Agent discovers implemented capabilities and constraints.
2. Agent produces a small declarative recipe or an ordinary code patch.
3. Deterministic validator rejects unknown/unavailable capabilities, invalid parameters or unauthorized effects.
4. Safe synthetic recipes are previewed locally; hardware, filesystem, network and executable code remain behind separate explicit approval and OS-enforced policies.
5. Record observed outputs, failure reasons and reproduction settings. Do not claim successful sandboxing without adversarial tests.

The initial Playroom Studio offers a live synthetic-signal panel. It is not yet connected to an LLM. Future integration can accept an LLM-generated JSON recipe instead of generated Python. That gives fast local iteration with minimal context and no automatic arbitrary-code execution.
