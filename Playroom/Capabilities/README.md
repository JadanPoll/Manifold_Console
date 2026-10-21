# Capability browser

Curated, evidence-qualified high-level capabilities. Implementation remains in Lib, AppOS, Hardware or applications; one canonical descriptor is referenced from multiple domains rather than copied.

`catalog.json` is the temporary explicit index. Each entry distinguishes working, hardware-verified, research and idea status. `working` here means implementation exists and was tested previously, **not** that this new browser was tested on Raspberry Pi. A demo of kind `local` is launched only when its fixed, trusted registry command is selected; research/idea entries never execute.

Run `python3 Playroom/Capabilities/browser.py` to explore/search, view source and copy minimal LLM context. Requires a desktop with Tkinter. This is a development UI, not a sandbox. No automatic execution of model-generated snippets.
