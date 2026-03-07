# Repositories Ports Design

## Overview
Crear los puertos de salida (interfaces) para los repositorios en el dominio puro del sistema.

## Location
`bot/domain/ports/repositories.py`

## Structure

4 clases abstractas con métodos async:

### SignalRepository
- `save(signal: Signal) -> Signal`
- `get_by_id(signal_id: int) -> Signal | None`
- `get_recent(limit: int) -> list[Signal]`
- `update_status(signal_id: int, status: str) -> None`

### ActiveTradeRepository
- `save(trade: ActiveTrade) -> ActiveTrade`
- `get_active() -> ActiveTrade | None`
- `update(trade: ActiveTrade) -> None`
- `close(trade_id: int, status: str) -> None`

### UserConfigRepository
- `get(user_id: int) -> UserConfig | None`
- `save(config: UserConfig) -> UserConfig`

### DrawdownRepository
- `get(user_id: int) -> DrawdownState | None`
- `save(state: DrawdownState) -> DrawdownState`
- `reset(user_id: int) -> DrawdownState`

## Dependencies
- `abc` (stdlib)
- Domain entities from `bot.domain`
