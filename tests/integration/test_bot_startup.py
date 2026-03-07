"""Tests de verificación de inicio del bot."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_environment_variables():
    """Verifica que el archivo .env existe."""
    assert os.path.exists('.env'), "Archivo .env no encontrado"


def test_data_directories():
    """Verifica directorios de datos necesarios."""
    required_dirs = ['logs', 'data-example']
    for dir_name in required_dirs:
        assert os.path.exists(dir_name), f"Directorio {dir_name} no encontrado"


def test_handler_registration_pattern():
    """Verifica el patrón de registro de handlers."""
    with open('sipsignal.py', 'r') as f:
        content = f.read()
    
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
    """Verifica que no hay errores de sintaxis."""
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
                import pytest
                pytest.fail(f"Syntax error in {file_path}: {e}")


def test_bot_initialization_structure():
    """Verifica la estructura de inicialización del bot."""
    with open('sipsignal.py', 'r') as f:
        content = f.read()
    
    assert 'def main():' in content
    assert 'ApplicationBuilder()' in content
    assert 'app.run_polling()' in content
    assert 'post_init' in content
