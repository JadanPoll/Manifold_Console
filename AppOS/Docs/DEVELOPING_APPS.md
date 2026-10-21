# Building Manifold applications

**Dev:** use ordinary C, Python, Cython and direct Linux/device libraries. No AppOS SDK required to experiment.

**Production goal:** apps can declare capabilities, request standardized AppOS services where applicable, and integrate with consistent Home/Back/app-switch navigation and managed storage/sound. The host enforces resource permissions independently of the programming language.

**LLM/developer quick orientation:** read `AppOS/README.md`, `Contracts/README.md`, and an application's manifest. The manifest vocabulary is provisional; see `Contracts/app.example.json`.

Native escape hatches are useful in Dev; Production can grant narrowly scoped native access when necessary. Don't confuse device agnosticism with a prohibition on device-specific features.
