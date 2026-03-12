# Access Control Inline Buttons Design

**Date:** 2026-03-11
**Status:** Approved
**Author:** SipSignal Team

---

## Overview

Mejora del sistema de control de acceso del bot SipSignal mediante botones inline interactivos y un sistema de roles granular.

### Problem Statement

El sistema actual requiere que los admins escriban comandos de texto (`/approve <id>`) para aprobar usuarios. No hay asignación de roles ni control granular sobre qué comandos puede usar cada usuario. Además, no existe un mecanismo para que usuarios existentes soliciten cambio de rol.

### Goals

1. ✅ Botones inline para aprobar/rechazar solicitudes
2. ✅ Menú de selección de roles (Viewer, Trader, Admin)
3. ✅ Notificación a usuarios sobre aprobación/rechazo
4. ✅ Control de acceso granular por rol
5. ✅ Corrección de decoradores inconsistentes
6. ✅ Sistema de solicitud de cambio de rol para viewer/trader

---

## Architecture

### Status → Role Mapping

| Status DB | Rol | Descripción |
|-----------|-----|-------------|
| `non_permitted` | Ninguno | Sin acceso a comandos |
| `pending` | Pendiente | Solicitud de acceso inicial |
| `viewer` | Viewer | Comandos básicos (info general) |
| `trader` | Trader | Todos menos admin |
| `admin` | Admin | Acceso total |
| `role_change_pending` | Pendiente | Solicitud de cambio de rol (BLOQUEADO) |

### Role Hierarchy

```
viewer ⊂ trader ⊂ admin
```

### Role Change Request Flow

| Rol Actual | Puede Solicitar | Requiere Aprobación | Estado Durante Espera |
|------------|-----------------|---------------------|----------------------|
| `viewer` | `trader`, `admin` | ✅ Sí | `role_change_pending` (bloqueado) |
| `trader` | `admin` | ✅ Sí | `role_change_pending` (bloqueado) |
| `admin` | ❌ No puede | N/A | N/A |

**Nota:** Admin no puede auto-cambiarse. Otro admin debe hacerlo con `/make_admin` o `/set_role`.

---

## Command Matrix

### Generales (Todos los usuarios)

| Comando | Viewer | Trader | Admin | role_change_pending |
|---------|--------|--------|-------|---------------------|
| `/start` | ✅ | ✅ | ✅ | ✅ |
| `/help` | ✅ | ✅ | ✅ | ✅ |
| `/myid` | ✅ | ✅ | ✅ | ✅ |
| `/lang` | ✅ | ✅ | ✅ | ✅ |
| `/change_role` | ✅ | ✅ | ❌ | ❌ |
| `/my_role` | ✅ | ✅ | ✅ | ✅ |

### Análisis y Trading (Trader + Admin)

| Comando | Viewer | Trader | Admin | Decorador |
|---------|--------|--------|-------|-----------|
| `/ta <symbol>` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/mk` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/p <symbol>` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/signal` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/chart [tf]` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/scenario` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |

### Gestión de Trading (Trader + Admin)

| Comando | Viewer | Trader | Admin | Decorador |
|---------|--------|--------|-------|-----------|
| `/journal` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/active` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/capital` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/resume` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/resetdd` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |
| `/setup` | ❌ | ✅ | ✅ | `@role_required(['trader', 'admin'])` |

### Administración (Solo Admin)

| Comando | Viewer | Trader | Admin | Decorador |
|---------|--------|--------|-------|-----------|
| `/users` | ❌ | ❌ | ✅ | `@admin_only` |
| `/logs` | ❌ | ❌ | ✅ | `@admin_only` |
| `/status` | ❌ | ❌ | ✅ | `@admin_only` |
| `/ad` | ❌ | ❌ | ✅ | `@admin_only` |
| `/ms` | ❌ | ❌ | ✅ | `@admin_only` |
| `/approve <id>` | ❌ | ❌ | ✅ | `@admin_only` |
| `/deny <id>` | ❌ | ❌ | ✅ | `@admin_only` |
| `/make_admin <id>` | ❌ | ❌ | ✅ | `@admin_only` |
| `/list_users [filter]` | ❌ | ❌ | ✅ | `@admin_only` |
| `/set_role <id> <role>` | ❌ | ❌ | ✅ | `@admin_only` |

### Cambio de Rol (Viewer + Trader)

| Comando | Viewer | Trader | Admin | Decorador |
|---------|--------|--------|-------|-----------|
| `/change_role` | ✅ | ✅ | ❌ | `@permitted_only` |
| `/my_role` | ✅ | ✅ | ✅ | Ninguno |

---

## Components

### 1. New Decorator: `@role_required`

**File:** `bot/utils/decorators.py`

```python
def role_required(allowed_roles: list[str]) -> Callable:
    """
    Decorator to restrict command access to specific roles.

    Args:
        allowed_roles: List of allowed roles (e.g., ['trader', 'admin'])

    Example:
        @role_required(['trader', 'admin'])
        async def signal_command(update, context):
            ...
    """
