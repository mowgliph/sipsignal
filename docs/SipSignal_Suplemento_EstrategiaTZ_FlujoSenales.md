**⚡ SIPSIGNAL --- ACTUALIZACIÓN ESTRATÉGICA**

**Integración Estrategia TZ · Flujo de Señales Inteligente · Gestión de
Capital Activa**

*Suplemento al PRD v1.0 · Basado en Guía TZ · Versión 1.1 --- Marzo
2026*

**SECCIÓN 7 --- LA ESTRATEGIA TZ: ANÁLISIS Y MAPEO AL SISTEMA**

**7.1 Resumen de la Estrategia TZ**

La estrategia TZ es un sistema de seguimiento de tendencia 100%
objetivo, diseñado para eliminar la subjetividad del análisis técnico
tradicional. Su fortaleza reside en que las reglas son completamente
claras y no dan lugar a interpretación: o se cumplen las condiciones o
no se cumplen. Esto la hace ideal para automatización.

**7.2 Los Tres Indicadores del Sistema TZ**

*INDICADOR 1 --- Supertrend (ATR Period: 10, Source: hl2, Multiplier:
1.8)*

Cumple tres funciones dentro del sistema:

> ● Señalar la dirección de la tendencia dominante (verde = alcista /
> rojo = bajista)
>
> ● Indicar el momento exacto de cerrar una operación cuando cambia de
> dirección
>
> ● Funcionar como Trailing Stop opcional para proteger ganancias
> abiertas

*Regla clave: el Supertrend usualmente avisará primero de un cambio de
tendencia. La señal es definitiva SOLO cuando la vela cierra, nunca
durante la vela abierta.*

*INDICADOR 2 --- Absolute Strength Histogram v2 (Period: 16 o 14,
Smoothing: 4, RSI, EMA)*

Es el gatillo real de entrada. Cumple dos funciones críticas:

> ● Confirmar la tendencia marcada por el Supertrend con fuerza real de
> momentum
>
> ● Filtrar mercados laterales (rangos): si el ASH no muestra fuerza, no
> hay señal válida aunque el Supertrend cambie

*Nota de configuración: period 16 es el estándar. Period 14 genera
entradas más tempranas con ligero incremento de falsas señales. Esta
elección debe ser configurable en el sistema.*

*INDICADOR 3 --- ATR Stop-Loss (Source: close, Period: 14, Multiplier:
1.5)*

Gestión de riesgo objetiva y adaptativa a la volatilidad del mercado:

> ● Stop-Loss inicial: precio de entrada ± (ATR × 1.5). Se coloca en la
> vela de la señal
>
> ● Take Profit parcial (TP1): precio de entrada ± (ATR × 1.0). Se toma
> el 50% de la posición
>
> ● Después de tocar TP1: el SL se mueve a breakeven (precio de
> entrada). Operación asegurada

**7.3 Reglas de Entrada del Sistema TZ**

*SEÑAL LONG (Compra / BUY):*

> ✓ Condición 1: Supertrend en verde (tendencia alcista activa)
>
> ✓ Condición 2: ASH mostrando fuerza alcista (histograma verde /
> positivo)
>
> ✓ Ambas condiciones deben cumplirse al CIERRE de la vela, no durante
> la vela abierta
>
> ✓ Entrada: al precio de cierre de la vela que confirma las dos
> condiciones

*SEÑAL SHORT (Venta / SELL):*

> ✓ Condición 1: Supertrend en rojo (tendencia bajista activa)
>
> ✓ Condición 2: ASH mostrando fuerza bajista (histograma rojo /
> negativo)
>
> ✓ Mismas reglas de cierre de vela aplican

**7.4 Reglas de Salida del Sistema TZ**

*Salida por Stop-Loss:*

> ● SL inicial colocado en el nivel ATR(14, 1.5) de la vela de entrada
>
> ● Si el precio toca el SL antes de tocar TP1: operación cerrada con
> pérdida controlada
>
> ● Máximo permitido: 2%-4% del capital por operación (ver sección de
> gestión de capital)

