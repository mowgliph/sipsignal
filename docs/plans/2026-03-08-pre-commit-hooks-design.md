# Pre-commit Hooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar sistema de hooks pre-commit profesional con validación de tests asociados para SipSignal.

**Architecture:** Sistema híbrido usando pre-commit framework para hooks estándar (ruff, format, etc.) + hook custom en Python para validar existencia de tests asociados.

**Tech Stack:** pre-commit framework, Python 3.13+, bash hooks, pytest.

---

## Tarea 1: Crear configuración base de pre-commit

**Files:**
- Create: `.pre-commit-config.yaml`

**Step 1: Crear archivo de configuración**

```yaml
# .pre-commit-config.yaml
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
default_language_version:
  python: python3.13

default_stages: [commit]

repos:
  # Ruff - Linter y formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Hooks estándar de pre-commit
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--unsafe]
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: check-case-conflict

  # Hook custom: validar tests asociados
  - repo: local
    hooks:
      - id: validate-tests
        name: Validate tests associated
        entry: python hooks/validate_tests.py
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
```

**Step 2: Verificar sintaxis YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"`
Expected: Sin errores

**Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: agregar configuración base de pre-commit"
```

---

## Tarea 2: Crear hook custom para validar tests

**Files:**
- Create: `hooks/validate_tests.py`
- Create: `hooks/__init__.py`

**Step 1: Crear directorio hooks**

```bash
mkdir -p hooks
```

**Step 2: Crear archivo __init__.py vacío**

```python
# hooks/__init__.py
"""Pre-commit hooks for SipSignal."""
```

**Step 3: Crear script validate_tests.py**

```python
#!/usr/bin/env python3
"""
Pre-commit hook to validate that modified Python files have associated tests.

This hook:
- Detects modified/added Python files in bot/ directory
- Maps each file to its corresponding test file in tests/
- Warns if test file doesn't exist (non-blocking)
- Logs warnings to logs/pre-commit-warnings.log
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pre-commit-warnings.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def get_modified_files() -> list[str]:
    """Get list of modified/added Python files in staging area."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f.endswith(".py") and f.startswith("bot/")]
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting modified files: {e}")
        return []


def map_to_test_file(source_file: str) -> str:
    """
    Map source file to its expected test file.

    Examples:
        bot/trading/signal.py -> tests/unit/trading/test_signal.py
        bot/handlers/commands.py -> tests/unit/handlers/test_commands.py
        bot/core/config.py -> tests/unit/core/test_config.py
    """
    # Extraer path relativo dentro de bot/
    relative_path = source_file.replace("bot/", "")
    parts = relative_path.split("/")

    # Construir path al test
    if len(parts) == 1:
        # Archivo directo en bot/ (raro)
        test_path = f"tests/unit/test_{parts[0]}"
    else:
        # Archivo en subdirectorio
        module_dir = parts[0]  # trading, handlers, core, etc.
        filename = parts[-1]
        test_path = f"tests/unit/{module_dir}/test_{filename}"

    return test_path


def validate_tests(files: list[str]) -> tuple[bool, list[str]]:
    """
    Validate that modified files have associated tests.

    Returns:
        tuple: (all_valid, warnings_list)
    """
    warnings = []

    print("🔍 Validando tests asociados...")

    for source_file in files:
        test_file = map_to_test_file(source_file)

        if not os.path.exists(test_file):
            warning_msg = (
                f"⚠️  WARNING: {source_file} no tiene test asociado\n"
                f"   → Se recomienda crear: {test_file}"
            )
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        else:
            logger.info(f"✅ {source_file} → {test_file}")

    # Resumen
    total = len(files)
    with_tests = total - len(warnings)
    print(f"✅ {with_tests}/{total} archivos tienen tests asociados")

    return len(warnings) == 0, warnings


def main() -> int:
    """Main entry point."""
    modified_files = get_modified_files()

    if not modified_files:
        print("✅ No hay archivos Python modificados en bot/")
        return 0

    all_valid, warnings = validate_tests(modified_files)

    # Nota informativa (no bloquea)
    if warnings:
        print("\n💡 Tip: Los warnings no bloquean el commit, pero se recomienda agregar tests.")
        print(f"   Logs completos en: {LOG_FILE}")

    return 0  # Nunca bloquear, solo advertir


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Hacer ejecutable el script**

```bash
chmod +x hooks/validate_tests.py
```

**Step 5: Commit**

```bash
git add hooks/
git commit -m "feat: agregar hook custom para validar tests asociados"
```

---

## Tarea 3: Instalar pre-commit localmente

**Files:**
- Modify: `pyproject.toml` (agregar pre-commit a dev dependencies)

**Step 1: Agregar pre-commit a pyproject.toml**

Modificar `[project.optional-dependencies]` en `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "bandit>=1.7.0",
    "safety>=3.0.0",
    "pre-commit>=3.6.0",
]
```

**Step 2: Reinstalar dependencias**

```bash
pip install -e ".[dev]"
```

**Step 3: Instalar hooks de git**

```bash
pre-commit install
```

Expected output:
```
pre-commit installed at .git/hooks/pre-commit
```

**Step 4: Verificar instalación**

```bash
pre-commit --version
```

Expected: `pre-commit 3.x.x`

**Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "chore: agregar pre-commit como dependencia de desarrollo"
```

---

## Tarea 4: Probar hooks con archivos existentes

**Files:**
- None (testing task)

**Step 1: Ejecutar pre-commit en todos los archivos**

```bash
pre-commit run --all-files
```

Expected output:
```
ruff.....................................................................Passed
ruff-format..............................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check for added large files..............................................Passed
check for merge conflicts................................................Passed
check for case conflicts.................................................Passed
Validate tests associated................................................Passed
```

**Step 2: Verificar logs de warnings**

```bash
cat logs/pre-commit-warnings.log
```

Expected: Warnings para archivos sin tests

**Step 3: Probar con cambio real**

```bash
# Crear archivo de prueba
echo "# Test file" > bot/test_temp.py
git add bot/test_temp.py
git commit -m "test: probar hook"
```

Expected: Ver warning del hook custom

**Step 4: Limpiar archivo de prueba**

```bash
git reset --soft HEAD~1  # Deshacer commit
git reset bot/test_temp.py
rm bot/test_temp.py
```

---

## Tarea 5: Agregar documentación para el equipo

**Files:**
- Create: `docs/pre-commit-hooks.md`
- Modify: `README.md` (agregar sección de pre-commit)

**Step 1: Crear documentación completa**

```markdown
# Pre-commit Hooks

## Overview

SipSignal utiliza pre-commit hooks para asegurar calidad de código antes de cada commit.

## Instalación

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Instalar hooks
pre-commit install
```

## Hooks configurados

| Hook | Descripción | Bloquea |
|------|-------------|---------|
| ruff | Lint con auto-fix | ✅ |
| ruff-format | Formato de código | ✅ |
| trailing-whitespace | Elimina espacios extra | ✅ |
| end-of-file-fixer | Newline al final | ✅ |
| check-yaml | Valida YAML | ✅ |
| check-added-large-files | Previene archivos >1MB | ✅ |
| check-merge-conflict | Detecta conflictos | ✅ |
| check-case-conflict | Detecta case conflicts | ✅ |
| validate-tests | Valida tests asociados | ⚠️ (warning) |

## Comandos útiles

```bash
# Ejecutar en todos los archivos
pre-commit run --all-files

# Ejecutar hook específico
pre-commit run ruff --all-files

# Ver hooks instalados
pre-commit sample-config

# Actualizar versiones de hooks
pre-commit autoupdate

# Desinstalar hooks
pre-commit uninstall
```

## Hook custom: validate-tests

El hook `validate-tests` verifica que archivos modificados en `bot/` tengan tests asociados en `tests/`.

**Mapeo:**
- `bot/trading/signal.py` → `tests/unit/trading/test_signal.py`
- `bot/handlers/commands.py` → `tests/unit/handlers/test_commands.py`

**Comportamiento:**
- ✅ Si existe el test: log informativo
- ⚠️ Si no existe: warning (no bloquea commit)
- 📝 Logs en: `logs/pre-commit-warnings.log`

## Troubleshooting

### Hook falla con error de Python
```bash
# Verificar instalación
pip install pre-commit

# Reinstalar hooks
pre-commit uninstall
pre-commit install
```

### Quiero hacer commit sin hooks (solo emergencias)
```bash
git commit -m "msg" --no-verify
```

### Ver logs de warnings
```bash
cat logs/pre-commit-warnings.log
```
```

**Step 2: Agregar sección al README.md**

Buscar sección de "Development" o "Testing" y agregar:

```markdown
## Pre-commit Hooks

Instalar hooks antes de desarrollar:

```bash
pip install -e ".[dev]"
pre-commit install
```

Ver [docs/pre-commit-hooks.md](docs/pre-commit-hooks.md) para más detalles.
```

**Step 3: Commit**

```bash
git add docs/pre-commit-hooks.md README.md
git commit -m "docs: agregar documentación de pre-commit hooks"
```

---

## Tarea 6: Integrar con CI/CD (GitHub Actions)

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Agregar job de pre-commit al CI**

Modificar `.github/workflows/ci.yml`, agregar job después de `lint`:

```yaml
  pre-commit:
    name: Pre-commit
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
          pip install pre-commit

      - name: Run pre-commit
        run: pre-commit run --all-files
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: integrar pre-commit en pipeline de CI/CD"
```

---

## Tarea 7: Verificación final y cleanup

**Files:**
- None (verification task)

**Step 1: Ejecutar todos los tests**

```bash
pytest
```

Expected: Todos los tests pasan

**Step 2: Ejecutar ruff**

```bash
ruff check .
ruff format --check .
```

Expected: Sin errores

**Step 3: Verificar estructura de archivos**

```bash
ls -la hooks/
cat .pre-commit-config.yaml
pre-commit --version
```

**Step 4: Commit final (si hay cambios)**

```bash
git add .
git commit -m "chore: verificación final y cleanup"
```

---

## Checklist de Completitud

- [ ] `.pre-commit-config.yaml` creado con todos los hooks
- [ ] `hooks/validate_tests.py` implementado y ejecutable
- [ ] `hooks/__init__.py` creado
- [ ] `pyproject.toml` actualizado con pre-commit
- [ ] Hooks instalados localmente (`pre-commit install`)
- [ ] Tests de hooks pasan (`pre-commit run --all-files`)
- [ ] Documentación creada (`docs/pre-commit-hooks.md`)
- [ ] README.md actualizado
- [ ] CI/CD actualizado con job de pre-commit
- [ ] Todos los tests del proyecto pasan

---

## Comandos de Referencia Rápida

```bash
# Instalación
pip install -e ".[dev]"
pre-commit install

# Ejecución manual
pre-commit run --all-files

# Ver logs
cat logs/pre-commit-warnings.log

# Actualizar hooks
pre-commit autoupdate
```
