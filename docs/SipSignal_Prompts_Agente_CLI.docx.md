**⚡ SIPSIGNAL**

**PROMPTS PARA AGENTE CLI**

*Ciclos de Trabajo Consecutivos · Claude Code CLI · GitHub Flow Completo*

|  |
| --- |
| **INSTRUCCIONES DE USO**  Cada prompt es autónomo. Pégalo en Claude Code CLI, espera que complete el ciclo,  verifica el resultado en GitHub y Telegram, luego pasa al siguiente.  El agente usará superpowers:brainstorming → escribe el issue → crea rama →  implementa → corre tests → merge dev → push → cierra issue → borra rama. |

*Versión 1.0 · Marzo 2026 · Repositorio: mowgliph/sipsignal · 26 prompts · 5 Fases*

**CICLO ESTÁNDAR QUE SIGUE CADA PROMPT**

Cada prompt instruye al agente a seguir exactamente estos 8 pasos. El agente no debe saltar ninguno. **Cuanto más específica y pequeña sea la tarea, más eficiente será el resultado.**

| **#** | **Paso** | **Descripción** |
| --- | --- | --- |
| 1 | 🧠 Brainstorm | superpowers:brainstorming analiza el contexto del proyecto, hace preguntas, propone 2-3 enfoques y genera el plan antes de tocar cualquier archivo. |
| 2 | 📋 Issue GitHub | gh issue create con título, cuerpo detallado, labels (feat/bug/chore) y milestone de la fase. Obtiene el número de issue para el commit. |
| 3 | 🌿 Nueva rama | git checkout -b feature/NNN-nombre-corto dev — siempre desde dev, nunca desde main. |
| 4 | ⚙️ Implementa | Escribe el código específico de la tarea, archivo por archivo. TDD cuando aplique: test rojo → código → test verde. |
| 5 | ✅ Tests | python -m pytest tests/ -v o verificación funcional manual. El agente no puede continuar si hay tests fallando. |
| 6 | 🔀 Merge a dev | git checkout dev && git merge --no-ff feature/NNN-nombre — siempre no-fast-forward para conservar historia. |
| 7 | 🚀 Commit + Push | Mensaje convencional: 'feat/fix/chore: descripción (#NNN)'. git push origin dev. |
| 8 | 🗑️ Limpieza | gh issue close NNN && git branch -d feature/NNN-nombre. Rama temporal eliminada. |

**FASE 1 — LIMPIEZA Y ANDAMIAJE BASE**

Prompts 01–05 · Objetivo: repositorio limpio, estructura nueva, bot arrancando con /start y /status

|  |
| --- |
| **PROMPT 01 · ELIMINAR MÓDULOS DE CLIMA DEL REPOSITORIO**  Fase: Fase 1 · Limpieza · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| REPOSITORIO: mowgliph/sipsignal (fork de bbalert, bot Telegram de trading BTC) |
|  |
| TAREA: Eliminar únicamente los archivos y referencias del módulo de clima. |
|  |
| ARCHIVOS A ELIMINAR: |
| - core/weather\_loop\_v2.py |
| - handlers/weather.py |
| - utils/weather\_manager.py |
|  |
| REFERENCIAS A LIMPIAR (grep -r "weather\|openweather" --include="\*.py"): |
| - Imports y registros de handlers en el entry point principal |
| - Variables en core/config.py relacionadas a OPENWEATHER\_API\_KEY |
|  |
| VERIFICACIÓN: python -c "import bbalert" debe correr sin ImportError. |
|  |
| FLUJO GIT: |
| gh issue create --title "chore: eliminar módulo de clima" \ |
| --body "Remover weather\_loop\_v2.py, weather.py, weather\_manager.py \ |
| y referencias a openweather" --label "chore" --milestone "Fase 1" |
| git checkout -b feature/001-remove-weather dev |
| [hacer cambios] |
| python -c "import bbalert" |
| git checkout dev && git merge --no-ff feature/001-remove-weather |
| git commit -m "chore: remove weather module (#NNN)" |
| git push origin dev |
| gh issue close NNN |
| git branch -d feature/001-remove-weather |
|  |

|  |
| --- |
| **PROMPT 02 · ELIMINAR MÓDULOS DE PAGOS TELEGRAM STARS**  Fase: Fase 1 · Limpieza · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| REPOSITORIO: mowgliph/sipsignal |
|  |
| TAREA: Eliminar todo el sistema de pagos con Telegram Stars y tienda (/shop). |
|  |
| BUSCAR Y ELIMINAR (grep -r "stars\|shop\|payment\|invoice" --include="\*.py"): |
| - Archivos handlers/shop.py, handlers/payment.py (si existen) |
| - Cualquier handler de PreCheckoutQuery y SuccessfulPayment |
| - Variables en config.py relacionadas a pagos |
| - Entradas en requirements.txt de librerías de pago |
|  |
| VERIFICACIÓN: python -c "import bbalert" sin errores. |
| grep -r "stars\|shop\|payment" --include="\*.py" → debe dar 0 resultados. |
|  |
| FLUJO GIT: |
| gh issue create --title "chore: eliminar sistema de pagos Telegram Stars" \ |
| --body "Remover handlers de /shop, pagos Stars y PreCheckoutQuery" \ |
| --label "chore" --milestone "Fase 1" |
| git checkout -b feature/002-remove-payments dev |
| [hacer cambios] |
| git checkout dev && git merge --no-ff feature/002-remove-payments |
| git commit -m "chore: remove Telegram Stars payment system (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/002-remove-payments |
|  |

|  |
| --- |
| **PROMPT 03 · ELIMINAR MÓDULOS RSS, RECORDATORIOS Y /TASA CUBA**  Fase: Fase 1 · Limpieza · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| REPOSITORIO: mowgliph/sipsignal |
|  |
| TAREA: Eliminar RSS/Atom, sistema de recordatorios, tasas de cambio Cuba y Babel i18n. |
|  |
| BUSCAR Y ELIMINAR: |
| grep -r "rss\|atom\|feedparser\|recordatorio\|reminder\|tasa\|eltoque\|babel\|gettext" \ |
| --include="\*.py" -l |
|  |
| - Archivos de feeds RSS/Atom |
| - Sistema de recordatorios (/recordatorio, /reminder) |
| - Tasas de cambio Cuba (/tasa, eltoque.com) |
| - Sistema Babel/gettext si solo se usa para idiomas no esenciales |
| - Limpiar requirements.txt: feedparser, Babel |
|  |
| VERIFICACIÓN: python -c "import bbalert" sin errores. |
|  |
| FLUJO GIT: |
| gh issue create --title "chore: eliminar RSS, recordatorios y tasa Cuba" \ |
| --body "Remover feedparser, recordatorios, /tasa Cuba, Babel i18n" \ |
| --label "chore" --milestone "Fase 1" |
| git checkout -b feature/003-remove-rss-reminders dev |
| [hacer cambios] |
| git checkout dev && git merge --no-ff feature/003-remove-rss-reminders |
| git commit -m "chore: remove RSS, reminders and Cuba exchange rate (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/003-remove-rss-reminders |
|  |

|  |
| --- |
| **PROMPT 04 · CREAR ESTRUCTURA DE CARPETAS Y ARCHIVOS VACÍOS**  Fase: Fase 1 · Andamiaje · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| REPOSITORIO: mowgliph/sipsignal |
|  |
| TAREA: Crear los directorios y archivos base con docstrings vacíos para los nuevos módulos. |
| NO escribir código funcional todavía. Solo estructura + docstrings descriptivos. |
|  |
| CREAR EXACTAMENTE: |
| trading/\_\_init\_\_.py |
| trading/data\_fetcher.py → docstring: "Cliente async Binance para OHLCV" |
| trading/technical\_analysis.py → docstring: "Supertrend, ASH, ATR — port desde Pine Script" |
| trading/strategy\_engine.py → docstring: "Motor de detección de señales TZ" |
| trading/signal\_builder.py → docstring: "Constructor de mensajes Telegram con botones" |
| trading/chart\_capture.py → docstring: "Captura de gráficos TradingView" |
| trading/price\_monitor.py → docstring: "Monitor WebSocket de TP/SL en tiempo real" |
| ai/\_\_init\_\_.py |
| ai/groq\_client.py → docstring: "Cliente Groq para análisis de señales" |
| ai/prompts.py → docstring: "Plantillas de prompts para Groq" |
| db/\_\_init\_\_.py |
| db/models.py → docstring: "Esquema PostgreSQL y funciones asyncpg" |
| db/migrations/ → directorio con .gitkeep |
|  |
| VERIFICACIÓN: tree . -I '\_\_pycache\_\_' muestra la estructura completa. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: crear estructura de módulos trading, ai y db" \ |
| --body "Crear directorios y archivos stub para los nuevos módulos" \ |
| --label "feat" --milestone "Fase 1" |
| git checkout -b feature/004-project-structure dev |
| [crear archivos] |
| git checkout dev && git merge --no-ff feature/004-project-structure |
| git commit -m "feat: add module structure for trading, ai and db (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/004-project-structure |
|  |

