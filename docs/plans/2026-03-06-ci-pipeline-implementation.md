# CI Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement complete CI/CD pipeline for sipsignal Python project using GitHub Actions

**Architecture:** Multi-stage pipeline with lint, test, build, security scan, and deploy stages. Uses ruff for linting, pytest for testing, build for packaging, bandit+safety for security scanning.

**Tech Stack:** GitHub Actions, ruff, pytest, build, bandit, safety, kubectl

---

## Task 1: Create pyproject.toml with project and tool configuration

**Files:**
- Create: `/home/mowgli/sipsignal/pyproject.toml`

**Step 1: Create pyproject.toml with all configurations**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sipsignal"
version = "0.1.0"
description = "Signal-based trading system"
requires-python = ">=3.9"
dependencies = [
    "groq>=0.4.0",
    "alembic>=1.12.0",
    "sqlalchemy>=2.0.0",
    "python-dotenv>=1.0.0",
    "requests>=2.31.0",
    "pandas>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "bandit>=1.7.0",
    "safety>=3.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["."]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/.venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]

[tool.ruff]
target-version = "py39"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["B011"]
```

**Step 2: Verify pyproject.toml is valid**

```bash
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
```

Expected: No output (valid TOML)

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject.toml with project and tool config"
```

---

## Task 2: Create ruff configuration file

**Files:**
- Create: `/home/mowgli/sipsignal/.ruff.toml`

**Step 1: Create .ruff.toml**

```toml
target-version = "py39"
line-length = 100

[lint]
select = [
    "E",     # pycodestyle errors
    "F",     # pyflakes
    "W",     # pycodestyle warnings
    "I",     # isort
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
]
ignore = ["E501"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["B011"]

[lint.isort]
known-first-party = ["ai", "core", "db", "handlers", "utils"]
```

**Step 2: Commit**

```bash
git add .ruff.toml
git commit -m "chore: add ruff configuration"
```

---

## Task 3: Create GitHub Actions CI workflow

**Files:**
- Create: `/home/mowgli/sipsignal/.github/workflows/ci.yml`

**Step 1: Create .github/workflows directory**

```bash
mkdir -p .github/workflows
```

**Step 2: Create ci.yml**

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]
  workflow_dispatch:

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install ruff

      - name: Run ruff
        run: ruff check .

      - name: Run ruff format check
        run: ruff format --check .

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run pytest
        run: pytest --cov=. --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install build
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Check package
        run: pip install dist/*.whl && pip uninstall sipsignal -y

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  security:
    name: Security
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run bandit
        run: bandit -r . -x ./tests -f json -o bandit-report.json
        continue-on-error: true

      - name: Run safety
        run: safety check --json > safety-report.json || true

      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json
```

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI pipeline"
```

---

## Task 4: Create tests directory with basic test structure

**Files:**
- Create: `/home/mowgli/sipsignal/tests/__init__.py`
- Create: `/home/mowgli/sipsignal/tests/test_example.py`

**Step 1: Create tests directory**

```bash
mkdir -p tests
```

**Step 2: Create tests/__init__.py**

```python
# Tests package
```

**Step 3: Create test_example.py**

```python
def test_example():
    """Example test to verify pytest works."""
    assert 1 + 1 == 2


def test_example_with_parametrize():
    """Example parametrized test."""
    numbers = [1, 2, 3, 4, 5]
    for num in numbers:
        assert num > 0
```

**Step 4: Run tests to verify**

```bash
pip install -e ".[dev]" && pytest tests/ -v
```

Expected: 2 tests pass

**Step 5: Commit**

```bash
git add tests/__init__.py tests/test_example.py
git commit -m "test: add basic test structure"
```

---

## Task 5: Verify CI pipeline works locally

**Steps:**

**Step 1: Install dev dependencies**

```bash
pip install -e ".[dev]"
```

**Step 2: Run lint**

```bash
ruff check .
```

Expected: No errors (or ignore E501)

**Step 3: Run tests**

```bash
pytest --cov=. --cov-report=term-missing
```

Expected: Tests pass with coverage report

**Step 4: Run build**

```bash
pip install build && python -m build
```

Expected: dist/ folder with .whl and .tar.gz

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-03-06-ci-pipeline-design.md`. Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
