# CI Pipeline Design - sipsignal

**Date:** 2026-03-06
**Status:** Approved

## Overview

Implement a complete CI/CD pipeline for the sipsignal Python project using GitHub Actions.

## Architecture

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐
│   Lint   │→ │   Test   │→ │  Build   │→ │  Security  │→ │  Deploy  │
└──────────┘  └──────────┘  └──────────┘  └────────────┘  └──────────┘
   ruff         pytest       build        bandit/          manual
                               .whl      safety          to k8s
```

## Stages

| Stage | Tool | Description |
|-------|------|-------------|
| Lint | ruff | Code quality + formatting |
| Test | pytest + coverage | Unit tests with ≥70% coverage |
| Build | build (setuptools) | Generate .whl installable |
| Security | bandit + safety | Vulnerability scan |
| Deploy | kubectl | Deploy to staging (auto), prod (manual) |

## Triggers

- **Push to develop**: Lint → Test → Build → Security → Deploy staging (auto)
- **PR to main**: Same stages, manual deploy to prod
- **Tags v***: Release build + deploy prod

## Files to Create

1. `.github/workflows/ci.yml` - Main pipeline
2. `pyproject.toml` - Project config + pytest + ruff
3. `.ruff.toml` - Linter configuration