```

**Implementation:**
- Fetch user from DB
- Check if `user['status']` is in `allowed_roles`
- Send "Access denied" if not permitted
- Execute command if permitted

---

### 2. Inline Keyboards

**File:** `bot/utils/inline_keyboards.py` (new)

```python
def build_access_keyboard(user_chat_id: int) -> InlineKeyboardMarkup:
    """Build keyboard with Approve/Deny buttons."""
    # [✅ Aprobar] [❌ Rechazar]

def build_role_keyboard(user_chat_id: int) -> InlineKeyboardMarkup:
    """Build keyboard with role selection buttons."""
    # [👁️ Viewer] [📊 Trader] [⭐ Admin]
    # [❌ Cancelar]

def build_role_change_keyboard(available_roles: list[str]) -> InlineKeyboardMarkup:
    """Build keyboard for role change request."""
    # [📊 Trader] [⭐ Admin] (excludes current role)
    # [❌ Cancelar]

def build_role_change_admin_keyboard(user_chat_id: int, new_role: str) -> InlineKeyboardMarkup:
    """Build approve/deny keyboard for admin role change notification."""
    # [✅ Aprobar] [❌ Rechazar]
```

---

### 3. Callback Handlers

**File:** `bot/handlers/access_callbacks.py` (new)

| Callback Pattern | Handler | Action |
|------------------|---------|--------|
| `access_approve:<chat_id>` | `access_approve_callback` | Show role selection menu |
| `access_deny:<chat_id>` | `access_deny_callback` | Deny user access |
| `role_set:<chat_id>:<role>` | `role_set_callback` | Set user role and notify |
| `role_cancel` | `role_cancel_callback` | Cancel role selection |

---

### 4. Role Change Handlers

**File:** `bot/handlers/role_change.py` (new)

| Comando | Handler | Descripción |
|---------|---------|-------------|
| `/change_role` | `change_role_command` | Show role change menu (viewer/trader only) |
| `/my_role` | `my_role_command` | Show current role and permissions |

**File:** `bot/handlers/role_change_callbacks.py` (new)

| Callback Pattern | Handler | Action |
|------------------|---------|--------|
| `role_change_request:<role>` | `role_change_request_callback` | Create role change request, notify admins |
| `role_change_approve:<user_id>:<role>` | `role_change_approve_callback` | Approve role change |
| `role_change_deny:<user_id>` | `role_change_deny_callback` | Deny role change, restore previous role |
| `role_change_cancel` | `role_change_cancel_callback` | Cancel role change request |

---

### 5. Database Functions

**File:** `bot/db/users.py`

```python
async def set_user_role(user_id: int, role: str) -> bool:
    """
    Set user's role (status).

    Args:
        user_id: Telegram user ID
        role: One of 'viewer', 'trader', 'admin'

    Returns:
        True if successful
    """

async def request_role_change(user_id: int, new_role: str) -> bool:
    """
    Mark user as role_change_pending with requested role.

    Args:
        user_id: Telegram user ID
        new_role: Requested role ('viewer', 'trader', 'admin')

    Returns:
        True if successful
    """
    # Sets: status='role_change_pending', requested_role=new_role, previous_role=current_role