*Salida por Take Profit Parcial (TP1):*

> ● TP1 colocado a 1 ATR de distancia del precio de entrada
>
> ● Al tocar TP1: cerrar el 50% de la posición
>
> ● Mover inmediatamente el SL a breakeven (precio de entrada)
>
> ● La operación queda asegurada: el peor resultado posible ahora es 0
> (breakeven)

*Salida Definitiva (segunda mitad de la posición):*

> ● Escenario A: el precio retrocede y toca el SL en breakeven.
> Operación cerrada a 0. La mitad inicial de ganancia se conserva
>
> ● Escenario B: el precio continúa a favor. Mantener posición usando el
> Supertrend como guía
>
> ● Cierre definitivo: cuando el Supertrend cambia de dirección (señal
> contraria)

*Trailing Stop (opcional):*

> ● Solo activar si: TP1 ya fue tocado Y el Supertrend ofrece un nivel
> más conveniente que breakeven
>
> ● Ubicar en el antepenúltimo valor único del Supertrend (valores
> planos cuentan como uno solo)
>
> ● Si el trailing stop saca la posición antes de tiempo: buscar
> reentrada usando el ASH

**7.5 Temporalidades Recomendadas por TZ**

El autor recomienda un enfoque escalonado según experiencia:

**Nivel inicial:** Gráfica Diaria (1D) --- menos operaciones, menos
errores, mayor relevancia de señales

**Nivel intermedio:** 12H, 8H, 6H --- cuando ya hay experiencia con el
sistema

**Nivel avanzado:** 4H --- la temporalidad más popular para este sistema

**No recomendado:** Por debajo de 4H --- requiere configuración
diferente

*Para SipSignal v1.0 se implementará en gráfica Diaria y 4H como
timeframes principales, con 1H como filtro de confluencia secundario.*

**7.6 Datos Clave del Backtest TZ (BTC, desde 2017)**

Resultados con longs + shorts (2% riesgo por operación):

> ● Retorno: +254.6% · Acierto: 62.28% · Profit Factor: 1.59 · Drawdown:
> 15.07%

*Resultados solo longs (estrategia recomendada para BTC):*

> ● Retorno: +234% · Acierto: 68.03% · Profit Factor: 2.087

*El backtest demuestra que operar solo en largo en BTC casi duplica el
profit factor y mejora el winrate en 13 puntos. Esto confirma la
decisión de SipSignal de implementar la estrategia con sesgo alcista en
BTC como configuración por defecto.*

