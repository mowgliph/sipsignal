# Diseño: Actualizar capital_handler.py para usar HandleDrawdown

## Fecha: 2026-03-08

## Objetivo

Reemplazar llamadas directas a funciones de `trading/drawdown_manager.py` por el caso de uso `HandleDrawdown` del container en `bot/handlers/capital_handler.py`.

## Contexto

El archivo `capital_handler.py` actualmente usa funciones directas del módulo `drawdown_manager`:
- `get_drawdown()`
- `is_trading_paused()`
- `resume_trading()`
- `reset_drawdown()`

El proyecto cuenta con un caso de uso `HandleDrawdown` registrado en el container que encapsula esta lógica.

## Diseño

### 1. Imports

**Antes:**
```python
from bot.trading.drawdown_manager import (
    get_drawdown,
    is_trading_paused,
    reset_drawdown,
    resume_trading,
)
```

**Después:**
- Eliminar imports de `drawdown_manager`
- Agregar acceso al container: `container = context.bot_data["container"]`

### 2. Funciones a modificar

| Función | Cambio |
|---------|--------|
| `capital_command` | Mantener `get_drawdown` (necesario para mostrar estado) |
| `resume_command` | Usar `container.handle_drawdown.resume(user_id)` |
| `resetdd_command` | Mantener `get_drawdown` para verificar estado |
| `resetdd_callback` | Usar `container.handle_drawdown.reset(user_id)` |

### 3. Patrón de acceso al container

Seguir el mismo patrón usado en otros handlers:
```python
container = context.bot_data["container"]
```

### 4. Consideraciones

- No modificar la lógica de los botones inline
- No modificar el formato de los mensajes
- Mantener el manejo de errores existente

## Referencias

- `bot/application/handle_drawdown.py` - Caso de uso
- `bot/container.py` - Registro del container
- `bot/handlers/signal_handler.py` - Ejemplo de patrón de acceso
