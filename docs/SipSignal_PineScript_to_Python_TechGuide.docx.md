**🐍 PINE SCRIPT → PYTHON**

**Guía Técnica de Traducción · MSATR Strategy → strategy\_engine.py**

*SipSignal v1.1 · Referencia de Implementación · Marzo 2026*

**SECCIÓN A — ANÁLISIS DEL PINE SCRIPT MSATR**

**A.1 Qué aporta este código que no existía antes**

El Pine Script enviado (MSATR Strategy) es el puente perfecto entre la guía TZ y Python. Contiene dos piezas críticas de conocimiento: la implementación matemática completa del Absolute Strength Histogram (ASH), que es un indicador propietario de un trader de TradingView y no existe en ninguna librería estándar de Python, y la lógica exacta de detección de señales que combina Supertrend con ASH. La buena noticia es que el código Pine Script es suficientemente explícito para traducirlo línea por línea a Python puro con Pandas y NumPy.

**A.2 Inventario de componentes del Pine Script**

**● Supertrend:** ta.supertrend(Sup\_M, Sup\_P) → disponible en pandas-ta como ta.supertrend()

**● ASH (Absolute Strength Histogram):** Implementación propia completa con fórmulas RSI/Stochastic/ADX. HAY QUE PORTARLA MANUALMENTE a Python

**● ATR (para SL y TP):** ta.atr(period) → disponible en pandas-ta como ta.atr()

**● Condiciones de Entrada/Salida:** Lógica de condición: SUP\_BUY\_ALL AND ash\_bullish\_signal. Se traduce directamente a condiciones booleanas sobre DataFrames

**● Estado de la operación:** Variables de estado: inTrade, in\_long\_trade, in\_short\_trade, long\_tp\_level, etc. Se implementan como variables de clase en Python

**A.3 Diferencia clave con la guía TZ original**

El Pine Script tuyo introduce una variación importante respecto a la guía TZ que debes conocer:

**● Guía TZ original:** Guía TZ: TP1 = 1.0× ATR (toma parcial del 50%), el sistema cierra definitivamente cuando cambia el Supertrend

**● Tu MSATR Strategy:** Tu Pine Script: TP único = 1.5× ATR (cierre completo de la posición en un solo target). Sin toma parcial.

*Decisión de implementación en SipSignal: se implementarán AMBOS modos y el trader podrá elegir en /config cuál prefiere. Modo TZ (TP parcial 50% + cierre por Supertrend) o Modo MSATR (TP único 1.5× + SL 1.5× ATR). El modo TZ es el activado por defecto según las recomendaciones del suplemento anterior.*

**A.4 Parámetros del Pine Script vs Guía TZ**

|  |  |  |
| --- | --- | --- |
| **Parámetro** | **Guía TZ** | **Tu Pine Script (MSATR)** |
| Supertrend Period | 10 | 14 |
| Supertrend Multiplier | 1.8 | 1.8 |
| ATR Stop-Loss | 14 × 1.5 | 14 × 1.5 |
| ATR Take Profit | 14 × 1.0 (50%) | 14 × 1.5 (100%) |
| ASH Period | 16 (o 14) | 14 |

*Nota: SipSignal permitirá configurar todos estos parámetros vía /config.*

**SECCIÓN B — TRADUCCIÓN: SUPERTREND**

**B.1 Pine Script → Python (Supertrend)**

El Supertrend está disponible nativamente en pandas-ta. NO hay que reimplementarlo. Solo hay que llamarlo con los parámetros correctos y extraer la columna de dirección.

|  |  |
| --- | --- |
| **🌲 Pine Script** | **🐍 Python (pandas-ta / numpy)** |
| Sup\_P = input.int(14, ...) | SUP\_PERIOD = 14 |
| Sup\_M = input.float(1.8, ...) | SUP\_MULTI = 1.8 |
|  |  |
| [supertrend, direction] = ta.supertrend(Sup\_M, Sup\_P) | df.ta.supertrend(length=SUP\_PERIOD, |
|  | multiplier=SUP\_MULTI, |
| SUP\_TREND\_UP = direction < 0 | append=True) |
| SUP\_TREND\_DOWN = direction >= 0 | # Columnas creadas: SUPERTd\_14\_1.8 |
|  | # SUPERTl\_14\_1.8 |
| SUP\_Signal\_Up = SUP\_TREND\_UP and | # SUPERTs\_14\_1.8 |
| not SUP\_TREND\_UP[1] | direction = df['SUPERTd\_14\_1.8'] |
| SUP\_Signal\_Dn = SUP\_TREND\_DOWN and | sup\_up = direction < 0 |
| not SUP\_TREND\_DOWN[1] | sup\_down = direction >= 0 |
|  | # Señal de cambio: |
|  | sup\_cross\_up = sup\_up & ~sup\_up.shift(1).fillna(False) |
|  | sup\_cross\_dn = sup\_down & ~sup\_down.shift(1).fillna(False) |