*Script de backtest automatizado disponible en TradingView: TradingZone
STASH (https://www.tradingview.com/script/UQdmc9sj-TradingZone-STASH/).
Este script implementa exactamente la lógica que codificaremos en
strategy_engine.py.*

**SECCIÓN 8 --- GESTIÓN DE CAPITAL Y CONFIGURACIÓN INICIAL DEL TRADER**

**8.1 Onboarding: Lo que el Bot Pregunta Antes de Empezar**

La primera vez que el trader usa el bot, antes de enviar cualquier
señal, el sistema debe recopilar los parámetros de gestión de capital
necesarios para operar correctamente. Sin esta información el bot no
puede calcular el tamaño de posición ni el drawdown máximo. Este proceso
de configuración inicial se guarda en la base de datos PostgreSQL y
puede actualizarse en cualquier momento con el comando /config.

**8.2 Preguntas del Onboarding (en secuencia)**

> **PASO 1 --- CAPITAL TOTAL DE TRADING**
>
> El bot pregunta: \'¿Cuál es tu capital total destinado a trading en
> este momento? Ingresa el monto en USDT.\' El trader responde con un
> número. Este valor se almacena como capital_total en la tabla de
> configuración del usuario.
>
> **PASO 2 --- PORCENTAJE DE RIESGO POR OPERACIÓN**
>
> El bot pregunta: \'¿Qué porcentaje de tu capital quieres arriesgar por
> operación? TZ recomienda entre 2% y 4%. Ingresa un número del 1 al
> 5.\' Por defecto: 2%. Este valor define el monto máximo a perder por
> trade y determina el tamaño de posición.
>
> **PASO 3 --- LÍMITE DE DRAWDOWN MÁXIMO**
>
> El bot informa: \'El sistema tiene configurado un Drawdown Máximo del
> 8% de tu capital. Cuando las pérdidas acumuladas alcancen ese umbral,
> el bot dejará de enviar señales y te notificará para que revises tu
> situación. ¿Confirmas este límite o quieres ajustarlo?\' Rango
> permitido: 5% al 15%.
>
> **PASO 4 --- DIRECCIÓN DE OPERACIONES**
>
> El bot pregunta: \'¿Quieres recibir señales en ambas direcciones (LONG
> y SHORT) o solo señales de compra (LONG)? Según el backtest histórico
> de BTC, operar solo en largo ha mostrado resultados superiores.\'
> Opciones: Solo LONG / LONG y SHORT.
>
> **PASO 5 --- TIMEFRAME PRINCIPAL**
>
> El bot pregunta: \'¿En qué temporalidad quieres operar? 1D (Diario ---
> recomendado para principiantes), 4H (avanzado), o ambos con filtro de
> confluencia.\' Esta elección afecta la frecuencia de señales y la
> configuración del scheduler.
>
> **PASO 6 --- CONFIRMACIÓN Y RESUMEN**
>
> El bot muestra un resumen completo de la configuración: capital,
> riesgo por trade (en porcentaje y en USDT), drawdown máximo (en
> porcentaje y en USDT), dirección, y timeframe. Pide confirmación antes
> de activar el sistema.

**8.3 Cálculos Automáticos del Bot**

Con los datos del onboarding, el bot calcula automáticamente para cada
señal:

**Riesgo por trade en USDT:** capital_total × (porcentaje_riesgo / 100)
→ Ej: 1000 × 0.02 = 20 USDT

**Umbral de drawdown en USDT:** capital_total × (drawdown_maximo / 100)
→ Ej: 1000 × 0.08 = 80 USDT

**Tamaño de posición:** riesgo_por_trade / (precio_entrada - stop_loss)
→ unidades de BTC a comprar

**Target TP1 (1× ATR):** precio_entrada + ATR_valor (long) /
precio_entrada - ATR_valor (short)

**Stop-Loss (1.5× ATR):** precio_entrada - (ATR_valor × 1.5) (long) /
precio_entrada + (ATR_valor × 1.5) (short)

**Ratio R:R:** (TP1 - entrada) / (entrada - SL) → siempre debe ser ≥ 1:1
para emitir la señal

**8.4 Sistema de Drawdown y Pausa Automática**

El bot lleva un contador de pérdidas acumuladas en la sesión activa.
Este contador se actualiza cada vez que el trader marca una operación
como perdedora o cuando el bot detecta que el precio tocó el Stop-Loss
de una operación en seguimiento.

> ● Al llegar al 50% del drawdown máximo: el bot envía un aviso de
> advertencia al trader
>
> ● Al llegar al 100% del drawdown máximo (8% por defecto): el bot
> suspende el envío de señales automáticamente
>
> ● El bot envía mensaje explicando el motivo de la pausa y los pasos
> para reactivarlo
>
> ● El trader puede reactivar manualmente con /resume después de revisar
> su situación
>
> ● El contador de drawdown se puede reiniciar con /resetdd (requiere
> confirmación explícita)

**SECCIÓN 9 --- FLUJO INTELIGENTE DE SEÑALES CON SEGUIMIENTO ACTIVO**

**9.1 Visión del Flujo**

