# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING:** dropped Python 3.8 and 3.9 support; minimum is now 3.10.
- Moved `PyOpenGL-accelerate` from a required dependency to an
  `[accelerated]` extra (`pip install pyvvisf[accelerated]` to opt in).
  It is binary, lags on Apple Silicon and new Python releases, and is a
  performance optimization rather than a correctness requirement.
- Added compatible-release upper bounds on top-level dependencies so a
  major bump of `pydantic` / `numpy` / `glfw` / etc. cannot silently
  break installs.
- Migrated `setuptools_scm` from the deprecated `write_to` to
  `version_file`.
- Hidden the offscreen GLFW window by default. `render()` no longer
  flashes a visible window on macOS/Windows; `render_to_window()` now
  explicitly toggles visibility.
- Replaced the single-job CI workflow with a matrix of
  Linux/macOS/Windows × Python 3.10–3.13, plus a separate
  `release.yml` for PyPI publishes.
- Switched code style and lint tooling from black + isort + flake8 to
  `ruff` and `ruff format`.

### Removed
- Dead `except NameError:` stubs around OpenGL/GLFW calls (~22 sites).
  These were unreachable and previously suppressed real GL failures.
- `ShaderSourceProcessor` class and its `inject_*` helpers — confirmed
  unreferenced by the live render path.

### Fixed
- Sphinx `version`/`release` now read from package metadata instead of
  the hardcoded `1.0`.
- `raise ... from e` chaining on coercion / parsing errors so the
  underlying cause is preserved.

## [0.7.2] — earlier

See the GitHub [Releases](https://github.com/jimcortez/pyvvisf/releases)
page for the history prior to this changelog.