async def approve_role_change(user_id: int, new_role: str) -> bool:
    """
    Approve role change and set new role.

    Args:
        user_id: Telegram user ID
        new_role: New role to assign

    Returns:
        True if successful
    """
    # Sets: status=new_role, requested_role=NULL, previous_role=NULL

async def deny_role_change(user_id: int) -> bool:
    """
    Deny role change and restore previous role.

    Args:
        user_id: Telegram user ID

    Returns:
        True if successful
    """
    # Sets: status=previous_role, requested_role=NULL, previous_role=NULL
```

---

### 5. AccessManager Updates

**File:** `bot/core/access_manager.py`

**Changes:**
- Update admin notification to include inline buttons
- Maintain backward compatibility with `/approve`, `/deny` commands
- **NEW:** Handle `role_change_pending` status (block commands except /help, /change_role, /my_role)

**Before:**
```
🔔 Nueva Solicitud de Acceso
Chat ID: `123456`
Username: @usuario
Comandos sugeridos:
/approve 123456
/deny 123456
```

**After:**
```
🔔 Nueva Solicitud de Acceso
Chat ID: `123456`
Username: @usuario

[✅ Aprobar] [❌ Rechazar]
```

**Role Change Pending Behavior:**
```python
if status == "role_change_pending":
    # BLOCK all commands except /help, /change_role, /my_role
    if update.message and update.message.text in ("/help", "/change_role", "/my_role"):
        return True  # Allow these commands
    await self._send_message(
        bot, chat_id,
        "⏳ Tu solicitud de cambio de rol está siendo revisada. "
        "No puedes usar otros comandos hasta que sea aprobada."
    )
    return False
```

---

### 6. User Notifications

**Approval Message (Initial Access):**
```
✅ ¡Tu acceso ha sido APROBADO!

Rol asignado: {rol_emoji} {rol_nombre}

Comandos disponibles:
• /help - Ver ayuda
• /ta <symbol> - Análisis técnico
• /journal - Historial de señales
... (según rol)

¡Empieza con /help para más información!
```

**Rejection Message:**
```
❌ Tu solicitud de acceso ha sido RECHAZADA.

Si crees que es un error, contacta al administrador.
```

**Role Change Approval Message:**
```
✅ Tu rol ha sido actualizado!

Rol anterior: {old_role_emoji} {old_role}
Nuevo rol: {new_role_emoji} {new_role}

Comandos disponibles:
• /help - Ver ayuda
... (lista según nuevo rol)
```

**Role Change Rejection Message:**
```
❌ Tu solicitud de cambio de rol ha sido RECHAZADA.

Tu rol actual se mantiene: {current_role}
```

---

### 7. Admin Notifications (Role Change)

**Notification Message:**
```
🔔 @usuario solicita cambio de rol

Rol actual: 👁️ Viewer
Rol solicitado: 📊 Trader
Usuario: BLOQUEADO hasta aprobación

[✅ Aprobar] [❌ Rechazar]
```

---

## Decorator Migration Plan

### Commands to Update

| File | Command | Old Decorator | New Decorator |
|------|---------|---------------|---------------|
| `signal_handler.py` | `/signal` | `@admin_only` | `@role_required(['trader', 'admin'])` |
| `chart_handler.py` | `/chart` | `@admin_only` | `@role_required(['trader', 'admin'])` |
| `scenario_handler.py` | `/scenario` | `@admin_only` | `@role_required(['trader', 'admin'])` |
| `ta.py` | `/ta` | `@permitted_only` | `@role_required(['trader', 'admin'])` |
| `trading.py` | `/mk`, `/p` | `@permitted_only` | `@role_required(['trader', 'admin'])` |
| `journal_handler.py` | `/journal`, `/active` | `@permitted_only` | `@role_required(['trader', 'admin'])` |
| `capital_handler.py` | `/capital`, `/resume`, `/resetdd` | `@permitted_only` | `@role_required(['trader', 'admin'])` |
| `setup_handler.py` | `/setup` | None | `@role_required(['trader', 'admin'])` |
| `role_change.py` | `/change_role` | None | `@permitted_only` |
| `role_change.py` | `/my_role` | None | None |

---

## Database Migration

**New Columns Required:**

```sql
-- Add requested_role column for tracking role change requests
ALTER TABLE users
ADD COLUMN requested_role VARCHAR(20) NULL;

