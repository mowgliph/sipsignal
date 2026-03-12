"""Tests for inline keyboard builders."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.utils.inline_keyboards import (
    build_access_keyboard,
    build_role_change_admin_keyboard,
    build_role_change_keyboard,
    build_role_keyboard,
)


def test_build_access_keyboard():
    """Test access keyboard has approve and deny buttons."""
    keyboard = build_access_keyboard(123456)

    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2

    approve_btn = keyboard.inline_keyboard[0][0]
    deny_btn = keyboard.inline_keyboard[0][1]

    assert approve_btn.text == "✅ Aprobar"
    assert approve_btn.callback_data == "access_approve:123456"

    assert deny_btn.text == "❌ Rechazar"
    assert deny_btn.callback_data == "access_deny:123456"


def test_build_role_keyboard():
    """Test role selection keyboard structure."""
    keyboard = build_role_keyboard(123456)

    # Should have 2 rows
    assert len(keyboard.inline_keyboard) == 2

    # First row: 3 role buttons
    assert len(keyboard.inline_keyboard[0]) == 3

    viewer_btn = keyboard.inline_keyboard[0][0]
    trader_btn = keyboard.inline_keyboard[0][1]
    admin_btn = keyboard.inline_keyboard[0][2]

    assert viewer_btn.text == "👁️ Viewer"
    assert viewer_btn.callback_data == "role_set:123456:viewer"

    assert trader_btn.text == "📊 Trader"
    assert trader_btn.callback_data == "role_set:123456:trader"

    assert admin_btn.text == "⭐ Admin"
    assert admin_btn.callback_data == "role_set:123456:admin"

    # Second row: cancel button
    assert len(keyboard.inline_keyboard[1]) == 1
    cancel_btn = keyboard.inline_keyboard[1][0]
    assert cancel_btn.text == "❌ Cancelar"
    assert cancel_btn.callback_data == "role_cancel"


def test_build_role_change_keyboard_trader_admin():
    """Test role change keyboard for viewer (can request trader or admin)."""
    keyboard = build_role_change_keyboard(["trader", "admin"])

    # Should have 2 rows (roles + cancel)
    assert len(keyboard.inline_keyboard) == 2

    # First row: 2 role buttons
    assert len(keyboard.inline_keyboard[0]) == 2

    trader_btn = keyboard.inline_keyboard[0][0]
    admin_btn = keyboard.inline_keyboard[0][1]

    assert trader_btn.text == "📊 Trader"
    assert trader_btn.callback_data == "role_change_request:trader"

    assert admin_btn.text == "⭐ Admin"
    assert admin_btn.callback_data == "role_change_request:admin"

    # Second row: cancel button
    cancel_btn = keyboard.inline_keyboard[1][0]
    assert cancel_btn.text == "❌ Cancelar"
    assert cancel_btn.callback_data == "role_change_cancel"


def test_build_role_change_keyboard_admin_only():
    """Test role change keyboard for trader (can only request admin)."""
    keyboard = build_role_change_keyboard(["admin"])

    # Should have 2 rows (1 role + cancel)
    assert len(keyboard.inline_keyboard) == 2

    # First row: 1 role button
    assert len(keyboard.inline_keyboard[0]) == 1

    admin_btn = keyboard.inline_keyboard[0][0]
    assert admin_btn.text == "⭐ Admin"
    assert admin_btn.callback_data == "role_change_request:admin"


def test_build_role_change_admin_keyboard():
    """Test admin keyboard for role change approval."""
    keyboard = build_role_change_admin_keyboard(123456, "trader")

    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2

    approve_btn = keyboard.inline_keyboard[0][0]
    deny_btn = keyboard.inline_keyboard[0][1]

    assert approve_btn.text == "✅ Aprobar"
    assert approve_btn.callback_data == "role_change_approve:123456:trader"

    assert deny_btn.text == "❌ Rechazar"
    assert deny_btn.callback_data == "role_change_deny:123456"