|  |
| --- |
| **PROMPT 05 · CONFIGURAR .ENV, DOTENV Y BOT\_MAIN.PY MÍNIMO FUNCIONAL**  Fase: Fase 1 · Infraestructura · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| REPOSITORIO: mowgliph/sipsignal |
|  |
| TAREA A — Crear .env.example con todas las variables del sistema: |
| TOKEN\_TELEGRAM="" |
| ADMIN\_CHAT\_IDS="" # IDs separados por coma |
| BINANCE\_API\_KEY="" |
| BINANCE\_API\_SECRET="" |
| GROQ\_API\_KEY="" |
| SCREENSHOT\_API\_KEY="" |
| DATABASE\_URL="postgresql://user:pass@localhost:5432/sipsignal\_db" |
| LOG\_LEVEL="INFO" |
| ENVIRONMENT="production" |
|  |
| TAREA B — Reescribir core/config.py: |
| - Cargar variables con python-dotenv |
| - Clase Settings con todos los valores tipados |
| - Validar TOKEN\_TELEGRAM, ADMIN\_CHAT\_IDS, DATABASE\_URL al iniciar |
| - Lanzar ValueError con mensaje claro si falta alguna obligatoria |
| - admin\_chat\_ids debe ser list[int] |
|  |
| TAREA C — Reescribir bot\_main.py (mínimo funcional): |
| - Responder /start: "✅ SipSignal activo. Sistema de trading BTC iniciando..." |
| - Responder /status: fecha UTC, versión "1.0.0-dev", uptime |
| - Validar que chat\_id sea ADMIN\_CHAT\_IDS en cada handler |
| - Asegurar que .env está en .gitignore |
|  |
| VERIFICACIÓN: python bot\_main.py arranca sin errores (Ctrl+C para parar). |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: .env config, Settings y bot\_main.py mínimo" \ |
| --body "Configurar python-dotenv, validación de variables y entry point mínimo" \ |
| --label "feat" --milestone "Fase 1" |
| git checkout -b feature/005-env-config-botmain dev |
| [implementar] |
| python -c "from core.config import settings; print('OK')" |
| python bot\_main.py & sleep 3 && kill %1 |
| git checkout dev && git merge --no-ff feature/005-env-config-botmain |
| git commit -m "feat: dotenv config, Settings validation and minimal bot\_main (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/005-env-config-botmain |
|  |

**FASE 2 — MOTOR DE DATOS E INDICADORES**

Prompts 06–11 · Objetivo: Binance conectado, Supertrend+ASH+ATR calculando, gráficos funcionando

