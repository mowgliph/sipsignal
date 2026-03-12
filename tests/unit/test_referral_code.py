"""Tests for referral code generator."""

from bot.utils.referral_code import generate_referral_code


def test_generate_referral_code_length():
    """Código debe tener 8 caracteres por defecto."""
    code = generate_referral_code()
    assert len(code) == 8


def test_generate_referral_code_alphanumeric():
    """Código debe ser alfanumérico en mayúsculas."""
    code = generate_referral_code()
    assert code.isalnum()
    assert code == code.upper()


def test_generate_referral_code_no_confusing_chars():
    """Código no debe tener caracteres confusos (0, O, I, L)."""
    code = generate_referral_code()
    assert all(c not in "0OIL" for c in code)


def test_generate_referral_code_custom_length():
    """Código debe soportar longitud personalizada."""
    code = generate_referral_code(length=12)
    assert len(code) == 12


def test_generate_referral_code_uniqueness():
    """Códigos generados deben ser únicos."""
    codes = [generate_referral_code() for _ in range(1000)]
    assert len(codes) == len(set(codes))
