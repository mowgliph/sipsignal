# Diseño: Actualizar signal_response_handler.py para usar Container DI

## Fecha: 2026-03-07

## Contexto

El handler `signal_response_handler.py` actualmente usa llamadas directas a la base de datos (`fetchrow`, `execute` de `bot.core.database`) para manejar los callbacks de decisiones del trader.

## Problema

El código viola el patrón de inyección de dependencias implementado en el proyecto, donde todos los handlers deben obtener recursos a través del `Container`.

## Solución

### 1. Modificar `ManageJournal.mark_skipped()`

Agregar parámetro opcional `status` para permitir flexibilidad:

```python
async def mark_skipped(self, signal_id: int, status: str = "CANCELADA") -> None:
    await self._signal_repo.update_status(signal_id, status)
```

### 2. Actualizar `_handle_taken`

Reemplazar:
```python
from bot.core.database import fetchrow, execute
signal = await fetchrow("SELECT * FROM signals WHERE detected_at = $1 AND status = 'EMITIDA' ORDER BY id DESC LIMIT 1", detected_dt)
await execute("UPDATE signals SET status = 'TOMADA', taken_at = NOW(), updated_at = NOW() WHERE id = $1", signal_id)
```

Con:
```python
container = context.bot_data["container"]
signal = await container.signal_repo.get_by_id(signal_id)
await container.manage_journal.mark_taken(signal_id)
```

**Nota:** Mantener la lógica de creación de `active_trade` ya que es parte del flujo de negocio.

### 3. Actualizar `_handle_skipped`

Reemplazar:
```python
signal = await fetchrow(...)
await execute("UPDATE signals SET status = 'NO_TOMADA'...")
```

Con:
```python
container = context.bot_data["container"]
signal = await container.signal_repo.get_by_id(signal_id)
await container.manage_journal.mark_skipped(signal_id, "NO_TOMADA")
```

### 4. Actualizar `_handle_detail`

Reemplazar:
```python
signal = await fetchrow(...)
```

Con:
```python
container = context.bot_data["container"]
signal = await container.signal_repo.get_by_id(signal_id)
```

## Beneficios

- Elimina dependencias directas a `bot.core.database`
- Sigue el patrón de DI ya establecido en el proyecto
- Mantiene la lógica de negocio existente
- Código más testeable y mantenible