|  |
| --- |
| **PROMPT 06 · IMPLEMENTAR DATA\_FETCHER.PY — CLIENTE BINANCE OHLCV**  Fase: Fase 2 · Datos · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/data\_fetcher.py (actualmente vacío con docstring) |
|  |
| IMPLEMENTAR clase BinanceDataFetcher: |
|  |
| async get\_ohlcv(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame |
| - Columnas: timestamp(datetime), open, high, low, close, volume (float64) |
| - CRÍTICO: Excluir última vela si está abierta |
| (timestamp\_última + duración\_intervalo > datetime.utcnow()) |
| - Retry exponencial: 3 intentos, espera 2s/4s/8s entre intentos |
| - Log de cada petición con latencia en ms |
|  |
| async get\_current\_price(symbol: str) -> float |
| - Precio ask/bid mid del ticker 24h |
|  |
| INTERVALOS SOPORTADOS: '1d', '4h', '1h', '15m' |
|  |
| DEPENDENCIA: pip install python-binance (añadir a requirements.txt) |
|  |
| VERIFICACIÓN: |
| python -c " |
| import asyncio |
| from trading.data\_fetcher import BinanceDataFetcher |
| df = asyncio.run(BinanceDataFetcher().get\_ohlcv('BTCUSDT','4h', 10)) |
| assert len(df) <= 10 |
| assert 'close' in df.columns |
| assert df['close'].dtype == float |
| print('OK — última vela:', df.index[-1]) |
| " |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: data\_fetcher async con cliente Binance OHLCV" \ |
| --body "Cliente async Binance con exclusión de vela abierta y retry exponencial" \ |
| --label "feat" --milestone "Fase 2" |
| git checkout -b feature/006-data-fetcher dev |
| [implementar] |
| [verificación arriba] |
| git checkout dev && git merge --no-ff feature/006-data-fetcher |
| git commit -m "feat: add async Binance OHLCV data fetcher (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/006-data-fetcher |
|  |

|  |
| --- |
| **PROMPT 07 · IMPLEMENTAR FUNCIONES \_MA() Y CALCULATE\_SUPERTREND()**  Fase: Fase 2 · Indicadores · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/technical\_analysis.py |
|  |
| IMPLEMENTAR (en este orden): |
|  |
| 1. def \_alma(s: pd.Series, length, offset=0.85, sigma=6) -> pd.Series |
| Arnaud Legoux Moving Average — fórmula gaussiana. |
|  |
| 2. def \_ma(s: pd.Series, length: int, ma\_type='EMA', \*\*kw) -> pd.Series |
| Polimórfica: EMA, SMA, WMA, SMMA, HMA, ALMA. |
| (Traducción de la función ma() del Pine Script MSATR Strategy del proyecto) |
|  |
| 3. def calculate\_supertrend(df, period=14, multiplier=1.8) -> pd.DataFrame |
| - df.ta.supertrend(length=period, multiplier=multiplier, append=True) |
| - Columna 'sup\_is\_bullish': True cuando SUPERTd == -1 (pandas-ta: -1 = alcista) |
| - Columna 'sup\_cross\_bullish': True SOLO en el 1er bar del cruce alcista |
| → sup\_is\_bullish & ~sup\_is\_bullish.shift(1) |
| - Columna 'sup\_cross\_bearish': inverso del anterior |
| - Columna 'supertrend\_line': valor float de la línea |
|  |
| DEPENDENCIA: pip install pandas-ta (añadir a requirements.txt) |
|  |
| TESTS: Crear tests/test\_supertrend.py con: |
| - test\_sup\_is\_bullish\_is\_bool: verificar tipo boolean |
| - test\_sup\_cross\_only\_on\_first\_bar: el cruce solo True en barra de cambio |
| - test\_no\_crash\_on\_200\_candles: correr sin excepciones sobre datos reales |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: función \_ma() y calculate\_supertrend() en technical\_analysis" \ |
| --body "MA polimórfica y Supertrend con pandas-ta, parámetros TZ exactos" \ |
| --label "feat" --milestone "Fase 2" |
| git checkout -b feature/007-supertrend dev |
| [implementar] |
| python -m pytest tests/test\_supertrend.py -v |
| git checkout dev && git merge --no-ff feature/007-supertrend |
| git commit -m "feat: add \_ma helper and calculate\_supertrend (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/007-supertrend |
|  |

|  |
| --- |
| **PROMPT 08 · IMPLEMENTAR CALCULATE\_ASH() — PORT DEL PINE SCRIPT MSATR**  Fase: Fase 2 · Indicadores · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/technical\_analysis.py (agregar función) |
|  |
| IMPLEMENTAR def calculate\_ash(df, length=14, smooth=4, src\_col='close', |
| mode='RSI', ma\_type='EMA', ...) -> pd.DataFrame |
|  |
| LÓGICA (traducción fiel del Pine Script MSATR Strategy — modo RSI): |
| Price1 = df[src\_col] |
| Price2 = df[src\_col].shift(1) |
| diff = Price1 - Price2 |
| Bulls = 0.5 \* (diff.abs() + diff) # max(diff, 0) |
| Bears = 0.5 \* (diff.abs() - diff) # max(-diff, 0) |
| AvgBulls = \_ma(Bulls, length, ma\_type) |
| AvgBears = \_ma(Bears, length, ma\_type) |
| SmthBulls = \_ma(AvgBulls, smooth, ma\_type) |
| SmthBears = \_ma(AvgBears, smooth, ma\_type) |
| difference = (SmthBulls - SmthBears).abs() |
| ash\_bullish = (difference > SmthBears) & ~(difference > SmthBulls) |
| ash\_bearish = (difference > SmthBulls) & ~(difference > SmthBears) |
| ash\_neutral = ~ash\_bullish & ~ash\_bearish |
|  |
| # CRÍTICO: señal = TRANSICIÓN de neutro a bullish/bearish, no el estado |
| ash\_bullish\_signal = ash\_bullish & ash\_neutral.shift(1).fillna(False) |
| ash\_bearish\_signal = ash\_bearish & ash\_neutral.shift(1).fillna(False) |
|  |
| COLUMNAS QUE AGREGA: ash\_smth\_bulls, ash\_smth\_bears, ash\_difference, |
| ash\_bullish, ash\_bearish, ash\_neutral, ash\_bullish\_signal, ash\_bearish\_signal |
|  |
| TESTS: tests/test\_ash.py: |
| - test\_ash\_signal\_is\_transition: señal True solo en barra de cruce, no en barras siguientes |
| - test\_ash\_neutral\_when\_balanced: neutro cuando bulls≈bears |
| - test\_ash\_no\_crash\_200\_candles: sin excepciones |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: calculate\_ash() port completo desde Pine Script" \ |
| --body "Absolute Strength Histogram v2 en Python puro — traducción de MSATR Strategy" \ |
| --label "feat" --milestone "Fase 2" |
| git checkout -b feature/008-ash-indicator dev |
| [implementar] |
| python -m pytest tests/test\_ash.py -v |
| git checkout dev && git merge --no-ff feature/008-ash-indicator |
| git commit -m "feat: add ASH indicator ported from Pine Script MSATR (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/008-ash-indicator |
|  |

|  |
| --- |
| **PROMPT 09 · IMPLEMENTAR CALCULATE\_ATR\_LEVELS() CON SHIFT CORRECTO**  Fase: Fase 2 · Indicadores · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/technical\_analysis.py (agregar función) |
|  |
| IMPLEMENTAR def calculate\_atr\_levels(df, tp\_period=14, sl\_period=14, |
| tp\_mult=1.5, sl\_mult=1.5) -> pd.DataFrame |
|  |
| REGLA CRÍTICA DEL PINE SCRIPT: Profit\_ATR[1] y Stop\_ATR[1] |
| El Pine Script usa el ATR de la VELA ANTERIOR. |
| En Python: df['ATRr\_14'].shift(1) |
| Sin este shift los niveles no coinciden con TradingView. |
|  |
| IMPLEMENTACIÓN: |
| df.ta.atr(length=tp\_period, append=True) # → col 'ATRr\_{tp\_period}' |
| atr\_tp = df[f'ATRr\_{tp\_period}'].shift(1) # ← shift obligatorio |
| atr\_sl = df[f'ATRr\_{sl\_period}'].shift(1) |
| df['long\_tp'] = df['close'] + atr\_tp \* tp\_mult |
| df['long\_sl'] = df['close'] - atr\_sl \* sl\_mult |
| df['short\_tp'] = df['close'] - atr\_tp \* tp\_mult |
| df['short\_sl'] = df['close'] + atr\_sl \* sl\_mult |
| df['rr\_ratio'] = (atr\_tp \* tp\_mult) / (atr\_sl \* sl\_mult) |
|  |
| TAMBIÉN AGREGAR función calculate\_all(df, config) → pd.DataFrame: |
| Llama en orden: calculate\_supertrend → calculate\_ash → calculate\_atr\_levels |
|  |
| TESTS: tests/test\_atr.py: |
| - test\_rr\_ratio\_equals\_1\_when\_mult\_equal: tp\_mult==sl\_mult → rr\_ratio≈1.0 |
| - test\_long\_tp\_above\_close: long\_tp > close siempre |
| - test\_atr\_uses\_previous\_candle: atr\_tp[i] == ATRr\_14[i-1] |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: calculate\_atr\_levels con shift(1) y calculate\_all()" \ |
| --body "ATR SL/TP con shift de vela anterior como Pine Script + orquestador" \ |
| --label "feat" --milestone "Fase 2" |
| git checkout -b feature/009-atr-levels dev |
| [implementar] |
| python -m pytest tests/test\_atr.py -v |
| git checkout dev && git merge --no-ff feature/009-atr-levels |
| git commit -m "feat: add ATR SL/TP with Pine Script shift and calculate\_all (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/009-atr-levels |
|  |

|  |
| --- |
| **PROMPT 10 · IMPLEMENTAR CHART\_CAPTURE.PY — CAPTURAS TRADINGVIEW**  Fase: Fase 2 · Gráficos · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/chart\_capture.py |
|  |
| IMPLEMENTAR clase ChartCapture: |
|  |
| async capture(symbol: str, timeframe: str) -> bytes | None |
|  |
| PROVEEDOR: screenshotapi.net (SCREENSHOT\_API\_KEY de settings) |
| URL a capturar: https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}&interval={tv\_tf} |
| MAPEO de intervalos: '1d'→'D', '4h'→'240', '1h'→'60', '15m'→'15' |
|  |
| CACHÉ EN MEMORIA (dict simple): |
| - Key: "{symbol}\_{timeframe}" |
| - Si la entrada tiene menos de 5 minutos, devolver imagen cacheada |
| - Si no: hacer petición, guardar en caché con timestamp |
|  |
| FALLBACK: Si falla (timeout 15s, error HTTP): return None |
| La señal se enviará sin imagen. No crashear nunca. |
| Logear el error con nivel WARNING. |
|  |
| VERIFICACIÓN: |
| python -c " |
| import asyncio |
| from trading.chart\_capture import ChartCapture |
| result = asyncio.run(ChartCapture().capture('BTCUSDT','4h')) |
| print('OK' if result is None or len(result) > 1000 else 'FAIL') |
| " |
| (None es aceptable si no hay API key en el entorno de test) |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: chart\_capture con screenshotapi y caché 5min" \ |
| --body "Captura TradingView con caché en memoria y fallback silencioso" \ |
| --label "feat" --milestone "Fase 2" |
| git checkout -b feature/010-chart-capture dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/010-chart-capture |
| git commit -m "feat: add TradingView chart capture with in-memory cache (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/010-chart-capture |
|  |

|  |
| --- |
| **PROMPT 11 · IMPLEMENTAR HANDLERS /SIGNAL Y /CHART EN TELEGRAM**  Fase: Fase 2 · Handlers · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVOS: handlers/signal\_handler.py + handlers/chart\_handler.py |
|  |
| HANDLER A — /signal (handlers/signal\_handler.py): |
| - Calcular indicadores sobre últimos 200 candles BTC/USDT 4H |
| - Evaluar señal en la ÚLTIMA VELA CERRADA (iloc[-1]) |
| - Enviar mensaje con: |
| · Estado Supertrend: "🟢 Alcista" o "🔴 Bajista" |
| · Estado ASH: "🟢 Bullish" / "🔴 Bearish" / "⚪ Neutral" |
| · Si hay señal activa: entrada, TP, SL y ratio R:R |
| · Si no: "Sin señal activa en este momento" |
| - Adjuntar imagen de chart\_capture (si disponible) |
| - Solo responder a ADMIN\_CHAT\_IDS |
|  |
| HANDLER B — /chart [timeframe] (handlers/chart\_handler.py): |
| - Captura y envía el gráfico del timeframe indicado |
| - Timeframes válidos: 1d, 4h, 1h, 15m — default: 4h |
| - Texto: "📊 BTC/USDT {TF} — {timestamp UTC}" |
| - Solo responder a ADMIN\_CHAT\_IDS |
|  |
| REGISTRAR ambos handlers en bot\_main.py. |
|  |
| VERIFICACIÓN MANUAL: Enviar /signal y /chart 4h en Telegram y verificar respuesta. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: handlers /signal y /chart conectados a indicadores" \ |
| --body "Handlers Telegram que muestran estado real de Supertrend+ASH y gráfico" \ |
| --label "feat" --milestone "Fase 2" |
| git checkout -b feature/011-signal-chart-handlers dev |
| [implementar + registrar en bot\_main.py] |
| git checkout dev && git merge --no-ff feature/011-signal-chart-handlers |
| git commit -m "feat: add /signal and /chart Telegram handlers (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/011-signal-chart-handlers |
|  |

