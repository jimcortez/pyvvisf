# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] — 2026-06-01

This release is a stability, portability, and maintenance overhaul. The
public API is unchanged but the supported Python versions, install
extras, and CI guarantees have shifted — see Breaking Changes below.

### Breaking changes

- **Dropped Python 3.8 and 3.9.** Minimum supported version is now
  Python 3.10. 3.8 went EOL in October 2024 and 3.9 in October 2025.
  Python 3.13 is now part of the matrix.
- **`PyOpenGL-accelerate` moved out of required dependencies** into an
  `[accelerated]` extra. Install with `pip install pyvvisf[accelerated]`
  to opt in. It is a binary wheel that lags on Apple Silicon and on new
  Python releases, and the renderer does not require it for correctness.

### Added

- **Cross-platform CI matrix.** GitHub Actions now runs Linux + Windows
  × Python 3.10–3.13 on every push and pull request, validating the
  `Operating System :: OS Independent` PyPI classifier. macOS cells are
  in the matrix but marked `continue-on-error` because GitHub-hosted
  macOS runners do not expose a Cocoa graphics session that GLFW can
  attach to (`NSGL: Failed to find a suitable pixel format`); macOS is
  fully supported as a user platform.
- **Lint and type-check job** gates the test matrix: `ruff check`,
  `ruff format --check`, and `mypy src/` run before any tests.
- **Separate `release.yml` workflow** triggered by `release: published`.
  Builds sdist + wheel and publishes to PyPI via OIDC trusted publishing
  in a dedicated `release` environment.
- **`build-docs.yml`** now builds with `sphinx-build -W --keep-going` so
  warnings break the build.
- **Module split.** `renderer.py` (489 LOC → 216) decomposed into
  `context.py`, `quad.py`, `result.py`. `shader_compiler.py` (816 LOC →
  ~150) decomposed into `shader_skeletons.py`, `glsl_versions.py`,
  `shader_processor.py`. The public API at `pyvvisf.*` is unchanged.
- **GLFW error callback** wired to the package logger. The previous bare
  "Failed to create GLFW window" message now includes the underlying
  driver-level reason (e.g. NSGL pixel-format errors).
- **Process-global GLFW init/terminate refcount** so multiple
  `ISFRenderer` instances share a single GLFW initialization and only
  the last one to clean up calls `glfw.terminate()`.
- **Community files.** `CHANGELOG.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, GitHub issue / PR templates,
  Dependabot config (pip + actions, weekly), CodeQL workflow, and an
  `.editorconfig`.
- **Pre-commit configuration** at `.pre-commit-config.yaml` with `ruff`
  and `ruff-format` hooks.
- **README badges** for CI status, supported Python versions, license,
  and release. **README "Running headless" section** documenting
  `xvfb-run` for Linux servers and the headless display action for
  GitHub Actions.
- **Coverage reporting** in `pytest`: `addopts` now includes
  `--cov=pyvvisf --cov-report=term-missing` (currently 83%).

### Changed

- **Offscreen renders no longer flash a visible window** on macOS or
  Windows. `GLContextManager.initialize` creates the GLFW window with
  `VISIBLE = FALSE` by default; `render_to_window` flips visibility on
  entry via the new `show_window()` method.
- **Tooling switched to `ruff` and `ruff-format`**, replacing
  black + isort + flake8. The dev extra is now slimmer:
  `pytest`, `pytest-cov`, `ruff`, `mypy`, `pre-commit`, `build`.
- **`setuptools_scm` migrated** from the deprecated `write_to` setting
  to `version_file`. Build floor bumped to `setuptools_scm>=8`.
- **Compatible-release upper bounds** added to all top-level dependencies
  (`pydantic<3`, `numpy<3`, `glfw<3`, `PyOpenGL<4`, `pillow<12`,
  `json5<1`) so a future major bump cannot silently break installs.
- **Wide single-line `from OpenGL.GL import …`** statements (600+ chars)
  replaced with `from OpenGL import GL` and `GL.glX(...)` call sites.
- **Test files** no longer manipulate `sys.path`; they rely on the
  editable install. Sphinx `version`/`release` are now pulled from
  `importlib.metadata.version("pyvvisf")` instead of being hardcoded
  to `1.0`.
- **`_version.py` import** is now resilient when running from a source
  tree that has not been built. Falls back to `0.0.0+unknown` instead
  of raising `ImportError`.
- **README** restructured around the slim-readme template (Quick Start,
  Features, FAQ, Contributing, License, Support); demo screenshot added.

### Fixed

- **`ISFRenderer.cleanup()` binds its own GL context before issuing
  GL deletes.** Without this, two `ISFRenderer` instances inside one
  `with` block would have the second teardown run GL calls against a
  null context — silent on Linux, hard `OpenGL.error.GLError(1282)` on
  Windows. Both surface as the same bug and are now fixed together.
- **`OPENGL_FORWARD_COMPAT`** is now set on macOS, which GLFW requires
  for any 3.3 core profile context. Necessary for users running locally
  on macOS even though GitHub-hosted runners have a separate session
  limitation.
- **Exception chaining** added on coercion / parsing failures (`raise
  ... from e`) so the underlying cause is preserved through
  `RenderingError`, `ShaderCompilationError`, and `ISFParseError`.
- **Sphinx warnings** in `docs/source/index.rst` (3 RST section
  underlines that were too short) eliminated. Docs build cleanly under
  `-W`.

### Removed

- **~22 dead `except NameError:` stubs** scattered through the OpenGL
  call sites in `renderer.py`, `framebuffer_manager.py`, and
  `shader_compiler.py`. The `OpenGL.GL` and `glfw` symbols are imported
  at module top level, so `NameError` was unreachable. The stubs
  silently swallowed real GL failures.
- **`ShaderSourceProcessor` class** and its
  `inject_uniform_declarations` / `inject_standard_uniforms` /
  `inject_isf_macros` / `inject_vertex_shader_init` /
  `inject_pass_target_uniforms` / `patch_legacy_gl_fragcolor` /
  `ensure_version_directive` static methods. Confirmed dead by grep
  across `src/`, `tests/`, and `examples/`; the live render path uses
  `ISFShaderProcessor` exclusively.
- **Empty `.gitmodules`** and the stale `external` line from
  `.gitignore`, both leftovers from the C++/VVISF era.

## [0.7.2] — earlier

See the GitHub [Releases](https://github.com/jimcortez/pyvvisf/releases)
page for the history prior to this changelog.