**B.2 Cómo leer las columnas del Supertrend en pandas-ta**

pandas-ta genera tres columnas al calcular el Supertrend:

**SUPERTd\_{length}\_{multiplier}:** Dirección: -1 = tendencia alcista (equivalente a direction<0 en Pine), 1 = bajista

**SUPERTl\_{length}\_{multiplier}:** Valor de la línea alcista (solo visible cuando hay uptrend)

**SUPERTs\_{length}\_{multiplier}:** Valor de la línea bajista (solo visible cuando hay downtrend)

*ATENCIÓN: En pandas-ta la convención es inversa a Pine Script. En Pine, direction<0 significa alcista. En pandas-ta, SUPERTd = -1 significa alcista. El resultado es el mismo, solo cambia la notación.*

**▸ trading/technical\_analysis.py → función supertrend**

import pandas\_ta as ta

import pandas as pd

def calculate\_supertrend(df: pd.DataFrame,

period: int = 14,

multiplier: float = 1.8) -> pd.DataFrame:

df.ta.supertrend(length=period, multiplier=multiplier, append=True)

col\_d = f'SUPERTd\_{period}\_{multiplier}'

col\_l = f'SUPERTl\_{period}\_{multiplier}'

col\_s = f'SUPERTs\_{period}\_{multiplier}'

df['supertrend\_direction'] = df[col\_d] # -1=alcista, 1=bajista

df['supertrend\_line'] = df[col\_l].combine\_first(df[col\_s])

df['sup\_is\_bullish'] = df['supertrend\_direction'] == -1

df['sup\_cross\_bullish'] = (df['sup\_is\_bullish'] &

~df['sup\_is\_bullish'].shift(1).fillna(False))

df['sup\_cross\_bearish'] = (~df['sup\_is\_bullish'] &

df['sup\_is\_bullish'].shift(1).fillna(False))

return df

**SECCIÓN C — TRADUCCIÓN COMPLETA: ASH (ABSOLUTE STRENGTH HISTOGRAM)**

**C.1 Por qué el ASH no está en ninguna librería estándar**

El Absolute Strength Histogram v2 (jiehonglim en TradingView) es un indicador propietario publicado en Pine Script. No existe en pandas-ta, TA-Lib, ni ninguna librería Python estándar. Sin embargo, el código Pine Script que nos enviaste contiene TODA la implementación matemática, lo que nos permite portarlo exactamente. La implementación en Python es directa porque todas las operaciones son vectorizables con Pandas y NumPy.

**C.2 Arquitectura del ASH: 3 capas de cálculo**

El ASH se calcula en tres capas progresivas. Es importante entender la arquitectura antes del código:

**● Capa 1:** Capa de Fuente: según el modo (RSI/Stochastic/ADX), calcula Bulls\_raw y Bears\_raw

**● Capa 2:** Capa de Suavizado inicial: aplica la media móvil elegida (EMA/SMA/WMA/etc.) sobre Bulls y Bears con periodo L

**● Capa 3:** Capa de Suavizado final: aplica un segundo suavizado más corto (SM) sobre el resultado anterior

**● Capa 4:** Capa de Color: compara SmthBulls vs SmthBears para determinar si la tendencia es alcista o bajista

**C.3 Traducción de la función ma() (media móvil polimórfica)**

Pine Script tiene una función ma() que acepta diferentes tipos. La traducción en Python:

