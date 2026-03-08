# Security Audit Fix Design

## Fecha: 2025-04-20
## Tema: Corrección de Vulnerabilidades de Seguridad

---

## 1. Problema

La auditoría de seguridad identificó los siguientes problemas:

| ID | Severidad | Problema | Archivo |
|----|-----------|----------|---------|
| 1 | CRÍTICO | API Keys duplicadas en configuración | `bot/core/config.py` |
| 2 | ALTO | Uso de `requests` síncrono en contexto async | `bot/core/api_client.py` |
| 3 | MEDIO | Spam de solicitudes de acceso sin rate limiting | `bot/core/access_manager.py` |
| 4 | MEDIO | Comandos admin sin protección contra rate limiting | `bot/handlers/access_admin.py` |

---

## 2. Solución Propuesta

### Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Update                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              AccessManager (Middleware)                  │
│  • Verifica estado usuario                              │
│  • Aplica rate limiting (aiolimiter)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐         ┌──────────────────┐
│ Rate Limited  │         │ Rate Limited     │
│ Notificaciones│         │ Comandos Admin   │
│ (1 req/10s)   │         │ (5 req/min)      │
└───────────────┘         └──────────────────┘
```

---

## 3. Componentes a Modificar

### 3.1 Fix config.py (Critical)

- Eliminar las líneas duplicadas de `cmc_api_key_alerta` y `cmc_api_key_control`

### 3.2 Rate Limiter Module (Nuevo)

**Archivo**: `bot/utils/rate_limiter.py`

- Usar librería `aiolimiter` para rate limiting async
- Crear wrapper reutilizable para diferentes contextos
- Limitar notificaciones a admins: 1 req / 10 segundos
- Limitar comandos admin: 5 req / minuto

### 3.3 AccessManager (Middleware)

**Archivo**: `bot/core/access_manager.py`

- Integrar rate limiter para notificaciones a admins
- Prevenir spam de solicitudes de acceso
- Usar cooldown mechanism

### 3.4 Access Admin Handlers

**Archivo**: `bot/handlers/access_admin.py`

- Agregar rate limiting a comandos sensibles
- Proteger contra abuso

### 3.5 API Client Migration

**Archivo**: `bot/core/api_client.py`

- Migrar de `requests` a `httpx` async
- Mantener compatibilidad hacia atrás donde sea posible

---

## 4. Dependencias

```toml
# pyproject.toml
aiolimiter = "^1.1.0"
httpx = "^0.27.0"
```

---

## 5. Testing

- Tests unitarios para rate limiter
- Tests de integración para AccessManager
- Verificar que no se rompan funcionalidades existentes

---

## 6. Éxito

- [ ] Duplicados de config eliminados
- [ ] Rate limiting implementado y funcionando
- [ ] API client migrado a async
- [ ] Todos los tests pasando
- [ ] Linting sin errores