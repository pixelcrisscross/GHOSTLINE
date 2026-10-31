# GHOSTLINE Session Archive

Exported: 2026-10-31T05:46:15.271701+00:00

## USER · chat · 2026-10-31T05:41:57.658663+00:00

Explain what a Python virtual environment is.

## ASSISTANT · chat · 2026-10-31T05:43:27.244765+00:00

A Python virtual environment is an isolated directory containing its own Python interpreter and installed packages, separate from the global Python environment. It allows projects to have distinct dependencies without conflicting with each other. When activated, it modifies your shell's `PATH` to use the virtual environment's binaries (like `python` and `pip`), ensuring commands affect only that isolated space. This prevents version clashes and ensures reproducibility. Tools like `venv` (Python 3.3+) or `virtualenv` create these environments, which are typically managed via activation scripts (`source venv/bin/activate` on Unix, `venv\Scripts\activate` on Windows).

## USER · chat · 2026-10-31T05:43:31.859033+00:00

Give me an example.
