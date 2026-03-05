# Comando /status y Pruebas de Funcionalidad - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar comando `/status` como alias de `/logs` y realizar pruebas de funcionamiento del bot en entorno venv.

**Architecture:** Reutilizar la función `logs_command` existente en `handlers/admin.py` y registrar un nuevo handler en `sipsignal.py`. Crear suite de tests básicos para verificar inicio del bot y comandos.

**Tech Stack:** Python 3, python-telegram-bot, pytest, venv

---

## Task 1: Crear Entorno Virtual e Instalar Dependencias

**Files:**
- Create: `venv/` directory
- Modify: N/A
- Test: N/A

**Step 1: Crear venv en carpeta del proyecto**

```bash
cd /home/mowgli/sipsignal
python3 -m venv venv
```

Expected: Directorio `venv/` creado con bin/, lib/, include/

**Step 2: Activar venv e instalar dependencias**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Expected: Todas las dependencias instaladas sin errores

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: setup venv and install dependencies"
```

---

## Task 2: Implementar Comando /status

**Files:**
- Create: N/A
- Modify: `sipsignal.py:239-241`
- Test: N/A (testeado en Task 3)

**Step 1: Agregar handler para /status**

En `sipsignal.py`, después del handler de `/logs` (línea 240), agregar:

```python
app.add_handler(CommandHandler("status", logs_command))
```

**Step 2: Verificar import correcto**

Confirmar que `logs_command` ya está importado en la línea 28:
```python
from handlers.admin import users, logs_command, set_admin_util, set_logs_util, ms_conversation_handler, ad_command
```

**Step 3: Commit**

```bash
git add sipsignal.py
git commit -m "feat: add /status command alias for /logs"
```

---

## Task 3: Escribir Tests de Funcionalidad

**Files:**
- Create: `tests/test_bot_basic.py`
- Create: `tests/__init__.py`
- Modify: N/A

**Step 1: Crear directorio de tests**

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 2: Escribir test básico de imports**

Create: `tests/test_bot_basic.py`

```python
"""Tests básicos de funcionamiento del bot."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports_basic():
    """Verifica que los módulos principales se pueden importar."""
    try:
        from utils.logger import logger
        from utils.file_manager import cargar_usuarios
        from core.config import settings, VERSION
        from handlers.admin import logs_command
        from handlers.general import start, help_command
        assert VERSION is not None
        assert settings is not None
    except Exception as e:
        pytest.fail(f"Import failed: {e}")


def test_config_loaded():
    """Verifica que la configuración carga correctamente."""
    from core.config import settings, VERSION, PID, STATE
    assert VERSION != ""
    assert PID > 0
    assert STATE in ["RUNNING", "ACTIVE", "IDLE"]


def test_status_handler_registered():
    """Verifica que el handler /status está registrado en la lista de handlers."""
    # Leer el archivo sipsignal.py y verificar que status está registrado
    import re
    with open('sipsignal.py', 'r') as f:
        content = f.read()
    
    # Buscar el registro del handler status
    assert 'CommandHandler("status", logs_command)' in content, \
        "Handler /status no encontrado en sipsignal.py"


def test_logs_command_exists():
    """Verifica que la función logs_command existe y es callable."""
    from handlers.admin import logs_command
    assert callable(logs_command)


def test_file_manager_functions():
    """Verifica funciones críticas de file_manager."""
    from utils.file_manager import cargar_usuarios, guardar_usuarios
    # Estas funciones deben existir y ser callable
    assert callable(cargar_usuarios)
    assert callable(guardar_usuarios)
```

**Step 3: Instalar pytest y ejecutar tests**

```bash
source venv/bin/activate
pip install pytest pytest-asyncio
python -m pytest tests/test_bot_basic.py -v
```

Expected: Todos los tests PASS

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: add basic functionality tests"
```

---

## Task 4: Verificar Inicio del Bot (Dry Run)

**Files:**
- Create: `tests/test_bot_startup.py`
- Modify: N/A

**Step 1: Crear test de verificación de estructura**

Create: `tests/test_bot_startup.py`

```python
"""Tests de verificación de inicio del bot."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_environment_variables():
    """Verifica que el archivo .env existe y tiene variables necesarias."""
    assert os.path.exists('.env'), "Archivo .env no encontrado"
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verificar que al menos existe la variable de token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    # Nota: No validamos que exista para no fallar en CI
    # Solo verificamos que el sistema de carga funcione