**FASE 3 — STRATEGY ENGINE Y SEÑALES AUTOMÁTICAS**

Prompts 12–18 · Objetivo: señales detectadas y enviadas automáticamente al cierre de cada vela

|  |
| --- |
| **PROMPT 12 · IMPLEMENTAR STRATEGY\_ENGINE.PY — SIGNALDTO Y RUN\_CYCLE()**  Fase: Fase 3 · Motor · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/strategy\_engine.py |
|  |
| IMPLEMENTAR: |
|  |
| @dataclass class SignalDTO: |
| direction: str # 'LONG' o 'SHORT' |
| entry\_price: float |
| tp1\_level: float |
| sl\_level: float |
| rr\_ratio: float |
| atr\_value: float |
| supertrend\_line: float |
| timeframe: str |
| detected\_at: datetime |
|  |
| async def run\_cycle(config: UserConfig) -> SignalDTO | None: |
| 1. df = await BinanceDataFetcher().get\_ohlcv('BTCUSDT', config.timeframe, 200) |
| 2. df = calculate\_all(df, config) |
| 3. last = df.iloc[-1] # última vela cerrada |
| 4. active = await db.fetch\_active\_trade() |
| if active: return None # ya hay una operación abierta |
| 5. if config.enable\_long and last['sup\_is\_bullish'] and last['ash\_bullish\_signal']: |
| if last['rr\_ratio'] >= 1.0: return SignalDTO(direction='LONG', ...) |
| 6. if config.enable\_short and not last['sup\_is\_bullish'] and last['ash\_bearish\_signal']: |
| if last['rr\_ratio'] >= 1.0: return SignalDTO(direction='SHORT', ...) |
| 7. return None |
|  |
| TESTS: tests/test\_strategy\_engine.py: |
| - test\_returns\_none\_if\_active\_trade: mock active trade → None |
| - test\_long\_signal\_when\_both\_conditions: mock last con sup\_bullish=True y ash\_bullish\_signal=True |
| - test\_no\_signal\_when\_rr\_below\_1: rr\_ratio=0.8 → None |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: strategy\_engine con SignalDTO y run\_cycle completo" \ |
| --body "Motor central TZ: Supertrend+ASH+ATR, validación R:R, sin señal si trade activo" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/012-strategy-engine dev |
| [implementar] |
| python -m pytest tests/test\_strategy\_engine.py -v |
| git checkout dev && git merge --no-ff feature/012-strategy-engine |
| git commit -m "feat: add strategy\_engine with SignalDTO and run\_cycle (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/012-strategy-engine |
|  |

|  |
| --- |
| **PROMPT 13 · IMPLEMENTAR ESQUEMA POSTGRESQL — DB/MODELS.PY Y MIGRATION**  Fase: Fase 3 · Base de Datos · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVOS: db/models.py + db/migrations/001\_initial.sql + core/database.py |
|  |
| TABLA signals (en 001\_initial.sql): |
| id SERIAL PK, detected\_at TIMESTAMPTZ, direction VARCHAR(5), |
| entry\_price DECIMAL(12,2), tp1\_level DECIMAL(12,2), sl\_level DECIMAL(12,2), |
| rr\_ratio DECIMAL(5,3), atr\_value DECIMAL(12,2), timeframe VARCHAR(5), |
| status VARCHAR(20) DEFAULT 'EMITIDA', |
| taken\_at TIMESTAMPTZ, tp1\_hit BOOLEAN DEFAULT FALSE, tp1\_hit\_at TIMESTAMPTZ, |
| sl\_moved\_to\_breakeven BOOLEAN DEFAULT FALSE, |
| close\_price DECIMAL(12,2), close\_at TIMESTAMPTZ, |
| result VARCHAR(15), pnl\_usdt DECIMAL(10,2), pnl\_percent DECIMAL(6,3), |
| supertrend\_exit BOOLEAN DEFAULT FALSE, ai\_context TEXT |
|  |
| TABLA active\_trades: id SERIAL PK, signal\_id INT FK→signals, |
| direction VARCHAR(5), entry\_price DECIMAL(12,2), |
| tp1\_level DECIMAL(12,2), sl\_level DECIMAL(12,2), |
| status VARCHAR(20), created\_at TIMESTAMPTZ |
|  |
| TABLA user\_config: user\_id BIGINT PK, capital\_total DECIMAL(12,2), |
| risk\_percent DECIMAL(4,2), max\_drawdown\_percent DECIMAL(4,2), |
| direction VARCHAR(10), timeframe\_primary VARCHAR(5), |
| setup\_completed BOOLEAN DEFAULT FALSE, updated\_at TIMESTAMPTZ |
|  |
| TABLA drawdown\_tracker: user\_id BIGINT PK FK→user\_config, |
| current\_drawdown\_usdt DECIMAL(10,2), current\_drawdown\_percent DECIMAL(5,3), |
| losses\_count INT DEFAULT 0, last\_reset\_at TIMESTAMPTZ, |
| is\_paused BOOLEAN DEFAULT FALSE |
|  |
| core/database.py: pool asyncpg, funciones connect(), close(), execute(), fetch(), fetchrow() |
|  |
| VERIFICACIÓN: |
| psql $DATABASE\_URL -f db/migrations/001\_initial.sql |
| psql $DATABASE\_URL -c "\dt" | grep -E "signals|active\_trades|user\_config|drawdown" |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: esquema PostgreSQL completo con 4 tablas y asyncpg" \ |
| --body "Tablas signals, active\_trades, user\_config, drawdown\_tracker + pool asyncpg" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/013-database-schema dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/013-database-schema |
| git commit -m "feat: add complete PostgreSQL schema and asyncpg database pool (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/013-database-schema |
|  |

|  |
| --- |
| **PROMPT 14 · IMPLEMENTAR GROQ AI CLIENT Y PROMPTS DE ANÁLISIS**  Fase: Fase 3 · IA · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVOS: ai/groq\_client.py + ai/prompts.py |
|  |
| ai/groq\_client.py — clase GroqClient: |
| async analyze\_signal(signal: SignalDTO) -> str |
| - Modelo: llama3-70b-8192 |
| - Timeout: 8 segundos |
| - Si falla: return "" (señal se envía sin análisis IA, nunca bloquear) |
| - Log del error con WARNING si falla |
|  |
| ai/prompts.py — función build\_signal\_prompt(signal: SignalDTO) -> str: |
| Construir prompt que pide análisis de contexto de mercado en 2-3 oraciones en español, |
| incluyendo: dirección, precio entrada, estado Supertrend, ATR actual, ratio R:R. |
| Sin saludos, sin explicaciones adicionales. Solo el análisis. |
|  |
| DEPENDENCIA: pip install groq (añadir a requirements.txt) |
|  |
| VERIFICACIÓN: |
| python -c " |
| import asyncio |
| from trading.strategy\_engine import SignalDTO |
| from datetime import datetime |
| from ai.groq\_client import GroqClient |
| signal = SignalDTO('LONG', 95000, 96000, 93500, 1.33, 1500, 94000, '4h', datetime.utcnow()) |
| result = asyncio.run(GroqClient().analyze\_signal(signal)) |
| print('OK — longitud:', len(result), 'chars') |
| " |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: Groq AI client con análisis de señales y fallback" \ |
| --body "Cliente async Groq con prompts en español y fallback silencioso si falla" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/014-groq-ai-client dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/014-groq-ai-client |
| git commit -m "feat: add Groq AI client with signal analysis and silent fallback (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/014-groq-ai-client |
|  |

