# ChartCapture Design

## Overview
Captura de gráficos TradingView para señales de trading con generación local y fallback a API externa.

## Proveedores

### Primario: Matplotlib (local)
- Librería Python `matplotlib`
- Genera gráficos localmente sin dependencias GUI
- Funciona en servidores sin display (VPS, containers)
- PNG 1200x800px, tema oscuro, candlestick

### Fallback: screenshot-api.org
- API externa como respaldo
- URL: `https://api.screenshot-api.org/api/v1/screenshot`
- Timeout: 15s

## Características del Gráfico

- Candlestick OHLCV
- Colores: verde #26a69a (up), rojo #ef5350 (down)
- Volumen en panel inferior
- Background oscuro #000000

## Mapeo Timeframes

| Input | TradingView |
|-------|-------------|
| 1d    | D           |
| 4h    | 240         |
| 1h    | 60          |
| 15m   | 15          |

## Caché en Memoria

```python
_cache: Dict[str, Dict] = {
    "BTCUSDT_4h": {
        "data": bytes,
        "timestamp": float
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
3. Obtener OHLCV de Binance
4. Generar gráfico con matplotlib
5. Si falla → intentar screenshot-api.org
6. Si todo falla → return None + log WARNING
7. Guardar en caché si exitoso

## Manejo de Errores

- Timeout (15s) → None
- HTTP error → None
- Excepción → None
- Log WARNING con detalles

## Dependencias

- `matplotlib` (local)
- `aiohttp` (para fallback API)
- `pandas` (para DataFrame OHLCV)
