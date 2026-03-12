# Referral System Design - Comando `/ref`

**Fecha:** 2026-03-12
**Estado:** Aprobado
**Autor:** SipSignal Development Team

---

## 1. Overview

### 1.1 Objetivo

Implementar un sistema de referidos para tracking orgánico del crecimiento de usuarios en SipSignal. El sistema permite que usuarios aprobados inviten nuevos usuarios mediante un código único y enlace personalizado.

### 1.2 Alcance

- **Incluye:**
  - Generación de códigos de referido únicos por usuario
  - Enlace de invitación personalizado (`t.me/sipsignal_bot?start=<codigo>`)
  - Tracking de qué usuario refirió a cuál
  - Comando `/ref` para mostrar código y estadísticas
  - Modificación del comando `/start` para aceptar códigos de referido

- **No incluye:**
  - Recompensas económicas o de capital
  - Sistema de comisiones o afiliados
  - Features premium por referidos
  - Múltiples niveles de referidos (solo nivel 1)

---

## 2. Arquitectura de Base de Datos

### 2.1 Nueva Tabla: `referrals`

```sql
CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(referrer_id, referred_id)
);

CREATE INDEX idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX idx_referrals_referred_id ON referrals(referred_id);
```

**Propósito:** Registrar cada relación de referido de forma explícita y permitir consultas eficientes.

### 2.2 Modificaciones a `users`

```sql
ALTER TABLE users ADD COLUMN referrer_code VARCHAR(32) UNIQUE;
ALTER TABLE users ADD COLUMN referred_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE INDEX idx_users_referrer_code ON users(referrer_code);
```

**Campos:**
- `referrer_code`: Código único del usuario (generado al primer uso de `/ref`)
- `referred_by`: ID del usuario que lo refirió (NULL si no fue referido)

---

## 3. Componentes del Sistema

### 3.1 Estructura de Archivos

```
bot/
├── domain/
│   └── ports/
│       └── repositories.py          # Añadir ReferralRepository (interface)
├── infrastructure/
│   └── database/
│       └── referral_repository.py   # PostgreSQLReferralRepository
├── handlers/
│   └── referral_handler.py          # Handler comando /ref
├── utils/
│   └── referral_code.py             # Generador de códigos únicos
└── main.py                          # Registrar nuevo handler
```

### 3.2 ReferralRepository Interface

```python
class ReferralRepository(ABC):
    @abstractmethod
    async def get_referrer_code(self, user_id: int) -> str | None:
        """Obtener código de referido de un usuario."""
        ...

    @abstractmethod
    async def generate_referrer_code(self, user_id: int) -> str:
        """Generar y guardar código único para usuario."""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> int | None:
        """Obtener user_id desde código de referido."""
        ...

    @abstractmethod
    async def record_referral(self, referrer_id: int, referred_id: int) -> None:
        """Registrar nueva relación de referido."""
        ...

    @abstractmethod
    async def get_referrals(self, referrer_id: int) -> list[dict]:
        """Obtener lista de usuarios referidos."""
        ...

    @abstractmethod
    async def get_referral_count(self, referrer_id: int) -> int:
        """Obtener cantidad total de referidos."""
        ...

    @abstractmethod
    async def get_referrer(self, referred_id: int) -> int | None:
        """Obtener el ID de quien refirió a un usuario."""
        ...
```

### 3.3 Generador de Códigos

```python
# bot/utils/referral_code.py
import secrets
import string

def generate_referral_code(length: int = 8) -> str:
    """
    Genera un código de referido único y legible.

    Usa solo caracteres alfanuméricos en mayúsculas,
    excluyendo caracteres confusos (0, O, I, L).
    """
    alphabet = string.ascii_uppercase + string.digits
    # Excluir caracteres confusos
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('L', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```

---

## 4. Flujo de Usuario

### 4.1 Usuario ejecuta `/ref`

```
┌─────────────┐
│ Usuario     │
│ ejecuta     │
│ /ref        │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ Handler verifica si usuario │
│ tiene código de referido    │
└──────┬──────────────────────┘
       │
       ├───────┐
       │       │
       ▼       ▼
   ¿Existe?  No existe
       │       │
       │       ▼
       │  ┌────────────────────┐
       │  │ Generar código     │
       │  │ único y guardar    │
       │  └────────┬───────────┘
       │           │
       ▼           ▼
   ┌──────────────────────────┐
   │  Mostrar mensaje con:    │
   │  • Código de referido    │
   │  • Enlace directo        │
   │  • Estadísticas básicas  │
   └──────────────────────────┘
```

### 4.2 Nuevo usuario se registra con referido

```
┌─────────────────────────────────┐
│ Nuevo usuario hace clic en      │
│ enlace: t.me/sipsignal_bot?     │
│ start=ABC123XYZ                 │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Bot recibe /start ABC123XYZ │
│ (arg = código de referido)  │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Validar código existe       │
│ y obtener referrer_id       │
└──────┬──────────────────────┘
       │
       ├────────────┐
       │            │
       ▼            ▼
   ¿Válido?     Inválido
       │            │
       │            ▼
       │       ┌────────────┐
       │       │ Ignorar    │
       │       │ código     │
       │       │ continuar  │
       │       │ registro   │
       │       └────────────┘
       ▼
┌─────────────────────────────┐
│ Registrar usuario con       │
│ referred_by = referrer_id   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Insertar en tabla referrals │
│ (referrer_id, referred_id)  │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Completar registro normal   │
│ (mensaje de bienvenida)     │
└─────────────────────────────┘
```