|  |
| --- |
| **PROMPT 15 · IMPLEMENTAR SIGNAL\_BUILDER.PY — MENSAJE FORMATEADO Y BOTONES**  Fase: Fase 3 · Señales · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/signal\_builder.py |
|  |
| IMPLEMENTAR async build\_signal\_message(signal, config, ai\_context, chart\_bytes) -> tuple[str, InlineKeyboardMarkup] |
|  |
| FORMATO DEL TEXTO (Markdown Telegram): |
| 🟢 \*SEÑAL LONG BTC/USDT\* o 🔴 \*SEÑAL SHORT BTC/USDT\* |
| Timeframe: {tf} | Vela cerrada: ✅ |
|  |
| 💵 \*Entrada:\* ${entry\_price:,.2f} |
| 🛑 \*Stop-Loss (ATR×1.5):\* ${sl\_level:,.2f} ({sl\_pct:.1f}%) |
| 🎯 \*Take Profit 1 (ATR×1.0):\* ${tp1\_level:,.2f} (+{tp\_pct:.1f}%) |
| 📊 \*Ratio R:R:\* 1:{rr\_ratio:.2f} |
|  |
| 💼 \*Posición sugerida:\* {position\_size:.5f} BTC |
| ⚠️ \*Arriesgas:\* ${risk\_usdt:.2f} ({risk\_pct}% del capital) |
|  |
| 🤖 {ai\_context} |
|  |
| InlineKeyboardMarkup (3 botones en 2 filas): |
| Fila 1: [✅ Tomé la señal | ❌ No la tomé] |
| Fila 2: [📊 Ver análisis completo] |
| callback\_data: "taken:{signal\_id}" | "skipped:{signal\_id}" | "detail:{signal\_id}" |
|  |
| CÁLCULO POSICIÓN: risk\_usdt / (entry\_price - sl\_level) |
|  |
| TESTS: tests/test\_signal\_builder.py: |
| - test\_message\_contains\_prices: texto incluye entry\_price y sl\_level |
| - test\_buttons\_count: InlineKeyboard tiene exactamente 3 botones |
| - test\_callback\_data\_format: cada callback tiene el prefijo correcto |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: signal\_builder con Markdown y botones inline" \ |
| --body "Construye mensaje Telegram formateado con cálculo de posición y 3 botones" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/015-signal-builder dev |
| [implementar] |
| python -m pytest tests/test\_signal\_builder.py -v |
| git checkout dev && git merge --no-ff feature/015-signal-builder |
| git commit -m "feat: add signal\_builder with formatted message and inline buttons (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/015-signal-builder |
|  |

|  |
| --- |
| **PROMPT 16 · IMPLEMENTAR SCHEDULER.PY — CICLO AUTÓNOMO DE ANÁLISIS**  Fase: Fase 3 · Automatización · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: scheduler.py (en raíz del proyecto) |
|  |
| IMPLEMENTAR clase SignalScheduler: |
|  |
| async start(bot, config): |
| Loop infinito. En cada iteración: |
| 1. signal = await run\_cycle(config) |
| 2. Si signal: |
| a. chart\_bytes = await ChartCapture().capture('BTCUSDT', config.timeframe) |
| b. ai\_context = await GroqClient().analyze\_signal(signal) |
| c. text, keyboard = await build\_signal\_message(signal, config, ai\_context, chart\_bytes) |
| d. await bot.send\_photo(ADMIN\_CHAT\_ID, chart\_bytes, caption=text, reply\_markup=keyboard) |
| O send\_message si chart\_bytes es None |
| e. Guardar señal en DB signals (status='EMITIDA') |
| f. Arrancar timeout de 60 min para respuesta del trader |
| 3. Si no signal: nada |
| 4. Si falla cualquier paso: log ERROR, continuar al siguiente ciclo (NO crashear) |
| 5. await asyncio.sleep(CYCLE\_INTERVAL) |
| CYCLE\_INTERVAL: 900s (15min) para 4h, 3600s (60min) para 1d |
|  |
| async stop(): cancela el loop limpiamente |
|  |
| INTEGRAR en bot\_main.py: arrancar scheduler junto con el bot usando |
| application.run\_polling() con post\_init que lanza scheduler.start() |
|  |
| VERIFICACIÓN: Arrancar el bot, ver en logs que el scheduler corre ciclos cada N segundos. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: scheduler autónomo con ciclos de análisis de señales" \ |
| --body "Loop async que ejecuta run\_cycle y envía señales automáticamente" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/016-signal-scheduler dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/016-signal-scheduler |
| git commit -m "feat: add autonomous signal scheduler integrated in bot\_main (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/016-signal-scheduler |
|  |

|  |
| --- |
| **PROMPT 17 · IMPLEMENTAR ONBOARDING /SETUP — CONFIGURACIÓN DE CAPITAL**  Fase: Fase 3 · Capital · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: handlers/setup\_handler.py |
|  |
| IMPLEMENTAR ConversationHandler con 5 estados (STEP\_1 a STEP\_5): |
|  |
| /setup → STEP\_1: "¿Cuál es tu capital total en USDT? (solo el número)" |
| STEP\_1 → STEP\_2: "¿Qué % del capital quieres arriesgar por operación? [1-5] (default: 2)" |
| STEP\_2 → STEP\_3: "Drawdown máximo configurado: 8%. ¿Ajustar? [5-15]" |
| STEP\_3 → STEP\_4: Botones: [Solo LONG ✅ recomendado] [LONG y SHORT] |
| STEP\_4 → STEP\_5: Botones: [📅 Diario 1D] [⏱️ 4 Horas 4H] |
| STEP\_5 → CONFIRM: Mostrar resumen con todos los valores calculados en USDT |
| Botones: [✅ Confirmar y activar] [🔄 Repetir configuración] |
|  |
| Al confirmar: INSERT/UPDATE en tabla user\_config (asyncpg). |
| El scheduler NO debe arrancar hasta que setup\_completed=True. |
| Si ya hay config: mostrar valores actuales + "¿Actualizar?" |
|  |
| REGISTRAR el ConversationHandler en bot\_main.py. |
|  |
| VERIFICACIÓN MANUAL: Enviar /setup y completar los 5 pasos en Telegram. |
| Luego: psql -c "SELECT \* FROM user\_config;" — debe mostrar los valores. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: handler /setup con onboarding de capital en 5 pasos" \ |
| --body "ConversationHandler 5 pasos: capital, riesgo%, drawdown, dirección, timeframe" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/017-setup-handler dev |
| [implementar + registrar en bot\_main.py] |
| git checkout dev && git merge --no-ff feature/017-setup-handler |
| git commit -m "feat: add /setup capital onboarding ConversationHandler (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/017-setup-handler |
|  |

|  |
| --- |
| **PROMPT 18 · IMPLEMENTAR PRICE\_MONITOR.PY — WEBSOCKET PARA TP/SL**  Fase: Fase 3 · Monitor en tiempo real · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/price\_monitor.py |
|  |
| IMPLEMENTAR clase PriceMonitor: |
|  |
| async start(bot): conecta al WebSocket BTC/USDT de Binance (stream: btcusdt@ticker) |
|  |
| En cada tick de precio, para cada trade en active\_trades (status='EN\_SEGUIMIENTO'): |
| LONG: si current\_price >= trade.tp1\_level → notificar TP1 |
| LONG: si current\_price <= trade.sl\_level → notificar SL |
| SHORT: si current\_price <= trade.tp1\_level → notificar TP1 |
| SHORT: si current\_price >= trade.sl\_level → notificar SL |
|  |
| NOTIFICACIÓN TP1: |
| "📈 \*¡TP1 alcanzado!\* BTC llegó a ${tp1\_level:,.2f} |
| Cierra el 50% de tu posición y mueve el SL a ${entry\_price:,.2f} (breakeven)." |
| Botones: [✅ TP1 tomado y SL movido] [⏳ Aún no] |
|  |
| NOTIFICACIÓN SL: |
| "🛑 \*Stop-Loss alcanzado\* en ${sl\_level:,.2f} |
| Pérdida: -${loss\_usdt:.2f} ({loss\_pct:.1f}% del capital)" |
| Botones: [✅ Cerré la posición] [📊 Ver resumen] |
|  |
| Una sola conexión WebSocket para todas las operaciones activas. |
| Reconectar automáticamente si se pierde la conexión (retry con backoff). |
| Integrar en bot\_main.py junto con el scheduler. |
|  |
| VERIFICACIÓN: Arrancar bot, ver en logs que el ticker de precio se recibe cada ~1s. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: price\_monitor WebSocket Binance para TP/SL en tiempo real" \ |
| --body "Monitor WebSocket con notificaciones automáticas de TP1 y SL" \ |
| --label "feat" --milestone "Fase 3" |
| git checkout -b feature/018-price-monitor dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/018-price-monitor |
| git commit -m "feat: add real-time WebSocket price monitor for TP and SL (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/018-price-monitor |
|  |

