# ScreenshotAdapter Design

## Overview

Implementar `ScreenshotAdapter` que hereda de `ChartPort` en `bot/infrastructure/telegram/`.

## Arquitectura

- **Ubicación**: `bot/infrastructure/telegram/screenshot_adapter.py`
- **Herencia**: `ChartPort` (abstract base class)
- **Propósito**: Captura de gráficos usando matplotlib con fallback a API externa

## Constructor

```python
def __init__(self, api_key: str | None = None):
```

- Recibe `api_key` opcional
- Si no se provee, usa `SCREENSHOT_API_KEY` desde config

## Métodos

### capture(symbol: str, timeframe: str) -> bytes | None

Misma lógica que `ChartCapture.capture()`:
1. Verifica cache primero (TTL 300s)
2. Intenta matplotlib primero
3. Fallback a API externa si matplotlib falla
4. Guarda en cache si tiene datos
5. Retorna `None` si cualquier paso falla (sin propagar excepciones)

### close() -> None

- Cierra `aiohttp.ClientSession`
- Cierra `BinanceDataFetcher`

## Manejo de Errores

- Wrap con try/except en cada operación
- Log warnings pero retorna `None` silenciosamente
- No propaga excepciones

## Archivos

- **Nuevo**: `bot/infrastructure/telegram/screenshot_adapter.py`
- **Sin cambios**: `bot/trading/chart_capture.py`