|  |  |
| --- | --- |
| **🌲 Pine Script** | **🐍 Python (pandas-ta / numpy)** |
| ma(type, src, len) => | import pandas\_ta as ta |
| if type == 'EMA' | import numpy as np |
| result := ta.ema(src, len) |  |
| if type == 'SMA' | def \_ma(s: pd.Series, length: int, |
| result := ta.sma(src, len) | ma\_type: str = 'EMA', |
| if type == 'WMA' | alma\_offset=0.85, |
| result := ta.wma(src, len) | alma\_sigma=6) -> pd.Series: |
| if type == 'HMA' | t = ma\_type.upper() |
| result := ta.wma( | if t == 'EMA': |
| 2\*ta.wma(src,len/2) | return s.ewm(span=length, adjust=False).mean() |
| - ta.wma(src,len), | if t == 'SMA': |
| round(sqrt(len))) | return s.rolling(length).mean() |
| if type == 'ALMA' | if t == 'WMA': |
| result := ta.alma(src,len,...) | w = np.arange(1, length+1) |
|  | return s.rolling(length).apply( |
|  | lambda x: np.dot(x,w)/w.sum(), raw=True) |
|  | if t == 'HMA': |
|  | half = \_ma(s, length//2, 'WMA') |
|  | full = \_ma(s, length, 'WMA') |
|  | raw = 2\*half - full |
|  | sqlen= int(round(np.sqrt(length))) |
|  | return \_ma(raw, sqlen, 'WMA') |
|  | if t == 'ALMA': |
|  | return \_alma(s, length, |
|  | alma\_offset, alma\_sigma) |
|  | raise ValueError(f'MA desconocido: {t}') |

**C.4 Implementación completa del ASH en Python**

La siguiente es la traducción completa y fiel del ASH. El resultado de esta función debe coincidir exactamente con el indicador en TradingView si se usan los mismos parámetros. El modo por defecto para SipSignal es RSI con EMA (igual que la guía TZ).

**▸ trading/technical\_analysis.py → función calculate\_ash() — Port completo desde Pine Script**

# trading/technical\_analysis.py

# Absolute Strength Histogram v2 — Port from Pine Script (jiehonglim)

import numpy as np

import pandas as pd

from typing import Literal

MAType = Literal['EMA','SMA','WMA','SMMA','HMA','ALMA']

ASHMode = Literal['RSI','STOCHASTIC','ADX']

def \_ma(s: pd.Series, length: int, ma\_type: MAType = 'EMA',

alma\_offset: float = 0.85, alma\_sigma: int = 6) -> pd.Series:

t = ma\_type.upper()

if t == 'EMA':

return s.ewm(span=length, adjust=False).mean()

if t == 'SMA':

return s.rolling(length).mean()

if t == 'WMA':

w = np.arange(1, length + 1, dtype=float)

return s.rolling(length).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)

if t == 'SMMA':

wma = \_ma(s, length, 'WMA')

sma = \_ma(s, length, 'SMA')

result = sma.copy()

for i in range(length, len(s)):

result.iloc[i] = (result.iloc[i-1]\*(length-1) + s.iloc[i]) / length

return result

if t == 'HMA':