---

## 5. Diseño de Comandos

### 5.1 Comando `/ref`

**Acceso:** Usuarios con estado `approved` o superior (`admin`, `trader`)

**Formato de respuesta:**

```
🔗 *TU ENLACE DE REFERIDO*
─────────────────────

Tu código: `{code}`

Enlace directo:
t.me/sipsignal_bot?start={code}

Comparte este enlace para invitar amigos a SipSignal.

📊 *Estadísticas:*
• Referidos totales: {count}
• Último referido: {last_referred_username} ({time_ago})

─────────────────────
Usa /ref stats para ver lista completa
```

**Casos especiales:**

| Escenario | Respuesta |
|-----------|-----------|
| Usuario no aprobado | "⛔ Acceso denegado. Solo usuarios aprobados pueden usar referidos." |
| Usuario sin código | Generar código automáticamente y mostrar mensaje |
| 0 referidos | "📊 *Estadísticas:*\n• Referidos totales: 0\n\n¡Comparte tu enlace para comenzar!" |

### 5.2 Sub-comando `/ref stats`

**Propósito:** Mostrar lista detallada de referidos

**Formato:**

```
📊 *TUS REFERIDOS* ({total})
─────────────────────

1. @usuario1 - {date}
2. @usuario2 - {date}
3. @usuario3 - {date}
...

─────────────────────
Total: {total} referidos
```

**Paginación:** Si hay más de 10 referidos, mostrar de 10 en 10 con botones de navegación.

---

## 6. Error Handling

| Escenario | Manejo |
|-----------|--------|
| **Código inválido** | Ignorar silenciosamente, continuar registro normal sin referido |
| **Usuario ya tiene referido** | No permitir cambio (primero gana), loggear intento |
| **Auto-referido** | Bloquear (mismo user_id), mostrar mensaje de error |
| **Código duplicado** | Regenerar código único (retry con backoff) |
| **Usuario no existe** | Ignorar código, continuar registro normal |

---

## 7. Migración de Base de Datos

**Archivo:** `bot/db/migrations/004_referral_system.sql`

```sql
-- 1. Añadir columnas a users
ALTER TABLE users
ADD COLUMN referrer_code VARCHAR(32) UNIQUE,
ADD COLUMN referred_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_users_referrer_code ON users(referrer_code);
CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);

-- 2. Crear tabla referrals
CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(referrer_id, referred_id)
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);

-- 3. Comentario de documentación
COMMENT ON TABLE referrals IS 'Tracking de referidos entre usuarios';
COMMENT ON COLUMN users.referrer_code IS 'Código único para referidos';
COMMENT ON COLUMN users.referred_by IS 'ID del usuario que lo refirió';
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Archivo:** `tests/unit/test_referral_code.py`

```python
def test_generate_referral_code_format():
    """Código debe ser alfanumérico, 8 caracteres, sin caracteres confusos."""
    code = generate_referral_code()
    assert len(code) == 8
    assert code.isalnum()
    assert all(c not in '0OIL' for c in code)

def test_generate_referral_code_unique():
    """Códigos generados deben ser únicos."""
    codes = [generate_referral_code() for _ in range(1000)]
    assert len(codes) == len(set(codes))
```

### 8.2 Integration Tests

**Archivo:** `tests/integration/test_referral_flow.py`

```python
async def test_referral_registration_flow():
    """Flujo completo: generar código → registrar con referido → verificar."""
    # 1. Generar código para usuario existente
    # 2. Registrar nuevo usuario con código
    # 3. Verificar referred_by correcto
    # 4. Verificar entrada en tabla referrals
    pass

async def test_self_referral_blocked():
    """Auto-referido debe ser bloqueado."""
    pass

async def test_invalid_code_ignored():
    """Código inválido no debe romper registro."""
    pass
```

---

## 9. Consideraciones de Seguridad

1. **Códigos únicos:** Usar `secrets` module (no `random`) para generación criptográficamente segura
2. **Validación de entrada:** Sanitizar código recibido en `/start`
3. **Rate limiting:** Prevenir abuso en generación de códigos (máx 1 por usuario)
4. **Acceso:** Solo usuarios aprobados pueden usar `/ref`

---

## 10. Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| Códigos generados | >50% de usuarios aprobados |
| Tasa de conversión | >20% de clicks en enlaces → registro |
| Referidos por usuario | >1.5 promedio |

---

## 11. Dependencias Externas

- **PostgreSQL:** Versión actual del proyecto (soporta ON CONFLICT)
- **Python 3.13+:** Módulo `secrets` disponible
- **Telegram Bot API:** Soporte para deep linking (`start=` parameter)

---

## 12. Aprobación

**Aprobado por:** Usuario
**Fecha de aprobación:** 2026-03-12
**Próximos pasos:** Invocar `writing-plans` para plan de implementación