Este es el corazón de la experiencia del trader con SipSignal. El
objetivo es que el bot no sea un simple emisor de señales sino un
asistente activo que acompaña cada operación desde la detección de la
señal hasta el cierre final, registrando el resultado automáticamente en
el journal. El trader solo necesita responder con un botón en Telegram,
el sistema hace el resto.

**9.2 Fase 1 --- Emisión de la Señal**

El motor de estrategia detecta la confluencia de Supertrend + ASH al
cierre de una vela.

El bot envía el siguiente mensaje estructurado al chat del trader:

*Estructura del mensaje de señal:*

> ● Encabezado: tipo de señal con emoji (🟢 SEÑAL LONG BTC o 🔴 SEÑAL
> SHORT BTC)
>
> ● Timeframe: en qué temporalidad se detectó (1D / 4H)
>
> ● Precio de entrada sugerido: precio de cierre de la vela confirmada
>
> ● Stop-Loss calculado: ATR × 1.5 con el precio exacto en USDT
>
> ● Take Profit 1 (TP1): ATR × 1.0 con el precio exacto en USDT
>
> ● Ratio R:R calculado automáticamente
>
> ● Tamaño de posición sugerido basado en el capital y riesgo
> configurado
>
> ● Monto en riesgo en USDT (ej: \'Arriesgas: 20 USDT = 2% de tu
> capital\')
>
> ● Resumen del contexto de mercado generado por IA (2-3 líneas)
>
> ● Gráfico adjunto del timeframe principal capturado de TradingView
>
> ● Estado de los indicadores: Supertrend ✅, ASH ✅, señal al cierre de
> vela ✅

**9.3 Fase 2 --- Botones de Decisión del Trader**

Inmediatamente debajo del mensaje de señal, el bot adjunta botones
inline de Telegram (InlineKeyboardMarkup). El trader responde con un
toque en el móvil:

*Botones que aparecen bajo la señal:*

> **● ✅ \[TOMÉ LA SEÑAL\]:** La tomé en mi exchange --- activa el modo
> SEGUIMIENTO ACTIVO para esta operación
>
> **● ❌ \[NO LA TOMÉ\]:** No la tomé en esta ocasión --- registra la
> señal como NO TOMADA en el journal y cierra el flujo
>
> **● 📊 \[VER ANÁLISIS\]:** Muestra análisis técnico extendido con
> todos los indicadores y contexto IA

*Si el trader no responde en 30 minutos: el bot envía un recordatorio
único. Si no responde en 1 hora: la señal se registra automáticamente
como \'Sin respuesta\' en el journal.*

**9.4 Fase 3A --- Seguimiento Activo (si el trader tomó la señal)**

Cuando el trader confirma que tomó la señal, el sistema entra en modo
SEGUIMIENTO ACTIVO. Esto crea un registro en la tabla \'active_trades\'
de PostgreSQL con todos los parámetros de la operación. A partir de aquí
el bot monitorea el precio de BTC en tiempo real.

*Notificaciones automáticas en seguimiento activo:*

> **● 📈 NOTIF. TP1 ALCANZADO:** El precio acaba de tocar tu TP1.
> Botones: \[CONFIRMAR TP1 TOMADO\] / \[NO LO TOMÉ AÚN\]. Si confirma:
> el bot calcula el nuevo SL en breakeven y envía la notificación de
> movimiento de SL.
>
> **● 🔔 NOTIF. MOVER SL A BREAKEVEN:** Recuerda: mueve tu Stop-Loss a
> tu precio de entrada (X USDT). Tu operación ya está asegurada. Esta
> notificación se envía solo una vez. Botón: \[SL MOVIDO A BREAKEVEN\].
>
> **● 🛑 NOTIF. STOP-LOSS ALCANZADO:** El precio ha tocado tu Stop-Loss
> (X USDT). Si seguiste la gestión, tu pérdida máxima es de Y USDT (Z%
> de tu capital). Botones: \[SÍ, CERRÉ CON PÉRDIDA\] / \[NO, AÚN ESTOY
> EN LA OPERACIÓN\].
>
> **● 🔄 NOTIF. CIERRE POR SUPERTREND:** El Supertrend acaba de cambiar
> de dirección. Según el sistema TZ debes cerrar la segunda mitad de tu
> posición. Precio de cierre sugerido: X USDT. Botones: \[CERRÉ LA
> OPERACIÓN\] / \[CONTINÚO ABIERTO\].
>
> **● 📌 NOTIF. TRAILING STOP ACTUALIZADO:** Opcional. Si el trader
> activó esta función: \'Tu Trailing Stop está ahora en el antepenúltimo
> nivel del Supertrend: X USDT.\'

**9.5 Fase 3B --- Sin Seguimiento (si el trader no tomó la señal)**

Si el trader responde \'No la tomé\', el bot registra la señal en el
historial como \'Señal emitida --- No tomada\'. El sistema vuelve al
estado IDLE esperando la siguiente señal. No hay más notificaciones para
esa señal específica. En el journal aparecerá con estado: NO_TAKEN, lo
que permite al trader analizar retrospectivamente qué hubiera pasado si
la hubiera tomado.

**9.6 Fase 4 --- Cierre y Registro en Journal**

Cuando una operación en seguimiento activo llega a su conclusión (por
cualquier vía), el bot registra automáticamente el resultado completo en
la base de datos:

*Datos que se registran automáticamente:*

> ● ID de señal, fecha/hora de emisión, fecha/hora de cierre
>
> ● Dirección (LONG/SHORT), timeframe, precio de entrada
>
> ● SL inicial, TP1, Supertrend y ASH al momento de la señal
>
> ● ¿TP1 fue tocado? (sí/no), ¿SL movido a breakeven? (sí/no)
>
> ● Precio de cierre final, resultado: WINNER / LOSER / BREAKEVEN /
> PARCIAL
>
> ● Ganancia o pérdida en USDT y porcentaje del capital
>
> ● Actualización del drawdown acumulado del trader

*Mensaje de cierre que envía el bot:*

> ● Para operación ganadora: \'🏆 Operación cerrada con ganancia.
> Resultado: +X USDT (+Y%). Capital actualizado: Z USDT.\'
>
> ● Para breakeven: \'⚖️ Operación cerrada en breakeven. TP1 capturado.
> Capital sin cambios: Z USDT.\'
>
> ● Para operación perdedora: \'📉 Stop-Loss alcanzado. Pérdida: -X USDT
> (-Y%). Capital actualizado: Z USDT. Drawdown acumulado: W%.\'

**SECCIÓN 10 --- ESTADOS DE UNA OPERACIÓN EN EL SISTEMA**

**10.1 Diagrama de Estados (Descripción Textual)**

Cada operación pasa por los siguientes estados. Este es el flujo
completo de vida de una señal en SipSignal:

**1. EMITIDA**

La señal fue detectada por el motor de estrategia y enviada al trader.
Esperando respuesta. Timeout: 60 minutos.

**2a. TOMADA → EN SEGUIMIENTO ACTIVO**

El trader confirmó que abrió la operación en su exchange. El bot
monitorea TP1, SL y Supertrend en tiempo real.

**2b. NO_TOMADA → CERRADA**

El trader no tomó la señal. Se registra en el journal para análisis
retrospectivo. Fin del flujo.

**2c. SIN_RESPUESTA → CERRADA**

El trader no respondió en 60 minutos. Se registra como sin respuesta.
Fin del flujo.

**3a. TP1_ALCANZADO (desde EN_SEGUIMIENTO)**

El precio tocó el TP1. Bot notifica. Si el trader confirma: pasa a
estado PARCIAL_GANADA + SL_BREAKEVEN.

**3b. SL_ALCANZADO_INICIAL (desde EN_SEGUIMIENTO)**

El precio tocó el SL antes de TP1. Operación cerrada con pérdida
completa. Registro: PERDEDORA.

**4a. PARCIAL_GANADA + SL_BREAKEVEN (desde TP1_ALCANZADO)**

50% de la posición cerrada con ganancia. SL movido a breakeven.
Esperando cierre de la segunda mitad.

**5a. WINNER_COMPLETA (desde PARCIAL_GANADA)**

Supertrend cambió y el trader cerró la segunda mitad con ganancia.
Registro: WINNER con ganancia total.

**5b. BREAKEVEN (desde PARCIAL_GANADA)**

La segunda mitad fue sacada en breakeven. TP1 fue ganado, sin pérdida
neta. Registro: BREAKEVEN_PARCIAL.

**10.2 Tabla de Resultados Posibles**

**WINNER COMPLETA:** TP1 tocado + Supertrend cierra con ganancia en la
2da mitad. Mejor escenario

**WINNER PARCIAL:** TP1 tocado + 2da mitad cerrada en ganancia menor al
TP completo

**BREAKEVEN PARCIAL:** TP1 tocado + 2da mitad cerrada en precio de
entrada (SL movido)

**LOSER:** SL inicial tocado antes de llegar a TP1. Pérdida = riesgo
configurado

**CANCELADA:** El trader cerró manualmente antes de TP1 o SL (/close)

**NO TOMADA:** Señal emitida pero no seguida por el trader

**SIN RESPUESTA:** El trader no respondió dentro del tiempo de timeout

**SECCIÓN 11 --- NUEVOS COMANDOS Y ACTUALIZACIONES AL PRD ORIGINAL**

**11.1 Nuevos Comandos Incorporados**

Los siguientes comandos se añaden al PRD original como resultado de este
suplemento:

**/setup:** Inicia el proceso de configuración inicial (onboarding de
capital). Disponible siempre

**/config:** Actualiza cualquier parámetro de configuración: capital,
riesgo %, drawdown máximo, dirección, timeframe

**/capital:** Muestra el capital actual, drawdown acumulado, operaciones
activas y resumen del rendimiento

**/close:** Cierra manualmente una operación en seguimiento activo y
registra el resultado

**/resume:** Reactiva el sistema después de una pausa por drawdown
máximo

**/resetdd:** Reinicia el contador de drawdown (requiere confirmación +
contraseña de seguridad)

**/active:** Muestra las operaciones actualmente en seguimiento activo
con su estado actual

**/pause:** Pausa temporalmente el envío de señales sin afectar el
seguimiento de operaciones abiertas

**11.2 Actualizaciones a la Tabla de Base de Datos**

La tabla \'signals\' del PRD original se amplía con los siguientes
campos:

> ● status: EMITIDA / TOMADA / NO_TOMADA / SIN_RESPUESTA /
> EN_SEGUIMIENTO / TP1_ALCANZADO / PARCIAL_GANADA / WINNER / BREAKEVEN /
> LOSER / CANCELADA
>
> ● taken_at: timestamp de cuando el trader confirmó que tomó la señal
>
> ● tp1_hit: boolean --- si el TP1 fue alcanzado
>
> ● tp1_hit_at: timestamp del momento en que el precio tocó TP1
>
> ● sl_moved_to_breakeven: boolean
>
> ● close_price: precio final de cierre de la operación
>
> ● close_at: timestamp de cierre
>
> ● result: WINNER / LOSER / BREAKEVEN / PARTIAL / CANCELLED / NOT_TAKEN
>
> ● pnl_usdt: ganancia o pérdida en USDT
>
> ● pnl_percent: ganancia o pérdida como % del capital en ese momento
>
> ● supertrend_exit: boolean --- si el cierre fue por cambio de
> Supertrend

Nueva tabla \'user_config\':

> ● user_id, capital_total, risk_percent, max_drawdown_percent,
> direction (LONG_ONLY / BOTH), timeframe_primary, timeframe_filter,
> setup_completed, updated_at

Nueva tabla \'drawdown_tracker\':

> ● user_id, current_drawdown_usdt, current_drawdown_percent,
> losses_count, last_reset_at, is_paused

**11.3 Actualización al Mensaje de Señal (Estructura Final)**

El mensaje de señal revisado a la luz de la estrategia TZ incluye todos
estos campos:

> ● 🟢 SEÑAL LONG / 🔴 SEÑAL SHORT --- encabezado prominente con emoji
> de color
>
> ● Par: BTC/USDT \| Timeframe: 4H \| Cierre de vela: confirmado
>
> ● Precio de entrada: \$ XX,XXX.XX
>
> ● Stop-Loss (ATR×1.5): \$ XX,XXX.XX (−X.X% / −\$X USDT)
>
> ● Take Profit 1 (ATR×1.0): \$ XX,XXX.XX (+X.X% / +\$X USDT)
>
> ● Ratio R:R: 1:X.X
>
> ● Tamaño sugerido: X.XXXXX BTC (arriesgas \$XX USDT = X% de tu
> capital)
>
> ● Supertrend: ✅ Alcista \| ASH: ✅ Fuerza alcista \| Vela cerrada: ✅
>
> ● Contexto IA: \[párrafo de 2-3 líneas generado por Groq\]
>
> ● \[Gráfico del timeframe principal adjunto\]
>
> ● Botones: \[✅ TOMÉ LA SEÑAL\] \[❌ NO LA TOMÉ\] \[📊 VER ANÁLISIS\]

**11.4 Modificaciones al Strategy Engine (strategy_engine.py)**

El motor de estrategia se actualiza para implementar exactamente la
lógica TZ:

> ● Condición de señal: Supertrend bullish (close \> supertrend_line)
> AND ASH histograma positivo/alcista
>
> ● Solo evalúa señal al cierre de vela confirmada (no evalúa vela
> abierta)
>
> ● Calcula SL dinámico: precio_entrada − (ATR_14_1.5) para long,
> precio_entrada + (ATR_14_1.5) para short
>
> ● Calcula TP1 dinámico: precio_entrada + (ATR_14_1.0) para long,
> precio_entrada − (ATR_14_1.0) para short
>
> ● Verifica que el ratio R:R sea al menos 1:1 antes de emitir la señal
>
> ● El Supertrend se calcula con parámetros TZ: ATR Period=10,
> Source=hl2, Multiplier=1.8
>
> ● El ASH se calcula con: Period=16 (configurable a 14), Smoothing=4,
> Source=close, Method=RSI, MA=EMA
>
> ● Cooldown configurable entre señales (por defecto: no emitir señal en
> la misma dirección dentro de 24H en 1D / 4H en 4H)

**11.5 Monitor de Precios en Tiempo Real (price_monitor.py --- módulo
nuevo)**

Este módulo es nuevo y no estaba en el PRD original. Es necesario para
el seguimiento activo. Se ejecuta en paralelo al scheduler de análisis
de señales y su única función es monitorear si el precio de BTC toca los
niveles de TP1, SL o breakeven de las operaciones activas.

> ● Usa WebSocket de Binance para recibir el precio en tiempo real (sin
> polling)
>
> ● Compara el precio actual contra los niveles de cada operación en
> estado EN_SEGUIMIENTO
>
> ● Cuando detecta que un nivel fue tocado: emite la notificación
> correspondiente al trader
>
> ● También monitorea el Supertrend en tiempo real para notificar
> cambios de tendencia
>
> ● Es eficiente: usa una sola conexión WebSocket para todas las
> operaciones activas

**SECCIÓN 12 --- ACTUALIZACIÓN DE LAS FASES DE IMPLEMENTACIÓN**

**12.1 Cambios Respecto al Plan Original**

El plan de 5 fases del PRD original sigue siendo válido. Este suplemento
agrega tareas específicas en las Fases 3 y 4 para implementar el flujo
inteligente de señales, el onboarding de capital y el sistema de
seguimiento activo.

**FASE 3 (ACTUALIZADA) --- MOTOR DE ESTRATEGIA TZ + SEGUIMIENTO ACTIVO**

Se añaden las siguientes tareas a la Fase 3 original:

Tarea 3.5 --- Implementación exacta de indicadores TZ:

> ● Codificar el cálculo del Supertrend con los parámetros exactos de TZ
> (ATR 10, hl2, 1.8)
>
> ● Codificar el ASH con configuración TZ (Period 16/14 configurable,
> Smoothing 4, RSI, EMA)
>
> ● Validar los cálculos comparando contra el script de TradingZone
> STASH en TradingView
>
> ● Implementar la condición de señal exacta: esperar cierre de vela
> antes de evaluar

Tarea 3.6 --- Sistema de onboarding de capital:

> ● Crear flujo conversacional de 6 pasos para capturar configuración de
> capital del trader
>
> ● Almacenar en tabla user_config de PostgreSQL
>
> ● Implementar comando /setup y /config para el onboarding y
> actualizaciones
>
> ● Implementar cálculo automático de tamaño de posición en cada señal

Tarea 3.7 --- Botones inline y seguimiento activo:

> ● Implementar InlineKeyboardMarkup en el mensaje de señal con los tres
> botones
>
> ● Crear el handler de respuesta a botones: registrar decisión en BD
>
> ● Crear tabla active_trades en PostgreSQL para operaciones en
> seguimiento
>
> ● Implementar price_monitor.py con WebSocket de Binance
>
> ● Implementar timeout de 60 minutos para señales sin respuesta

Tarea 3.8 --- Notificaciones del ciclo de vida de la operación:

> ● Implementar notificación de TP1 alcanzado con botones de
> confirmación
>
> ● Implementar notificación de SL alcanzado con registro automático
>
> ● Implementar notificación de mover SL a breakeven
>
> ● Implementar notificación de cierre por Supertrend
>
> ● Implementar notificación de trailing stop actualizado (opcional)

**FASE 4 (ACTUALIZADA) --- BD COMPLETA + DRAWDOWN + JOURNAL
ENRIQUECIDO**

Se añaden las siguientes tareas a la Fase 4 original:

Tarea 4.5 --- Sistema de drawdown y pausa automática:

> ● Crear tabla drawdown_tracker en PostgreSQL
>
> ● Implementar actualización del drawdown en cada cierre de operación
>
> ● Implementar pausa automática al alcanzar el 100% del drawdown máximo
>
> ● Implementar aviso de advertencia al 50% del drawdown
>
> ● Implementar /resume y /resetdd con confirmación de seguridad

Tarea 4.6 --- Journal enriquecido con análisis de rendimiento:

> ● El comando /journal muestra el historial con todos los estados de
> cada operación
>
> ● Estadísticas automáticas: winrate, profit factor, drawdown actual,
> rachas
>
> ● Diferenciación visual: operaciones tomadas vs no tomadas vs sin
> respuesta
>
> ● Análisis IA mensual: Groq evalúa el historial e identifica patrones
> de errores recurrentes

**12.2 Orden de Implementación dentro de Fase 3**

La secuencia correcta para implementar la Fase 3 actualizada es:

> ● Primero: implementar los indicadores TZ y validarlos (Tarea 3.5)
>
> ● Segundo: implementar el onboarding de capital (Tarea 3.6)
>
> ● Tercero: añadir los botones inline al mensaje de señal (Tarea 3.7)
>
> ● Cuarto: implementar price_monitor.py con WebSocket (Tarea 3.7)
>
> ● Quinto: implementar cada notificación del ciclo de vida (Tarea 3.8)

*Este orden garantiza que cada componente funciona antes de construir el
siguiente encima.*

*SipSignal Trading Bot · Suplemento Estratégico v1.1 · Basado en Guía TZ
· Confidencial*
