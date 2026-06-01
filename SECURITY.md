# Security Policy

## Reporting a vulnerability

If you believe you have found a security vulnerability in pyvvisf, please
**do not open a public issue**. Instead, report it privately via GitHub's
[private vulnerability reporting](https://github.com/jimcortez/pyvvisf/security/advisories/new)
flow, or email the maintainer directly at the address listed on the
[project homepage](https://github.com/jimcortez/pyvvisf).

Please include:

- A description of the issue and its impact.
- Steps to reproduce, ideally with a minimal shader / Python snippet.
- The pyvvisf version, OS, and Python version where you observed it.

We aim to acknowledge reports within **3 business days** and to provide
an initial assessment within **7 business days**.

## Supported versions

Security fixes are applied to the latest minor release on PyPI. Older
versions are not back-patched.

| Version | Supported          |
| ------- | ------------------ |
| 0.7.x   | :white_check_mark: |
| < 0.7   | :x:                |

## Scope

In-scope concerns include, but are not limited to:

- Memory safety issues in the parsing or rendering paths.
- Vulnerabilities introduced by third-party dependencies that pyvvisf
  exposes through its public API.

Out-of-scope:

- Issues that require running adversarial GLSL with full developer
  privileges on the user's machine.
- Bugs reproducible only on unsupported Python or OS versions.