half = \_ma(s, length // 2, 'WMA')

full = \_ma(s, length, 'WMA')

raw = 2 \* half - full

sqlen = int(round(np.sqrt(length)))

return \_ma(raw, sqlen, 'WMA')

if t == 'ALMA':

return \_alma(s, length, alma\_offset, alma\_sigma)

raise ValueError(f'MA type unknown: {ma\_type}')

def \_alma(s: pd.Series, length: int,

offset: float = 0.85, sigma: int = 6) -> pd.Series:

m = offset \* (length - 1)

s2 = sigma \*\* 2

weights = np.array([np.exp(-((i - m)\*\*2) / (2 \* s2))

for i in range(length)], dtype=float)

weights /= weights.sum()

return s.rolling(length).apply(lambda x: np.dot(x, weights), raw=True)

def calculate\_ash(

df: pd.DataFrame,

length: int = 14,

smooth: int = 4,

src\_col: str = 'close',

mode: ASHMode = 'RSI',

ma\_type: MAType = 'EMA',

alma\_offset: float = 0.85,

alma\_sigma: int = 6,

) -> pd.DataFrame:

'''

Calcula el Absolute Strength Histogram v2.

Traducción directa desde Pine Script (jiehonglim / TradingView).

'''

Price = df[src\_col]

Price1 = Price # ma('SMA', Price, 1) = la misma serie

Price2 = Price.shift(1) # ma('SMA', Price[1], 1) = valor anterior

if mode == 'RSI':

diff = Price1 - Price2

Bulls = 0.5 \* (diff.abs() + diff) # max(diff, 0)

Bears = 0.5 \* (diff.abs() - diff) # max(-diff, 0)

elif mode == 'STOCHASTIC':

Bulls = Price1 - Price1.rolling(length).min()

Bears = Price1.rolling(length).max() - Price1

else: # ADX

high\_diff = df['high'] - df['high'].shift(1)

low\_diff = df['low'].shift(1) - df['low']

Bulls = 0.5\*(high\_diff.abs() + high\_diff)

Bears = 0.5\*(low\_diff.abs() + low\_diff)

kw = dict(ma\_type=ma\_type, alma\_offset=alma\_offset, alma\_sigma=alma\_sigma)

AvgBulls = \_ma(Bulls, length, \*\*kw)

AvgBears = \_ma(Bears, length, \*\*kw)

SmthBulls = \_ma(AvgBulls, smooth, \*\*kw)

SmthBears = \_ma(AvgBears, smooth, \*\*kw)

difference = (SmthBulls - SmthBears).abs()

# Replicar lógica de color del Pine Script:

# difference\_color determina la señal alcista/bajista

# GREEN/LIME → SmthBulls domina → señal alcista

# RED/ORANGE → SmthBears domina → señal bajista

# GRAY → equilibrio → sin señal

bulls\_dominant = difference > SmthBears

bears\_dominant = difference > SmthBulls

# En Pine: si diff > SmthBulls → bearish (bears dominan más)

# Si diff > SmthBears → bullish (bulls dominan más)

ash\_bullish = bulls\_dominant & ~bears\_dominant

ash\_bearish = bears\_dominant & ~bulls\_dominant

ash\_neutral = ~ash\_bullish & ~ash\_bearish

# Señal de entrada: transición de gris (neutro) a color

# Pine: ash\_bullish\_signal = ash\_is\_bullish AND ash\_was\_gray

ash\_bullish\_signal = ash\_bullish & ash\_neutral.shift(1).fillna(False)

ash\_bearish\_signal = ash\_bearish & ash\_neutral.shift(1).fillna(False)

df['ash\_smth\_bulls'] = SmthBulls

df['ash\_smth\_bears'] = SmthBears

df['ash\_difference'] = difference

df['ash\_bullish'] = ash\_bullish

df['ash\_bearish'] = ash\_bearish

df['ash\_neutral'] = ash\_neutral

df['ash\_bullish\_signal'] = ash\_bullish\_signal # ← señal de entrada LONG

df['ash\_bearish\_signal'] = ash\_bearish\_signal # ← señal de entrada SHORT

return df

**SECCIÓN D — TRADUCCIÓN: ATR (STOP-LOSS Y TAKE PROFIT)**

**D.1 ATR en Pine Script vs pandas-ta**

|  |  |
| --- | --- |
| **🌲 Pine Script** | **🐍 Python (pandas-ta / numpy)** |
| ATR\_TPP = input.int(14, ...) | ATR\_TP\_PERIOD = 14 |
| ATR\_SLP = input.int(14, ...) | ATR\_SL\_PERIOD = 14 |
| ATR\_TPM = input.float(1.5, ...) | ATR\_TP\_MULT = 1.5 # (1.0 en modo TZ) |
| ATR\_SLM = input.float(1.5, ...) | ATR\_SL\_MULT = 1.5 |
|  |  |
| Profit\_ATR = ta.atr(ATR\_TPP) | df.ta.atr(length=ATR\_TP\_PERIOD, |
| Stop\_ATR = ta.atr(ATR\_SLP) | append=True) # → col ATRr\_14 |
|  |  |
| # En entrada LONG: | # Nota: Pine usa ATR[1] (vela anterior) |
| long\_tp = entry + Profit\_ATR[1] \* ATR\_TPM | # Pandas: .shift(1) equivale a [1] en Pine |
| long\_sl = entry - Stop\_ATR[1] \* ATR\_SLM | atr = df['ATRr\_14'].shift(1) |
|  |  |
| # En entrada SHORT: | # LONG: |
| short\_tp = entry - Profit\_ATR[1] \* ATR\_TPM | long\_tp = entry\_price + atr \* ATR\_TP\_MULT |
| short\_sl = entry + Stop\_ATR[1] \* ATR\_SLM | long\_sl = entry\_price - atr \* ATR\_SL\_MULT |
|  |  |
|  | # SHORT: |
|  | short\_tp = entry\_price - atr \* ATR\_TP\_MULT |
|  | short\_sl = entry\_price + atr \* ATR\_SL\_MULT |

*IMPORTANTE — Uso de ATR[1] en Pine Script: El Pine Script usa Profit\_ATR[1] y Stop\_ATR[1] (el valor de la vela ANTERIOR, no la actual). En Python esto es df['ATRr\_14'].shift(1). Este detalle es crítico para que los niveles coincidan exactamente con TradingView.*

**▸ trading/technical\_analysis.py → función calculate\_atr\_levels()**

def calculate\_atr\_levels(

df: pd.DataFrame,

tp\_period: int = 14,

sl\_period: int = 14,

tp\_mult: float = 1.5, # 1.0 en modo TZ (TP parcial)

sl\_mult: float = 1.5,

) -> pd.DataFrame:

df.ta.atr(length=tp\_period, append=True)

if tp\_period != sl\_period:

df.ta.atr(length=sl\_period, append=True)

atr\_tp = df[f'ATRr\_{tp\_period}'].shift(1) # [1] como en Pine

atr\_sl = df[f'ATRr\_{sl\_period}'].shift(1)

df['atr\_tp'] = atr\_tp

df['atr\_sl'] = atr\_sl

df['long\_tp'] = df['close'] + atr\_tp \* tp\_mult

df['long\_sl'] = df['close'] - atr\_sl \* sl\_mult

df['short\_tp'] = df['close'] - atr\_tp \* tp\_mult

df['short\_sl'] = df['close'] + atr\_sl \* sl\_mult

# Ratio R:R (siempre debe ser >= 1.0 para emitir señal)

df['rr\_ratio'] = (atr\_tp \* tp\_mult) / (atr\_sl \* sl\_mult)

return df

**SECCIÓN E — STRATEGY ENGINE: CONDICIONES DE ENTRADA Y ESTADO**

**E.1 Condiciones de Entrada en Pine Script vs Python**

|  |  |
| --- | --- |
| **🌲 Pine Script** | **🐍 Python (pandas-ta / numpy)** |
| # Condición LONG: | # En strategy\_engine.py: |
| long\_entry = | # Todo se evalúa sobre velas CERRADAS |
| in\_date\_range | # (el bot solo analiza al cierre de vela) |
| and enable\_long |  |
| and SUP\_BUY\_ALL // Sup alcista | long\_signal = ( |
| and ash\_bullish\_signal // ASH activa | df['sup\_is\_bullish'] # Sup alcista |
| and not inTrade | & df['ash\_bullish\_signal'] # ASH activa |
|  | & df['rr\_ratio'] >= 1.0 # R:R mínimo |
| # Solo ejecutar en vela CONFIRMADA: | & ~in\_trade # Sin posición |
| if long\_entry and barstate.isconfirmed | ) |
| strategy.entry('Buy', strategy.long) |  |
|  | short\_signal = ( |
| # Condición SHORT: | ~df['sup\_is\_bullish'] # Sup bajista |
| short\_entry = | & df['ash\_bearish\_signal'] # ASH activa |
| in\_date\_range | & df['rr\_ratio'] >= 1.0 |
| and enable\_short | & ~in\_trade |
| and SUP\_SELL\_ALL | & enable\_short # Config trader |
| and ash\_bearish\_signal | ) |
| and not inTrade |  |
|  | # La última fila del DF = última vela cerrada |
|  | current = df.iloc[-1] |
|  | signal = current['long\_signal'] |

