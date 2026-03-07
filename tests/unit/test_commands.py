"""Tests de comandos del bot."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_command_status_registered():
    """Verifica que /status está registrado como alias de /logs."""
    with open("sipsignal.py") as f:
        content = f.read()

    # Buscar la línea exacta
    lines = content.split("\n")
    status_line_found = False
    logs_line_found = False

    for line in lines:
        if 'CommandHandler("status", logs_command)' in line:
            status_line_found = True
        if 'CommandHandler("logs", logs_command)' in line:
            logs_line_found = True

    assert logs_line_found, "Handler /logs no encontrado"
    assert status_line_found, "Handler /status no encontrado"


def test_all_basic_commands_exist():
    """Verifica que todos los comandos básicos existen."""
    with open("sipsignal.py") as f:
        content = f.read()

    basic_commands = ["start", "help", "myid", "ver", "status", "logs"]
    for cmd in basic_commands:
        assert f'CommandHandler("{cmd}"' in content, f"Comando /{cmd} no registrado"