**FASE 4 — COMANDOS AVANZADOS Y GESTIÓN DE CAPITAL**

Prompts 19–22 · Objetivo: drawdown automático, journal, calculadora R:R y análisis IA avanzado

|  |
| --- |
| **PROMPT 19 · IMPLEMENTAR CALLBACKS DE SEÑAL — DECISIONES DEL TRADER**  Fase: Fase 4 · Seguimiento activo · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: handlers/signal\_response\_handler.py |
|  |
| IMPLEMENTAR CallbackQueryHandler para 3 callbacks: |
|  |
| "taken:{signal\_id}": |
| - UPDATE signals SET status='TOMADA', taken\_at=now() WHERE id={signal\_id} |
| - INSERT INTO active\_trades (signal\_id, direction, entry\_price, tp1\_level, sl\_level, |
| status, created\_at) VALUES (...) |
| - Responder: "✅ Operación registrada. Monitoreando TP1 y Stop-Loss en tiempo real." |
| - Editar mensaje original: eliminar los botones (edit\_message\_reply\_markup) |
|  |
| "skipped:{signal\_id}": |
| - UPDATE signals SET status='NO\_TOMADA' WHERE id={signal\_id} |
| - Responder: "❌ Señal registrada como no tomada. Siguiente ciclo en curso." |
| - Eliminar botones del mensaje original |
|  |
| "detail:{signal\_id}": |
| - Recuperar señal de DB |
| - Enviar análisis completo (todos los indicadores, contexto IA, histórico del par) |
| - Mantener los botones originales activos |
|  |
| TIMEOUT 60 minutos: scheduler o tarea async que actualiza a 'SIN\_RESPUESTA' |
| las señales EMITIDAS con detected\_at < now() - 60min. |
|  |
| REGISTRAR el CallbackQueryHandler en bot\_main.py. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: callback handler para decisiones taken/skipped/detail" \ |
| --body "Procesar respuestas del trader, activar seguimiento activo, timeout 60min" \ |
| --label "feat" --milestone "Fase 4" |
| git checkout -b feature/019-signal-callbacks dev |
| [implementar + registrar] |
| git checkout dev && git merge --no-ff feature/019-signal-callbacks |
| git commit -m "feat: add signal response callback handler with 60min timeout (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/019-signal-callbacks |
|  |

|  |
| --- |
| **PROMPT 20 · IMPLEMENTAR DRAWDOWN\_MANAGER.PY Y COMANDOS /CAPITAL /RESUME /RESETDD**  Fase: Fase 4 · Gestión de Capital · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: trading/drawdown\_manager.py + handlers/capital\_handler.py |
|  |
| drawdown\_manager.py — async update\_drawdown(db, user\_id, pnl\_usdt: float): |
| - UPDATE drawdown\_tracker: current\_drawdown\_usdt += pnl\_usdt (negativo si pérdida) |
| - current\_drawdown\_percent = current\_drawdown\_usdt / capital\_total \* 100 |
| - Si abs(percent) >= max\_drawdown \* 0.5: |
| Enviar aviso: "⚠️ Drawdown al {pct:.1f}%. Revisa tu gestión." |
| - Si abs(percent) >= max\_drawdown: |
| UPDATE drawdown\_tracker SET is\_paused=True |
| Enviar: "🚨 SISTEMA PAUSADO. Drawdown máximo alcanzado ({pct:.1f}%). |
| Las señales están suspendidas. Usa /resume cuando estés listo." |
|  |
| capital\_handler.py — handlers para: |
| /capital → mostrar tabla: capital, drawdown actual ($$ y %), PnL mes, ops activas |
| /resume → si is\_paused: pedir confirmación → is\_paused=False → reactivar scheduler |
| /resetdd → pedir "Escribe CONFIRMAR para resetear" → drawdown a 0 si confirma |
|  |
| TAMBIÉN: Llamar update\_drawdown() desde el callback de SL (cuando trader confirma pérdida). |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: drawdown\_manager con pausa automática y /capital /resume" \ |
| --body "Tracking drawdown, pausa al límite, avisos al 50%, comandos de capital" \ |
| --label "feat" --milestone "Fase 4" |
| git checkout -b feature/020-drawdown-capital dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/020-drawdown-capital |
| git commit -m "feat: add drawdown manager with auto-pause and capital commands (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/020-drawdown-capital |
|  |

|  |
| --- |
| **PROMPT 21 · IMPLEMENTAR HANDLER /JOURNAL CON HISTORIAL Y ESTADÍSTICAS**  Fase: Fase 4 · Journal · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: handlers/journal\_handler.py |
|  |
| /journal [N=10]: |
| SELECT \* FROM signals ORDER BY detected\_at DESC LIMIT N |
| Para cada señal, una línea compacta: |
| {emoji} {fecha} · {direction} · ${entry\_price:,.0f} → {result} |
| Emojis: 🏆 WINNER | 📉 LOSER | ⚖️ BREAKEVEN | ⏭️ NO\_TOMADA | ❓ SIN\_RESPUESTA | ⏳ EN\_CURSO |
|  |
| Al final, bloque de estadísticas: |
| 📊 \*Resumen\* (últimas {N}): |
| Total: {n} | Tomadas: {taken} | Winrate: {wr:.0f}% |
| Profit Factor: {pf:.2f} | PnL total: ${pnl:+.2f} USDT |
| Mejor racha: {best\_streak} wins | Peor racha: {worst\_streak} losses |
|  |
| Botón inline [Ver más →] que carga las siguientes N señales (paginación offset). |
|  |
| /active: |
| SELECT \* FROM active\_trades WHERE status='EN\_SEGUIMIENTO' |
| Para cada trade: dirección, entrada, precio actual (get\_current\_price), distancia al TP y SL. |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: /journal paginado con estadísticas y /active" \ |
| --body "Historial con emojis de resultado, estadísticas, streaks y paginación" \ |
| --label "feat" --milestone "Fase 4" |
| git checkout -b feature/021-journal-active dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/021-journal-active |
| git commit -m "feat: add /journal with paginated history, stats and /active (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/021-journal-active |
|  |

|  |
| --- |
| **PROMPT 22 · IMPLEMENTAR HANDLER /RISK — CALCULADORA R:R INTERACTIVA**  Fase: Fase 4 · Herramientas · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVO: handlers/risk\_handler.py |
|  |
| /risk [entrada] [sl] [tp] |
| Ejemplo: /risk 95000 93500 97500 |
|  |
| CON 3 PARÁMETROS: |
| riesgo = abs(entrada - sl) |
| beneficio = abs(tp - entrada) |
| ratio\_rr = beneficio / riesgo |
| risk\_usdt = (config.capital\_total \* config.risk\_percent / 100) |
| pos\_size = risk\_usdt / riesgo |
| tp\_pct = beneficio / entrada \* 100 |
| sl\_pct = riesgo / entrada \* 100 |
|  |
| Respuesta: |
| 💵 \*Entrada:\* ${entrada:,.2f} | 🛑 \*SL:\* ${sl:,.2f} | 🎯 \*TP:\* ${tp:,.2f} |
| 📊 \*Ratio R:R:\* 1:{ratio\_rr:.2f} |
| 💼 \*Posición:\* {pos\_size:.5f} BTC |
| ⚠️ \*Arriesgas:\* ${risk\_usdt:.2f} ({risk\_pct}% del capital) |
| {emoji\_recom} {recomendacion} |
| Emojis: ✅ "Señal recomendable" si R:R≥1.5 | ⚠️ "Marginal" si 1.0≤R:R<1.5 | ❌ si <1.0 |
|  |
| SIN PARÁMETROS: Enviar mensaje de ayuda con ejemplo de uso. |
|  |
| TAMBIÉN añadir a /config: |
| Comando /config que permite actualizar cualquier parámetro de user\_config: |
| capital, riesgo%, drawdown máximo, dirección, timeframe. |
| Mostrar valores actuales y preguntar cuál quiere cambiar (botones). |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: /risk calculadora R:R y /config de parámetros" \ |
| --body "Calculadora manual con evaluación de señal y actualización de configuración" \ |
| --label "feat" --milestone "Fase 4" |
| git checkout -b feature/022-risk-config dev |
| [implementar] |
| git checkout dev && git merge --no-ff feature/022-risk-config |
| git commit -m "feat: add /risk R:R calculator and /config parameter updater (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/022-risk-config |
|  |

