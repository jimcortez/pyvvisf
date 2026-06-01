# Contributing to pyvvisf

Thank you for your interest in contributing! This document captures the
day-to-day workflow expected for this project.

## Getting set up

```bash
git clone https://github.com/jimcortez/pyvvisf.git
cd pyvvisf
pip install -e ".[dev]"
pre-commit install
```

Install `PyOpenGL-accelerate` only if it is available on your platform:

```bash
pip install -e ".[dev,accelerated]"
```

The accelerated bindings are a runtime optimization and not a correctness
requirement.

## Running tests

```bash
pytest
```

The renderer needs a real OpenGL context. On a headless Linux machine
(CI containers, servers, etc.) wrap the test command in `xvfb-run`:

```bash
xvfb-run -a pytest
```

GitHub Actions uses
[`pyvista/setup-headless-display-action`](https://github.com/pyvista/setup-headless-display-action)
to provide a display on every OS in the matrix.

> **macOS CI caveat.** GitHub-hosted macOS runners don't reliably expose a
> Cocoa graphics session that GLFW can attach to, so tests that open an
> OpenGL context are flaky there. The macOS matrix cells run with
> `continue-on-error: true` — they exercise parser and validation paths,
> but their failures don't gate PRs. macOS is fully supported as a
> *user* platform; this is purely a CI environment limitation.

## Lint, format, type-check

```bash
ruff check .
ruff format --check .
mypy src/
```

`pre-commit` runs `ruff` (with `--fix`) and `ruff-format` automatically on
staged files. CI gates tests on a green lint job — fix lint locally
before pushing rather than re-pushing to chase warnings.

## Supported toolchain

- Python: **3.10 – 3.13**
- OpenGL: **3.3 core profile**
- GLSL: **330** by default; pass `glsl_version=` to `ISFRenderer` to pin
  another version. `pyvvisf.get_supported_glsl_versions()` probes the
  current driver.

## Pull requests

- Branch from `main`. Keep PRs small and focused on a single change.
- Update `CHANGELOG.md` under `## [Unreleased]` for any user-visible
  change (behavior, public API, packaging).
- Add or extend tests when changing behavior.
- Be ready for the CI matrix (Linux + macOS + Windows × Python 3.10–3.13)
  to flag platform-specific issues; the project's `Operating System ::
  OS Independent` classifier is verified, not aspirational.

## Reporting bugs

Use the GitHub
[issue tracker](https://github.com/jimcortez/pyvvisf/issues). Include:

- pyvvisf version (`python -c "import pyvvisf; print(pyvvisf.__version__)"`)
- OS and Python version
- A minimal shader and Python snippet that reproduces the problem
- The full error message and traceback

For shader compilation issues, the wrapped GLSL source attached to the
exception is usually the most useful artifact — please paste it.