**E.2 Gestión de estado en Pine Script vs Python**

Pine Script usa variables 'var' que persisten entre velas. En Python, el estado de la operación se almacena en PostgreSQL (tabla active\_trades), no en el DataFrame. El DataFrame es stateless — solo calcula indicadores.

|  |  |
| --- | --- |
| **🌲 Pine Script** | **🐍 Python (pandas-ta / numpy)** |
| var bool inTrade = false | # PostgreSQL tabla active\_trades: |
| var bool in\_long\_trade = false | # signal\_id, direction, entry\_price, |
| var float long\_tp\_level = na | # tp1\_level, sl\_level, status, |
| var float long\_sl\_level = na | # taken\_at, tp1\_hit, sl\_hit |
| var float long\_entry\_price = na |  |
|  | # En signal\_builder.py: |
| if long\_entry and barstate.isconfirmed | async def create\_trade\_record( |
| long\_entry\_price := close | db, signal: SignalDTO) -> int: |
| inTrade := true | return await db.execute(''' |
| long\_tp\_level := entry + | INSERT INTO active\_trades |
| Profit\_ATR[1] \* ATR\_TPM | (direction, entry\_price, |
| long\_sl\_level := entry - | tp1\_level, sl\_level, status) |
| Stop\_ATR[1] \* ATR\_SLM | VALUES($1,$2,$3,$4,'EN\_SEGUIMIENTO') |
|  | RETURNING id''', |
| if strategy.position\_size == 0 | signal.direction, |
| inTrade := false | signal.entry\_price, |
|  | signal.tp1\_level, |
|  | signal.sl\_level) |
|  |  |
|  | # price\_monitor.py compara precio WS |
|  | # contra tp1\_level y sl\_level de la BD |

