# AppOS

AppOS is Manifold Console's navigable user interface and application-facing runtime. It is **not** a kernel or replacement operating system. Native C, Python, Cython, and Linux APIs remain available in development; production policy may constrain app execution through Linux-enforced isolation.

- `Shell/`: home screen, navigation, consistent application switching and visible interaction patterns
- `Runtime/`: application discovery, launch/lifecycle and eventual confinement
- `Services/`: device/capability brokerage, storage, sound and other shared conveniences
- `Contracts/`: compact documented manifests, APIs and capability vocabulary
- `Docs/`: short developer/LLM-oriented guidance and design decisions

**Status:** design skeleton; there is no running AppOS shell, enforceable sandbox, or stable API yet. Do not claim production isolation until verified with adversarial tests.