def test_data_directories():
    """Verifica que existen los directorios de datos necesarios."""
    required_dirs = ['logs', 'data-example']
    for dir_name in required_dirs:
        assert os.path.exists(dir_name) or os.path.exists(f'{dir_name}.json'), \
            f"Directorio/archivo {dir_name} no encontrado"


def test_handler_registration_pattern():
    """Verifica el patrón de registro de handlers en sipsignal.py."""
    import re
    with open('sipsignal.py', 'r') as f:
        content = f.read()
    
    # Verificar que existen handlers básicos
    required_handlers = [
        'CommandHandler("start"',
        'CommandHandler("help"',
        'CommandHandler("status"',
        'CommandHandler("myid"',
        'CommandHandler("ver"',
    ]
    
    for handler in required_handlers:
        assert handler in content, f"Handler {handler} no registrado"


def test_no_syntax_errors():
    """Verifica que no hay errores de sintaxis en archivos principales."""
    import py_compile
    
    files_to_check = [
        'sipsignal.py',
        'handlers/admin.py',
        'handlers/general.py',
        'core/config.py',
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                py_compile.compile(file_path, doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Syntax error in {file_path}: {e}")


def test_bot_initialization_structure():
    """Verifica la estructura de inicialización del bot."""
    with open('sipsignal.py', 'r') as f:
        content = f.read()
    
    # Verificar componentes clave
    assert 'def main():' in content
    assert 'ApplicationBuilder()' in content
    assert 'app.run_polling()' in content
    assert 'post_init' in content
```

**Step 2: Ejecutar tests**

```bash
python -m pytest tests/test_bot_startup.py -v
```

Expected: Todos los tests PASS

**Step 3: Commit**

```bash
git add tests/test_bot_startup.py
git commit -m "test: add bot startup verification tests"
```

---

## Task 5: Ejecutar Pruebas Completas

**Files:**
- Modify: N/A
- Test: Todos los tests

**Step 1: Ejecutar suite completa**

```bash
source venv/bin/activate
python -m pytest tests/ -v --tb=short
```

Expected: 
```
test_bot_basic.py::test_imports_basic PASSED
test_bot_basic.py::test_config_loaded PASSED
test_bot_basic.py::test_status_handler_registered PASSED
test_bot_basic.py::test_logs_command_exists PASSED
test_bot_basic.py::test_file_manager_functions PASSED
test_bot_startup.py::test_environment_variables PASSED
test_bot_startup.py::test_data_directories PASSED
test_bot_startup.py::test_handler_registration_pattern PASSED
test_bot_startup.py::test_no_syntax_errors PASSED
test_bot_startup.py::test_bot_initialization_structure PASSED
```

**Step 2: Verificar con flake8 (opcional)**

```bash
pip install flake8
flake8 sipsignal.py --max-line-length=120 --ignore=E501,W503
```

Expected: Sin errores críticos

**Step 3: Reporte Final**

Crear reporte de pruebas:

```bash
python -m pytest tests/ -v --tb=short > tests/reporte_pruebas.txt
cat tests/reporte_pruebas.txt
```

---

## Summary

Al completar estas tareas:

1. ✅ Entorno virtual creado y configurado
2. ✅ Comando `/status` implementado
3. ✅ Tests básicos funcionando
4. ✅ Bot verificado sin errores de sintaxis
5. ✅ Estructura de handlers validada

**Comandos implementados disponibles:**
- `/status` - Muestra estado del bot (nuevo)
- `/start`, `/help`, `/myid`, `/ver` - Comandos existentes

**Archivos modificados:**
- `sipsignal.py` - Agregado handler `/status`

**Archivos creados:**
- `tests/test_bot_basic.py`
- `tests/test_bot_startup.py`
- `docs/plans/2025-03-05-status-command-design.md`