**FASE 5 — TESTS, HARDENING Y PRODUCCIÓN**

Prompts 23–26 · Objetivo: suite de tests completa, seguridad y despliegue 24/7 en VPS

|  |
| --- |
| **PROMPT 23 · SUITE DE TESTS — COMPONENTES CRÍTICOS CON DATOS REALES**  Fase: Fase 5 · Testing · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming y superpowers:test-driven-development para planificar esta tarea. |
|  |
| TAREA: Crear suite completa de tests que valide los componentes críticos antes de producción. |
|  |
| tests/test\_technical\_analysis.py: |
| - test\_supertrend\_bullish\_flag: sup\_is\_bullish True en tendencia alcista conocida |
| - test\_ash\_signal\_is\_transition\_not\_state: ash\_bullish\_signal True SOLO en barra de cruce |
| - test\_atr\_shift\_uses\_previous\_candle: long\_sl usa ATR[i-1] no ATR[i] |
| - test\_rr\_ratio\_equals\_1\_when\_mult\_equal: mult\_tp==mult\_sl → rr\_ratio≈1.0 |
| - test\_calculate\_all\_no\_crash\_200\_candles: no excepciones con datos reales Binance |
|  |
| tests/test\_strategy\_engine.py: |
| - test\_no\_signal\_when\_active\_trade: mock active trade → return None |
| - test\_long\_signal\_with\_conditions\_met: mock last row con señal válida |
| - test\_no\_signal\_below\_rr\_threshold: rr\_ratio=0.8 → None |
| - test\_no\_signal\_when\_only\_one\_condition: Sup bullish pero ASH neutral → None |
|  |
| tests/test\_signal\_builder.py: |
| - test\_message\_has\_required\_fields: texto incluye entrada, TP, SL, ratio |
| - test\_three\_buttons\_present: InlineKeyboard tiene 3 botones |
| - test\_callback\_data\_has\_signal\_id: cada callback incluye el signal\_id |
|  |
| TODOS los tests deben pasar: python -m pytest tests/ -v --tb=short |
| Coverage mínimo objetivo: 70%: python -m pytest --cov=trading --cov=ai tests/ |
|  |
| FLUJO GIT: |
| gh issue create --title "test: suite completa para componentes críticos de trading" \ |
| --body "Tests unitarios para indicadores, strategy\_engine y signal\_builder con datos reales" \ |
| --label "test" --milestone "Fase 5" |
| git checkout -b feature/023-test-suite dev |
| [implementar hasta que todos en verde] |
| python -m pytest tests/ -v && python -m pytest --cov=trading tests/ |
| git checkout dev && git merge --no-ff feature/023-test-suite |
| git commit -m "test: add comprehensive test suite for critical components (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/023-test-suite |
|  |

|  |
| --- |
| **PROMPT 24 · HARDENING DE SEGURIDAD — VALIDACIONES Y ROBUSTEZ**  Fase: Fase 5 · Seguridad · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| TAREA: Auditar y fortalecer el sistema antes del despliegue en producción. |
|  |
| SEGURIDAD: |
| 1. grep -r "password\|secret\|token\|api\_key" --include="\*.py" \ |
| Verificar que NINGUNA credencial está hardcodeada. Si hay: moverla a .env. |
| 2. Verificar que .env está en .gitignore y NO fue commiteado: |
| git log --all -- .env (debe estar vacío) |
| 3. Verificar que TODOS los handlers comprueban: |
| if update.effective\_chat.id not in settings.admin\_chat\_ids: return |
| 4. Rate limiting básico: rechazar si el mismo user\_id envía >1 comando/segundo. |
|  |
| ROBUSTEZ: |
| 5. Cada handler tiene try/except que loguea el error con traceback completo. |
| 6. Si Binance API falla: scheduler loguea y espera el siguiente ciclo. |
| 7. Si PostgreSQL no responde: bot envía "⚠️ BD no disponible" al admin y reintenta. |
| 8. Si Groq falla: señal se envía sin contexto IA (ya implementado en fase 3). |
|  |
| LIMPIEZA DE CÓDIGO: |
| 9. pip install black isort flake8 && black . && isort . && flake8 --select=F401 . |
| 10. Corregir todos los imports no usados que reporte flake8. |
|  |
| VERIFICACIÓN FINAL: python -m pytest tests/ -v → todos en verde después del hardening. |
|  |
| FLUJO GIT: |
| gh issue create --title "security: hardening pre-producción — credenciales y robustez" \ |
| --body "Auditar credenciales, validar admin\_chat\_id, rate limiting, try/except global" \ |
| --label "security" --milestone "Fase 5" |
| git checkout -b feature/024-security-hardening dev |
| [implementar] |
| python -m pytest tests/ -v |
| git checkout dev && git merge --no-ff feature/024-security-hardening |
| git commit -m "security: pre-production hardening and code cleanup (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/024-security-hardening |
|  |

|  |
| --- |
| **PROMPT 25 · CREAR SCRIPT DEPLOY.SH Y README FINAL DE PRODUCCIÓN**  Fase: Fase 5 · Producción · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming para analizar y planificar esta tarea antes de escribir código. |
|  |
| ARCHIVOS: scripts/deploy.sh + README.md actualizado |
|  |
| deploy.sh (chmod +x): |
| #!/bin/bash |
| set -e |
| echo "🚀 Desplegando SipSignal..." |
| git pull origin main |
| source venv/bin/activate |
| pip install -r requirements.txt --quiet |
| python -c "from db.migrations import run\_migrations; run\_migrations()" |
| # Verificar variables obligatorias |
| for var in TOKEN\_TELEGRAM DATABASE\_URL BINANCE\_API\_KEY; do |
| [ -z "${!var}" ] && echo "❌ Falta variable: $var" && exit 1 |
| done |
| sudo systemctl daemon-reload |
| sudo systemctl restart sipsignal |
| sleep 3 |
| sudo systemctl status sipsignal --no-pager |
| echo "✅ SipSignal desplegado correctamente" |
|  |
| README.md — Secciones: |
| # SipSignal — Bot de señales BTC 24/7 |
| ## Descripción (3 líneas) |
| ## Prerequisitos (Python 3.12+, PostgreSQL 15+, Ubuntu 22.04 VPS) |
| ## Instalación paso a paso (clone → venv → .env → migrate → systemd) |
| ## Comandos disponibles (tabla: comando | descripción) |
| ## Configuración inicial (/setup) |
| ## Estrategia TZ (descripción breve) |
|  |
| FLUJO GIT: |
| gh issue create --title "feat: deploy.sh y README de producción completo" \ |
| --body "Script de despliegue para VPS y documentación de instalación" \ |
| --label "feat,docs" --milestone "Fase 5" |
| git checkout -b feature/025-deploy-readme dev |
| [implementar] |
| bash scripts/deploy.sh --dry-run (si implementas modo dry-run) |
| git checkout dev && git merge --no-ff feature/025-deploy-readme |
| git commit -m "feat: add deploy.sh and complete production README (#NNN)" |
| git push origin dev |
| gh issue close NNN && git branch -d feature/025-deploy-readme |
|  |

