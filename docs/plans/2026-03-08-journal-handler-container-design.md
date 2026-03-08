# Diseño: Actualizar journal_handler.py para usar Container

## Objetivo

Reemplazar el acceso directo a `core.database` en `bot/handlers/journal_handler.py` por el patrón de inyección de dependencias usando el container.

## Contexto Actual

El archivo `bot/handlers/journal_handler.py` usa `fetch` directamente desde `bot.core.database` para obtener señales y trades activos. El objetivo es migrar al patrón de container usado en otros handlers del proyecto.

## Cambios Requeridos

### 1. Extender Dominio Signal (`bot/domain/signal.py`)

Agregar campos adicionales al dataclass Signal:

```python
@dataclass
class Signal:
    # ... campos existentes ...
    result: str | None = None      # GANADA, PERDIDA, BREAKEVEN
    pnl_usdt: float | None = None  # Profit/Loss en USDT
```

### 2. Actualizar Repository (`bot/infrastructure/database/signal_repository.py`)

Modificar `_record_to_signal()` para mapear los campos adicionales:

```python
def _record_to_signal(record: asyncpg.Record) -> Signal:
    return Signal(
        # ... campos existentes ...
        result=record.get("result"),
        pnl_usdt=float(record["pnl_usdt"]) if record.get("pnl_usdt") else None,
    )
```

### 3. Actualizar Handler (`bot/handlers/journal_handler.py`)

Cambiar las funciones para usar el container:

```python
# Antes
from bot.core.database import fetch

async def get_signals_history(limit: int = 10, offset: int = 0):
    query = """..."""
    rows = await fetch(query, limit, offset)

# Después
async def get_signals_history(container, limit: int = 10, offset: int = 0):
    signals = await container.manage_journal.get_recent(limit=limit)
    return [signal_to_dict(s) for s in signals]
```

Helper para convertir Signal a dict:

```python
def signal_to_dict(signal: Signal) -> dict:
    return {
        "id": signal.id,
        "detected_at": signal.detected_at,
        "direction": signal.direction,
        "entry_price": signal.entry_price,
        "status": signal.status,
        "result": signal.result,
        "pnl_usdt": signal.pnl_usdt,
    }
```

### 4. Actualizar Handlers de Telegram

Pasar el context a las funciones que lo necesitan:

```python
async def journal_cmd(update: Update, context: CallbackContext) -> None:
    container = context.bot_data["container"]
    message = await journal_command(container, limit=limit, offset=offset)
```

### 5. Active Trades

Para `get_active_trades()`, verificar si existe método en container o crear uno. Por ahora mantener la implementación actual si no hay método equivalente.

## Compatibilidad

- Mantener la misma estructura de respuesta (diccionarios)
- No modificar funciones de formateo (`format_signal_line`, `calculate_journal_stats`, etc.)
- La paginación funciona igual (usa limit/offset)

## Testing

- Ejecutar tests existentes: `pytest tests/unit/test_journal_handler.py`
- Verificar que la salida de /journal sea idéntica
