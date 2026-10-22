# Manifold Console

An experimental console and application environment for hardware, software, and interactive projects.

- [AppOS](AppOS/): navigable UI shell, application lifecycle, capabilities and eventual production protections
- [Applications](Applications/): independently developed programs
- [Hardware](Hardware/): device-specific integrations, including Kinect, cameras and future FPGA/ESP targets
- [Lib](Lib/): reusable algorithms and primitives, starting with signal filtering
- [Playroom](Playroom/): capability browser, signal playground and research testbeds\n\nTry `python3 Playroom/Capabilities/browser.py` to browse the initial capability catalog (requires Tkinter).

Develop directly in C, Python, Cython and Linux if useful. AppOS aims to offer device-agnostic services, consistent navigation, storage, audio and enforced production isolation without inventing a mandatory application language.

**Current status:** repository structure and existing Kinect experiments; AppOS services and isolation are design goals, not working features.

## Diagnosis and rendering boundary

The experimental [Latent diagnostic command](AppOS/Latent/README.md) collects a single evidence ZIP on demand. It is observability only, **not** process isolation or a production GPU scheduler. The [native compute/presentation policy](AppOS/Native/OBSERVATION_POLICY.md) records the minimum constraints justified by the Raspberry Pi graphics investigation. Keep platform-specific driver mitigations out of generic application contracts.