**E.3 El ciclo completo del strategy\_engine.py (pseudocódigo)**

**▸ trading/strategy\_engine.py → run\_cycle() — Función principal del motor**

# trading/strategy\_engine.py

# Ciclo completo de detección de señal

async def run\_cycle(config: UserConfig) -> Signal | None:

# 1. Obtener datos OHLCV de Binance

df = await data\_fetcher.get\_ohlcv(

symbol='BTCUSDT',

interval=config.timeframe, # '1d' o '4h'

limit=200 # 200 velas históricas

)

# 2. Calcular indicadores

df = calculate\_supertrend(df,

period=config.sup\_period, # 14

multiplier=config.sup\_multi) # 1.8

df = calculate\_ash(df,

length=config.ash\_length, # 14

smooth=config.ash\_smooth, # 4

mode=config.ash\_mode, # 'RSI'

ma\_type=config.ash\_ma\_type) # 'EMA'

df = calculate\_atr\_levels(df,

tp\_mult=config.tp\_mult, # 1.5 (MSATR) o 1.0 (TZ)

sl\_mult=config.sl\_mult) # 1.5

# 3. Evaluar señal en la última vela CERRADA

last = df.iloc[-1]

active = await db.get\_active\_trade() # None si no hay operación abierta

if active is not None:

return None # Ya hay operación en seguimiento, no emitir otra

if config.enable\_long and last['sup\_is\_bullish'] and last['ash\_bullish\_signal']:

if last['rr\_ratio'] >= 1.0:

return Signal(

direction='LONG',

entry\_price=last['close'],

tp1\_level=last['long\_tp'],

sl\_level=last['long\_sl'],

rr\_ratio=last['rr\_ratio'],

atr\_value=last['atr\_tp'],

supertrend\_val=last['supertrend\_line'],

timeframe=config.timeframe,

)

if config.enable\_short and not last['sup\_is\_bullish'] and last['ash\_bearish\_signal']:

if last['rr\_ratio'] >= 1.0:

return Signal(

direction='SHORT',

entry\_price=last['close'],

tp1\_level=last['short\_tp'],

sl\_level=last['short\_sl'],

rr\_ratio=last['rr\_ratio'],

atr\_value=last['atr\_tp'],

supertrend\_val=last['supertrend\_line'],

timeframe=config.timeframe,

)

return None # Sin señal en este ciclo

**SECCIÓN F — DEPENDENCIAS, ADVERTENCIAS Y VALIDACIÓN**

**F.1 Dependencias Python necesarias para esta implementación**

**● pandas-ta >= 0.3.14b:** pip install pandas-ta — Supertrend, ATR nativos

**● pandas / numpy:** pip install pandas numpy — Base de datos vectorizados (ya en requirements.txt)

**● ASH (custom):** El ASH y la función \_ma() son código puro Python/NumPy, SIN dependencia externa

