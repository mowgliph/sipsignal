"""Generador de códigos de referido únicos y legibles."""

import secrets
import string


def generate_referral_code(length: int = 8) -> str:
    """
    Genera un código de referido único y legible.

    Args:
        length: Longitud del código (default: 8).

    Returns:
        Código alfanumérico en mayúsculas, sin caracteres confusos.
    """
    alphabet = string.ascii_uppercase + string.digits
    # Excluir caracteres confusos (0, O, I, L)
    alphabet = alphabet.replace("0", "").replace("O", "").replace("I", "").replace("L", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))
