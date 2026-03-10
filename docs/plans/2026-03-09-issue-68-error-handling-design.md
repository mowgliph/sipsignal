# Diseño de Refactorización: Manejo de Errores y Visibilidad Operativa (Issue #68)

**Fecha:** 2026-03-09
**Estado:** Aprobado
**Objetivo:** Eliminar 93 bloques `except Exception` genéricos para lograr **Visibilidad Operativa Total** y seguridad en el trading.

---

## 1. Clasificación de Errores y Reacciones

Implementaremos una estrategia de tres niveles para categorizar cada fallo detectado:

### Nivel 1: Crítico (Trading e Integridad de Datos)
*   **Módulos:** `bot/trading/`, `bot/db/`, `bot/infrastructure/database/`.
*   **Excepciones:** `asyncpg.PostgresError`, `TradeError` (custom), fallos de integridad.
*   **Acción:**
    1. Registro completo con `logger.exception` (stack trace).
    2. Alerta inmediata al Admin via Telegram con detalles del fallo.
    3. Propagación o detención controlada del ciclo para evitar daños al capital.

### Nivel 2: Operativo (APIs Externas y Análisis)
*   **Módulos:** `bot/infrastructure/binance/`, `bot/infrastructure/groq/`, `bot/core/btc_advanced_analysis.py`.
*   **Excepciones:** `aiohttp.ClientError`, `json.JSONDecodeError`, `TimeoutError`.
*   **Acción:**
    1. Registro como `logger.warning`.
    2. Aplicación de lógica de reintento o uso de `fallback_value` (ej. `0.0`, `None`).
    3. Notificación al Admin solo si el fallo persiste tras varios reintentos.

### Nivel 3: Interfaz (Telegram Handlers)
*   **Módulos:** `bot/handlers/`.
*   **Excepciones:** `telegram.error.TelegramError`.
*   **Acción:**
    1. Registro como `logger.info` o `logger.error`.
    2. Envío de mensaje amigable al usuario indicando el error ("Inténtelo de nuevo").
    3. Evitar que el handler se detenga abruptamente.

---

## 2. Componentes Técnicos

### A. Decorador de Gestión de Errores (`@handle_errors`)
Se creará un decorador centralizado en `bot/utils/decorators.py` que permita:
- Especificar qué excepciones capturar.
- Definir el nivel de log (INFO, WARNING, ERROR).
- Activar/desactivar la alerta al Admin.
- Definir un valor de retorno por defecto.

### B. Sistema de Alertas Técnicas
Integración con `NotifierPort` para enviar alertas específicas de sistema al `ADMIN_ID` configurado en el `.env`, separando el ruido técnico de las señales de trading.

---

## 3. Plan de Acción (Resumen)

1.  **Auditoría Técnica:** Identificar los 10 bloques de mayor riesgo (Trading/DB) para refactorización manual inmediata.
2.  **Infraestructura:** Implementar el decorador `@handle_errors` y la lógica de alertas al Admin.
3.  **Refactorización Masiva:** Aplicar el decorador o especialización de excepciones en los 83 bloques restantes de forma iterativa.
4.  **Validación:** Pruebas de estrés inyectando errores en la DB y APIs para confirmar que las alertas y logs funcionan según lo diseñado.

---

## 4. Criterios de Éxito
- Cero bloques `except Exception:` sin logging.
- El Admin recibe una notificación clara en Telegram ante cualquier fallo en el motor de trading.
- Los logs permiten identificar el archivo y línea exacta del error sin ambigüedad.
