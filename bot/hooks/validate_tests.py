#!/usr/bin/env python3
"""
Pre-commit hook to validate that modified Python files have associated tests.

This hook:
- Detects modified/added Python files in bot/ directory
- Maps each file to its corresponding test file in tests/
- Warns if test file doesn't exist (non-blocking)
- Logs warnings to logs/pre-commit-warnings.log
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

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
