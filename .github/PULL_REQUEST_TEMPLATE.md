<!-- Thanks for sending a pull request! Please fill in the sections below. -->

## Summary

<!-- One or two sentences describing the change and the motivation. -->

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would change existing behavior)
- [ ] Documentation update
- [ ] Maintenance (refactor / tooling / CI)

## Test plan

<!-- How did you verify this works? List the commands you ran and any
     manual checks. CI runs lint + tests on every push. -->

- [ ] `ruff check . && ruff format --check .`
- [ ] `pytest`
- [ ] Manual rendering smoke test (if behavior changed)

## Checklist

- [ ] I read [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] I updated `CHANGELOG.md` under `## [Unreleased]` if this change is
      user-visible.
- [ ] I added or extended tests for behavioral changes.
- [ ] I have not committed credentials, large binaries, or generated files.
