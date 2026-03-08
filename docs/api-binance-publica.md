# API Binance.US - Documentación de Integración

> **Fecha**: 2026-03-05
> **Versión**: 1.0
> **Estado**: Pendiente de implementación

---

## Resumen

Este documento describe la integración de la API pública de Binance.US para el proyecto SipSignal Trading Bot. La API proporciona datos de mercado OHLCV (velas) para análisis técnico de BTC/USDT sin requerir autenticación.

---

## Endpoints Públicos (Sin API Key)

### Base URLs

| Entorno | URL |
|---------|-----|
| Datos de mercado (público) | `https://data-api.binance.vision` |
| API REST completa | `https://api.binance.us` |
| WebSocket | `wss://stream.binance.us:9443` |

### Endpoints Utilizados

| Endpoint | Descripción | Parámetros |
|----------|-------------|------------|
| `GET /api/v3/klines` | Velas OHLCV históricas | `symbol`, `interval`, `limit`, `startTime`, `endTime` |
| `GET /api/v3/ticker/24hr` | Estadísticas 24h | `symbol` (opcional) |
| `GET /api/v3/ticker/price` | Precio actual | `symbol` (opcional) |
| `GET /api/v3/exchangeInfo` | Información de pares | - |
| `GET /api/v3/depth` | Order book | `symbol`, `limit` |

---

## Especificación Técnica

### Timeframes Soportados

| Intervalo | Código | Uso en SipSignal |
|-----------|--------|------------------|
| 15 minutos | `15m` | Timeframe principal para señales |
| 1 hora | `1h` | Confirmación de tendencia |
| 4 horas | `4h` | Contexto macro/tendencia dominante |

### Límites de Rate (Público)

- **IP-based**: 1200 request/minuto
- **Weight por endpoint**:
  - `/api/v3/klines`: 2
  - `/api/v3/ticker/24hr`: 1
  - `/api/v3/ticker/price`: 1

### Respuesta Klines (OHLCV)

```json
[
  [
    1499040000000,      // 0: Open time
    "0.01634790",       // 1: Open
    "0.80000000",       // 2: High
    "0.01575800",       // 3: Low
    "0.01577100",       // 4: Close
    "148976.11427815",  // 5: Volume
    1499644799999,      // 6: Close time
    "2434.19055334",    // 7: Quote asset volume
    308,                // 8: Number of trades
    "1756.87402397",    // 9: Taker buy base asset volume
    "28.46694368",      // 10: Taker buy quote asset volume
    "17928899.62484339" // 11: Ignore
  ]
]
```

---

## Documentación Oficial

- **Docs REST API**: https://docs.binance.us/
- **GitHub**: https://github.com/binance-us/binance-us-api-docs

---

## Notas sobre TradingView

> ⚠️ **Importante**: TradingView **no ofrece una API pública de datos** (precios, indicadores) para uso general.

### Alternativas para gráficos:

1. **Lightweight Charts** (Recomendado): Librería open source de TradingView
   - GitHub: https://github.com/tradingview/lightweight-charts
   - Genera gráficos profesionales con datos de Binance
   - Sin costos, renderizado local

2. **Charting Library**: Requiere aprobación de TradingView
   - Docs: https://tradingview.com/charting-library-docs/

3. **Broker API**: Solo para brokers integrados
   - Docs: https://www.tradingview.com/broker-api-docs/

---

## Referencias Adicionales

| Servicio | URL | Uso |
|----------|-----|-----|
| CryptoCompare (fallback) | `min-api.cryptocompare.com` | Datos alternativos |
| Groq API | `api.groq.com` | Análisis con IA |
| Alpha Vantage | `alphavvantage.co` | Datos de respaldo |

---

## Implementación Pendiente

Ver issue en GitHub para detalles de implementación técnica.
