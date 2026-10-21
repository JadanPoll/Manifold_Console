# Axiomatic Capabilities

Stable, small, composable capability contracts; **not** a claim of mathematical irreducibility.

Each capability must state: identifier/version, typed inputs and outputs (including units), parameters and bounds, side effects and permissions, failure conditions, implementation reference, executable tests and a tiny example suitable for an LLM. Capability metadata describes behavior but does not grant access.

Only mark a capability stable after its contracts, tests and at least one practical consumer agree. Underlying implementations live in `Lib/` or `AppOS/Services/` as appropriate; this layer is the indexed contract, not a second implementation tree.

See `capability.example.json` for a proposed metadata shape; no universal registry enforcement exists yet.
