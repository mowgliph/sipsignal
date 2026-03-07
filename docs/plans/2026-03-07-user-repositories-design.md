# Diseño: PostgreSQLUserConfigRepository y PostgreSQLDrawdownRepository

## Fecha
2026-03-07

## Objetivo
Implementar dos repositorios PostgreSQL en `bot/infrastructure/database/user_repositories.py` que implementen las interfaces `UserConfigRepository` y `DrawdownRepository`.

## Ubicación
- Archivo: `bot/infrastructure/database/user_repositories.py`

## PostgreSQLUserConfigRepository

### Herencia
Hereda de `UserConfigRepository` (ABC en `bot/domain/ports/repositories.py`).

### Métodos

#### `get(user_id: int) -> UserConfig | None`
```sql
SELECT * FROM user_config WHERE user_id = $1
```
- Mapea el `asyncpg.Record` a `UserConfig`
- Retorna `None` si no existe

#### `save(config: UserConfig) -> UserConfig`
```sql
INSERT INTO user_config
(user_id, capital_total, risk_percent, max_drawdown_percent, direction, timeframe_primary, setup_completed, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (user_id) DO UPDATE SET
    capital_total = EXCLUDED.capital_total,
    risk_percent = EXCLUDED.risk_percent,
    max_drawdown_percent = EXCLUDED.max_drawdown_percent,
    direction = EXCLUDED.direction,
    timeframe_primary = EXCLUDED.timeframe_primary,
    setup_completed = EXCLUDED.setup_completed,
    updated_at = EXCLUDED.updated_at
```
- Usa el mismo patrón `ON CONFLICT` de `bot/db/user_config.py`
- Retorna el `UserConfig` guardado

## PostgreSQLDrawdownRepository

### Herencia
Hereda de `DrawdownRepository` (ABC en `bot/domain/ports/repositories.py`).

### Métodos

#### `get(user_id: int) -> DrawdownState | None`
```sql
SELECT dt.*, uc.capital_total, uc.max_drawdown_percent 
FROM drawdown_tracker dt 
LEFT JOIN user_config uc ON dt.user_id = uc.user_id 
WHERE dt.user_id = $1
```
- Mapea a `DrawdownState`
- Los campos `capital_total` y `max_drawdown_percent` vienen de `user_config` pero no se mapean a `DrawdownState` (ese dominio es independiente)

#### `save(state: DrawdownState) -> DrawdownState`
```sql
UPDATE drawdown_tracker 
SET current_drawdown_usdt=$1, 
    current_drawdown_percent=$2, 
    losses_count=$3, 
    is_paused=$4, 
    updated_at=NOW() 
WHERE user_id=$5
```
- Si no existe la fila, hacer `INSERT`

#### `reset(user_id: int) -> DrawdownState`
```sql
UPDATE drawdown_tracker 
SET current_drawdown_usdt=0, 
    current_drawdown_percent=0, 
    losses_count=0, 
    is_paused=false, 
    last_reset_at=NOW(), 
    updated_at=NOW() 
WHERE user_id=$1
```
- Retorna el estado actualizado

## Patrón de implementación

Seguir el mismo patrón que `PostgreSQLSignalRepository` y `PostgreSQLActiveTradeRepository`:
- Usar funciones helper `_record_to_*` para mapeo
- Usar `bot.core.database` para queries (`execute`, `fetchrow`)
- Imports: `asyncpg`, `bot.core.database`, clases de dominio

## Dependencias
- `bot.domain.user_config.UserConfig`
- `bot.domain.drawdown_state.DrawdownState`
- `bot.domain.ports.repositories.UserConfigRepository`, `DrawdownRepository`
- `bot.core.database`
- `asyncpg`