|  |
| --- |
| **PROMPT 26 · RELEASE V1.0 — MERGE DEV→MAIN, TAG Y GITHUB RELEASE**  Fase: Fase 5 · Release · Ciclo completo: Brainstorm → Issue → Rama → Código → Tests → Merge → Push → Cierre |
| Usa superpowers:brainstorming y superpowers:finishing-a-development-branch para esta tarea. |
|  |
| TAREA: Crear el primer release de producción de SipSignal. |
|  |
| PREREQUISITOS (verificar antes de empezar): |
| git checkout dev |
| python -m pytest tests/ -v → todos en verde |
| python bot\_main.py & sleep 5 && kill %1 → arranca sin errores |
|  |
| FLUJO COMPLETO: |
| # 1. Merge dev → main |
| git checkout main |
| git merge --no-ff dev -m "release: v1.0.0 — SipSignal production ready" |
|  |
| # 2. Tag |
| git tag -a v1.0.0 -m "SipSignal v1.0.0 |
| - Estrategia TZ: Supertrend + ASH + ATR |
| - Señales automáticas cada 15min/60min |
| - Seguimiento activo con WebSocket Binance |
| - Gestión de capital y drawdown automático |
| - /setup /signal /journal /risk /capital /chart" |
|  |
| # 3. Push |
| git push origin main |
| git push origin v1.0.0 |
|  |
| # 4. GitHub Release |
| gh release create v1.0.0 \ |
| --title "SipSignal v1.0.0 — Production Ready" \ |
| --notes "## SipSignal v1.0.0 |
| Bot de señales BTC 24/7 basado en la estrategia TZ. |
| ### Incluye |
| - Indicadores: Supertrend + ASH (port Pine Script) + ATR |
| - Scheduler autónomo de análisis |
| - Seguimiento activo por WebSocket |
| - Onboarding de capital en 5 pasos |
| - Sistema de drawdown con pausa automática |
| - Journal con estadísticas y paginación |
| ### Instalación |
| Ver README.md" |
|  |
| # 5. Desplegar en VPS |
| ssh tu-vps 'cd ~/sipsignal && bash scripts/deploy.sh' |
|  |

**BONUS — SKILLS RECOMENDADAS PARA SIPSIGNAL**

Skills del ecosistema obra/superpowers encontradas en skills.sh. Instalación para Claude Code. Ejecutar una vez antes de empezar la Fase 1.

**Instalación Base Obligatoria**

Todo el sistema de skills se activa instalando superpowers como plugin. Las 14 skills se instalan automáticamente a través del plugin.

|  |
| --- |
| **▸ Instalar obra/superpowers — base de todas las skills** |
| # Claude Code — Instalar superpowers (método marketplace) |
| /plugin marketplace add obra/superpowers |
|  |
| # O método manual (si el marketplace no está disponible): |
| git clone https://github.com/obra/superpowers.git ~/.claude/superpowers |
| # Agregar a ~/.claude/claude.json: |
| { "plugins": ["~/.claude/superpowers"] } |
|  |

**Skills Incluidas en Superpowers — Relevancia para SipSignal**

|  |
| --- |
| **brainstorming (11.3K installs)**  CRÍTICA — Se usa en cada prompt de este documento. Analiza contexto del proyecto, hace preguntas, propone 2-3 enfoques, genera design doc antes de tocar código.  $ npx skills add https://github.com/obra/superpowers --skill brainstorming |

|  |
| --- |
| **systematic-debugging (6.3K installs)**  MUY ÚTIL — Para cuando el Supertrend o el ASH no coincidan con TradingView. Metodología de 4 fases: hipótesis → evidencia → raíz del problema → verificación.  $ npx skills add https://github.com/obra/superpowers --skill systematic-debugging |

|  |
| --- |
| **test-driven-development (5.5K installs)**  CRÍTICA para Fase 5 — RED-GREEN-REFACTOR estricto. Escribe el test fallando primero, luego el mínimo código para que pase. Indispensable para calculate\_ash() y strategy\_engine.  $ npx skills add https://github.com/obra/superpowers --skill test-driven-development |

|  |
| --- |
| **writing-plans (5.5K installs)**  ÚTIL — Convierte el diseño aprobado en plan de tareas de 2-5 minutos cada una, con rutas exactas y pasos de verificación. Se activa automáticamente tras brainstorming.  $ npx skills add https://github.com/obra/superpowers --skill writing-plans |

|  |
| --- |
| **executing-plans (4.9K installs)**  ÚTIL para fases largas — Ejecuta el plan en sesión separada con checkpoints de revisión. Ideal para las Fases 2-3 que tienen muchos archivos interdependientes.  $ npx skills add https://github.com/obra/superpowers --skill executing-plans |

|  |
| --- |
| **verification-before-completion (4.1K installs)**  CRÍTICA — Evita que el agente diga 'está hecho' sin haber corrido los tests. Obliga a ejecutar comandos de verificación antes de cualquier commit o cierre de issue.  $ npx skills add https://github.com/obra/superpowers --skill verification-before-completion |

|  |
| --- |
| **using-git-worktrees (4.0K installs)**  MUY ÚTIL — Crea worktrees aislados para cada feature. Permite trabajar en feature/008-ash-indicator sin afectar feature/007-supertrend al mismo tiempo.  $ npx skills add https://github.com/obra/superpowers --skill using-git-worktrees |

|  |
| --- |
| **finishing-a-development-branch (3.5K installs)**  ÚTIL al finalizar — Guía el cierre de ramas con opciones estructuradas: merge directo, PR, squash. Se usa explícitamente en el Prompt 26 (Release v1.0).  $ npx skills add https://github.com/obra/superpowers --skill finishing-a-development-branch |

|  |
| --- |
| **dispatching-parallel-agents (3.8K installs)**  AVANZADO — Para tareas independientes simultáneas. Útil en Fase 2 para calcular Supertrend y ASH en paralelo sin dependencias de estado compartido.  $ npx skills add https://github.com/obra/superpowers --skill dispatching-parallel-agents |

|  |
| --- |
| **requesting-code-review (4.5K installs)**  RECOMENDADA antes de cada merge a dev — Verifica que la implementación cumple el spec y que el código tiene calidad. Dos etapas: cumplimiento de spec + calidad.  $ npx skills add https://github.com/obra/superpowers --skill requesting-code-review |

**Skills del Plugin Lab (experimentales)**

superpowers-lab contiene skills experimentales. La más útil para SipSignal es tmux para manejar procesos interactivos como el bot de Telegram corriendo en background durante el desarrollo.

|  |
| --- |
| **▸ Instalar obra/superpowers-lab — skills experimentales** |
| # Instalar superpowers-lab (skills experimentales) |
| claude code plugin install https://github.com/obra/superpowers-lab |
|  |
| # O en claude.json: |
| { "plugins": ["https://github.com/obra/superpowers-lab"] } |
|  |
| # Skill incluida relevante para SipSignal: |
| # using-tmux-for-interactive-commands |
| # → Lanzar 'python bot\_main.py' en tmux durante el desarrollo |
| # → El agente puede ver los logs en tiempo real mientras hace cambios |
|  |

**Skill Custom del Proyecto — .claude/skills/fix-issue/**

Crear esta skill en el propio repositorio para que el agente la use automáticamente en cualquier sesión del proyecto sin necesidad de recordárselo en cada prompt.

|  |
| --- |
| **▸ Crear skill personalizada fix-issue en el repositorio** |
| # Crear la skill en el repositorio |
| mkdir -p .claude/skills/fix-issue |
| cat > .claude/skills/fix-issue/SKILL.md << 'EOF' |
| --- |
| name: fix-issue |
| description: Use when implementing any feature, fix or task in sipsignal. |
| Follows the full cycle: brainstorm, create GitHub issue, branch, implement, |
| test, merge dev, push, close issue, delete branch. |
| --- |
|  |
| Fix the task described in $ARGUMENTS following the SipSignal workflow: |
| 1. Use superpowers:brainstorming to analyze and plan before any code |
| 2. gh issue create with title, body, label and milestone |
| 3. git checkout -b feature/NNN-name dev |
| 4. Implement with TDD where applicable |
| 5. python -m pytest tests/ -v — all must pass |
| 6. git checkout dev && git merge --no-ff feature/NNN-name |
| 7. git commit -m 'type: description (#NNN)' && git push origin dev |
| 8. gh issue close NNN && git branch -d feature/NNN-name |
| EOF |
|  |
| # Commitear la skill al repositorio |
| git add .claude/skills/ && git commit -m "chore: add fix-issue project skill" |
|  |

|  |
| --- |
| *SipSignal · Prompts para Agente CLI · v1.0 · Marzo 2026 · 26 prompts · 5 Fases* |
