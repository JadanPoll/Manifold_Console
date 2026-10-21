# Minimal AX contract (REM discipline)

Problem: human developers using a web LLM need to modify experiments quickly without asking the model to reconstruct project structure, hardware rules or UI code on each attempt.

Current useful minimum: (1) capability context, (2) bounded JSON experiment configuration, (3) deterministic validation, (4) explicit user application, (5) visible result. These already exist for the signal demo; do **not** add orchestrators, agent protocols or agent accounts without demonstrated need.

Any future code-snippet workflow must preview a change, preserve base revisions, require approval, run with operating-system-enforced limits, and retain test results. Treat LLM output as untrusted data, not a command or security policy.
