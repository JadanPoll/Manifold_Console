# AppOS Services

AppOS provides optional shared conveniences for applications: device acquisition and a switchboard, eventually storage and audio policies. They are not replacements for ordinary native C/Python libraries.

Implemented: `switchboard.py` is a **dependency-free in-process reference model** for shared synthetic frame streams, independent subscriber sampling, explicit exclusive leases and consistent error codes. No hardware ownership, IPC or sandbox enforcement exists. See [SWITCHBOARD.md](SWITCHBOARD.md).

Latent, also inside AppOS, will eventually arbitrate budgets and scheduling; the Switchboard owns data routing and resource lifecycle. Neither should be inserted into cheap local mathematical operations.