**● python-binance:** pip install python-binance — Para descarga de datos OHLCV de Binance

**F.2 Advertencias críticas de implementación**

**ADVERTENCIA 1 — ATR[1] vs ATR (desplazamiento de vela):**

El Pine Script usa Profit\_ATR[1] y Stop\_ATR[1], es decir, el valor del ATR de la vela ANTERIOR a la señal. En Python hay que usar df['ATRr\_14'].shift(1). Si no se hace este desplazamiento los niveles de TP y SL no coincidirán con TradingView.

**ADVERTENCIA 2 — barstate.isconfirmed:**

En Pine Script la condición barstate.isconfirmed garantiza que la señal se evalúa solo en velas cerradas. En Python el bot cumple esto naturalmente porque el scheduler solo se ejecuta a intervalos fijos DESPUÉS del cierre de cada vela. Sin embargo, hay que verificar que los datos de Binance corresponden a velas cerradas y no a la vela abierta actual. Se recomienda excluir siempre df.iloc[-1] si el timestamp de esa vela es el período actual sin cerrar.

**ADVERTENCIA 3 — Columnas generadas por pandas-ta:**

pandas-ta puede generar columnas con nombres que varían según la versión. Los nombres de columna incluyen el periodo y multiplicador (ej: 'SUPERTd\_14\_1.8'). Siempre usar f-strings o buscar las columnas dinámicamente para evitar KeyErrors si se cambian los parámetros de configuración.

**ADVERTENCIA 4 — ASH: la señal de entrada es la TRANSICIÓN, no el estado:**

El Pine Script detecta la señal alcista del ASH cuando pasa de GRIS (neutro) a VERDE (alcista): ash\_bullish\_signal = ash\_is\_bullish AND ash\_was\_gray. Esto significa que si el ASH ya está verde hace varias velas, NO hay señal nueva. La señal solo ocurre en el PRIMER momento del cruce. En Python: ash\_bullish & ash\_neutral.shift(1). Este es el comportamiento correcto.

**F.3 Cómo validar que la implementación Python coincide con TradingView**

Proceso de validación recomendado antes de desplegar en producción:

● Abrir BTC/USDT en el timeframe 4H en TradingView con los indicadores de la estrategia activados

● Tomar nota de las últimas 5 señales detectadas: fecha, tipo (LONG/SHORT), precio de entrada, TP y SL

● Ejecutar el script Python sobre datos históricos de Binance del mismo período

● Comparar que las señales detectadas por Python coincidan en fecha y dirección con las de TradingView

● Verificar que los valores de TP y SL difieran como máximo en ±0.1% (diferencias por slippage/redondeo son normales)

● Crear test unitario que reproduzca esta validación automáticamente: tests/test\_strategy.py

**F.4 Estructura final del módulo technical\_analysis.py**

El archivo trading/technical\_analysis.py contendrá las siguientes funciones en este orden:

● \_alma(s, length, offset, sigma) → Series — Media móvil ALMA auxiliar

● \_ma(s, length, ma\_type, ...) → Series — Media móvil polimórfica

● calculate\_supertrend(df, period, multiplier) — Supertrend con pandas-ta

● calculate\_ash(df, length, smooth, mode, ...) → DataFrame — ASH port completo

● calculate\_atr\_levels(df, tp\_period, sl\_period, tp\_mult, sl\_mult) → DataFrame

● calculate\_all(df, config) → DataFrame — Función orquestadora que llama a todas las anteriores en orden

**F.5 Notas sobre el modo de operación MSATR vs TZ**

El sistema soportará dos modos de operación configurables por el trader:

**Modo TZ (por defecto):** TP parcial al 50% con ATR×1.0, segunda mitad cerrada por Supertrend. Más conservador y captura tendencias largas

**Modo MSATR:** TP único al 100% con ATR×1.5. Más agresivo, cierra todo en el primer target. Útil en mercados laterales

*El price\_monitor.py implementará el modo TZ con la lógica de dos exits: primero detecta cuando el precio toca TP1 (ATR×1.0) y notifica al trader para cerrar el 50%, luego monitorea el Supertrend para el cierre definitivo. En modo MSATR solo hay un exit único al alcanzar TP (ATR×1.5).*

*SipSignal · Guía Técnica Pine Script → Python · v1.1 · Uso interno*