-- Add previous_role column for restoring on denial
ALTER TABLE users
ADD COLUMN previous_role VARCHAR(20) NULL;

-- Update status column to support new role_change_pending status
-- (already VARCHAR(20), no change needed)
```

**New Status Values:**
- `non_permitted` - No access
- `pending` - Initial access request pending
- `viewer` - Basic access
- `trader` - Full trading access
- `admin` - Admin access
- `role_change_pending` - Role change request pending (BLOCKED)

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Callback without original message | Send new message |
| User not found | "❌ Usuario no encontrado" |
| Admin without permissions | "⛔ No tienes permisos para asignar este rol" |
| Rate limiting | Keep existing from `access_admin.py` |
| Invalid role selection | Log error, don't update DB |
| Admin tries /change_role | "⛔ Los administradores no pueden solicitar cambio de rol" |
| User already pending | "⏳ Ya tienes una solicitud pendiente" |
| role_change_pending tries blocked command | "⏳ Tu solicitud está siendo revisada. No puedes usar otros comandos." |

---

## Testing Strategy

### Unit Tests

1. **`test_decorators.py`**
   - Test `@role_required` with allowed roles
   - Test `@role_required` with denied roles
   - Test edge cases (user not found, invalid status)

2. **`test_access_callbacks.py`**
   - Test approve callback
   - Test deny callback
   - Test role selection callback
   - Test cancel callback

3. **`test_inline_keyboards.py`**
   - Test keyboard structure
   - Test callback data format

4. **`test_role_change.py`** (NEW)
   - Test `/change_role` command (viewer/trader can use, admin cannot)
   - Test `/my_role` command
   - Test role change request callback
   - Test role change approve callback
   - Test role change deny callback
   - Test `role_change_pending` blocks commands

5. **`test_access_manager.py`** (UPDATED)
   - Test `role_change_pending` status blocks correctly
   - Test exceptions for /help, /change_role, /my_role

### Integration Tests

1. **Access Request Flow**
   - User requests access → Admin notified with buttons
   - Admin approves → Role selection shown
   - Admin selects role → User notified

2. **Command Access**
   - Viewer tries trader command → Denied
   - Trader tries admin command → Denied
   - Admin tries any command → Allowed

3. **Role Change Flow** (NEW)
   - Viewer requests trader → Admin notified
   - Admin approves → User updated to trader
   - User notified of role change

4. **Role Change Rejection Flow** (NEW)
   - Trader requests admin → Admin notified
   - Admin denies → User restored to trader
   - User notified of rejection

5. **Role Change Pending Blocking** (NEW)
   - User requests role change → Status = `role_change_pending`
   - User tries `/ta` → Denied with message
   - User tries `/help` → Allowed
   - User tries `/change_role` → Allowed (show status)

---

## Rollback Plan

If issues arise:

1. **Revert decorators** → Keep `@admin_only` and `@permitted_only`
2. **Disable inline buttons** → Admins use text commands
3. **DB migration rollback:**
   ```sql
   ALTER TABLE users DROP COLUMN requested_role;
   ALTER TABLE users DROP COLUMN previous_role;
   ```
4. **Revert AccessManager changes** → Remove `role_change_pending` handling

---

## Success Metrics

- [ ] Admins can approve users with 1-2 clicks (vs writing commands)
- [ ] Users receive clear notification of approval/rejection
- [ ] Role-based access control working correctly
- [ ] All decorators updated and tested
- [ ] No regression in existing functionality
- [ ] Role change request flow works end-to-end
- [ ] `role_change_pending` status blocks commands correctly
- [ ] Admins can approve/deny role changes with inline buttons

---

## References

- Existing: `bot/core/access_manager.py`
- Existing: `bot/handlers/access_admin.py`
- Existing: `bot/db/users.py`
- Existing: `bot/utils/decorators.py`

**New Files:**
- `bot/handlers/role_change.py`
- `bot/handlers/role_change_callbacks.py`
- `bot/utils/inline_keyboards.py`
- `tests/unit/test_role_change.py`
