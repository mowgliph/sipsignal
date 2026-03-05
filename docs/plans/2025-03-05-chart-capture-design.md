# ChartCapture Design

## Overview
Captura de gráficos TradingView para señales de trading con generación local y fallback a API externa.

## Proveedores

### Primario: Lightweight Charts (local)
- Librería Python `lightweight-charts`
- Genera gráficos localmente sin dependencias externas
- PNG 1200x800px, tema oscuro

### Fallback: screenshotapi.net
- API externa como respaldo
- URL: `https://screenshotapi.net/api/v1/screenshot`
- Timeout: 15s

## Mapeo Timeframes

| Input | TradingView | Lightweight |
|-------|-------------|--------------|
| 1d    | D           | D            |
| 4h    | 240         | 240          |
| 1h    | 60          | 60           |
| 15m   | 15          | 15           |

## Caché en Memoria

```python
_cache: Dict[str, Dict] = {
    "BTCUSDT_4h": {
        "data": bytes,
        "timestamp": float  # time.time()
    }
}
```

- TTL: 5 minutos (300 segundos)
- Key: `{symbol}_{timeframe}`

## API

```python
class ChartCapture:
    async def capture(self, symbol: str, timeframe: str) -> bytes | None:
        """Captura gráfico TradingView para el símbolo."""
```

## Flujo

1. Check caché (key: `{symbol}_{timeframe}`)
2. Si cache válido → return bytes
3. Intentar lightweight-charts (local)
4. Si falla → intentar screenshotapi.net
5. Si todo falla → return None + log WARNING
6. Guardar en caché si exitoso

## Manejo de Errores

- Timeout (15s) → None
- HTTP error → None
- Excepción → None
- Log WARNING con detalles

## Dependencias

- `lightweight-charts` (local)
- `aiohttp` (para fallback API)
- `pandas` (para DataFrame OHLCV)
