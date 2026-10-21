# Web-LLM-to-Console workflow

**Objective:** very short ideation cycle without installing a coding agent or embedding a model in AppOS.

## Two lanes

1. **Declarative Playroom recipes (implemented):** In Playroom Studio select **Copy LLM Context**, paste that text into any web LLM, copy the LLM's JSON response, then select **Paste Recipe**. Local validation accepts only the five specified scalar fields, never arbitrary code, and immediately updates the synthetic experiment. You can also load a saved recipe file.
2. **Source-code snippets/patches (future):** Have the web LLM return a proposed change with target file, base revision, dependencies, expected effects, tests, and requested capabilities. Preview the exact diff, require human approval, then stage in a development workspace. No automatic execution or mutation of production files. Running untrusted C/Python code requires independently verified OS sandboxing; parsing a manifest is not a sandbox.

## Fast agent context

- `AppOS/Contracts/capabilities.json` lists implemented/unimplemented capabilities.
- `Playroom/Studio/recipe.py` defines the currently implemented recipe schema and validation.
- An app's `appos.json` defines identity, launch and requested capabilities. Its permissions are **not** granted by declaration.
- Expose tiny, task-specific context snippets and current experiment outputs, rather than dumping the whole repository into prompts.

## Boundaries

The initial recipe path never evaluates expressions, calls devices or opens network sockets. It has no LLM API connection; clipboard is the transport. The Python shell launches normal executables **unsandboxed in Dev Mode**. Do not run unknown code in that launcher expecting protection. Production isolation and code-patch ingestion have not been built.
