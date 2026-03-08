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
- `bot/core/config.py` → `tests/unit/core/test_config.py`

**Comportamiento:**
- ✅ Si existe el test: log informativo
- ⚠️ Si no existe: warning (no bloquea commit)
- 📝 Logs en: `logs/pre-commit-warnings.log`

**Archivos del hook:**
- `bot/hooks/validate_tests.py` - Script principal
- `bot/hooks/__init__.py` - Package init

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
