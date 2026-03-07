**⚡ SIPSIGNAL TRADING BOT**

**Sistema Inteligente de Señales BTC · VPS + Telegram**

PRD · AppFlow · Tech Stack · Plan de Limpieza · Fases de Implementación

*Versión 1.0 --- Marzo 2026*

**SECCIÓN 1 --- PRODUCT REQUIREMENTS DOCUMENT (PRD)**

**1.1 Resumen Ejecutivo**

SipSignal es un sistema automatizado de detección y notificación de
señales de trading para Bitcoin (BTC/USDT), diseñado para ejecutarse en
un VPS propio y comunicarse en tiempo real con el trader a través de un
bot de Telegram. El sistema no ejecuta órdenes automáticamente; su
propósito es actuar como un analista técnico permanente que detecta
oportunidades de entrada y salida según la estrategia definida por el
usuario, y envía una alerta enriquecida con contexto de mercado.

**1.2 Problema que Resuelve**

Los traders activos no pueden monitorear gráficos las 24 horas. Perder
una señal de entrada significativa en BTC implica pérdidas de
oportunidad o entradas en momentos desfavorables. El problema central
tiene tres dimensiones:

> ● Atención limitada: el trader no puede observar el gráfico de forma
> continua.
>
> ● Subjetividad emocional: sin un sistema automático, las decisiones se
> ven afectadas por sesgos.
>
> ● Falta de contexto: una señal de precio sin contexto técnico tiene
> poco valor accionable.

**1.3 Objetivos del Producto**

> ● Detectar señales de entrada y salida de BTC según la estrategia del
> usuario con precisión técnica.
>
> ● Enviar notificaciones instantáneas al bot de Telegram con datos
> ricos: precio, indicadores, gráfico y contexto IA.
>
> ● Proveer análisis técnico automatizado usando múltiples indicadores
> (RSI, MACD, Bollinger Bands, EMA, volumen).
>
> ● Almacenar historial de señales y operaciones en base de datos
> PostgreSQL.
>
> ● Ofrecer comandos de consulta interactivos en el bot para revisar
> estado del mercado bajo demanda.
>
> ● Ejecutar de manera estable y autónoma en un VPS con Linux usando
> systemd.

**1.4 Usuarios Objetivo**

Perfil primario: trader individual con experiencia técnica básica, que
opera BTC en Binance y ya tiene VPS propio.

**Nivel técnico:** Intermedio --- capaz de gestionar un servidor Linux y
claves API

**Mercado:** BTC/USDT exclusivamente en esta primera versión

**Uso esperado:** Recibir alertas de trading y consultar el estado del
mercado desde el móvil vía Telegram

**1.5 Funcionalidades Requeridas (Must Have)**

*Motor de Señales:*

> ● Carga de datos OHLCV desde Binance API en múltiples timeframes (5m,
> 15m, 1h, 4h, 1D).
>
> ● Cálculo de indicadores técnicos: RSI, MACD, Bollinger Bands, EMA
> 20/50/200, ATR, volumen ponderado.
>
> ● Lógica de detección de señal de COMPRA y VENTA configurable por el
> usuario.
>
> ● Filtro de confluencia multi-timeframe para reducir falsas señales.

*Notificaciones Telegram:*

> ● Mensaje estructurado con: dirección (BUY/SELL), precio actual,
> niveles de stop-loss y target sugeridos.
>
> ● Captura automática del gráfico desde TradingView adjunta al mensaje.
>
> ● Análisis contextual generado por IA (Groq/Claude) con resumen
> ejecutivo de la señal.
>
> ● Calculadora de riesgo-beneficio integrada en el mensaje.

*Comandos interactivos del bot:*

> ● /signal --- Solicitar análisis técnico instantáneo de BTC.
>
> ● /chart \[tf\] --- Ver gráfico actual en el timeframe indicado.
>
> ● /risk \[entrada\] \[sl\] \[tp\] --- Calcular ratio riesgo/beneficio
> y tamaño de posición.
>
> ● /journal --- Ver historial de señales recientes.
>
> ● /scenario --- Ver análisis de escenario alcista/neutral/bajista con
> IA.
>
> ● /status --- Estado del sistema y último ciclo de análisis.

*Infraestructura y Persistencia:*

> ● Base de datos PostgreSQL para usuarios, señales emitidas y
> configuración.
>
> ● Configuración por variables de entorno (.env) sin hardcodear
> credenciales.
>
> ● Servicio systemd para auto-reinicio en caso de fallo.
>
> ● Logs estructurados con rotación automática.

**1.6 Funcionalidades Diferenciadores (Nice to Have --- Fases Futuras)**

> ● Revisor de diario de trading con IA: análisis de errores recurrentes
> en operaciones pasadas.
>
> ● Motor de escenarios: modelado alcista, neutral y bajista proyectado
> a 3-6 meses.
>
> ● Panel web de administración ligero.
>
> ● Soporte para otros pares de criptomonedas (ETH, SOL) como expansión
> modular.
>
> ● Integración con Redis para cacheo de datos de mercado.

**1.7 Lo que el Sistema NO Hará (Out of Scope)**

> ✗ No ejecutará órdenes automáticas en Binance (no es un bot de trading
> algorítmico autónomo).
>
> ✗ No gestionará alertas de clima, tasas de cambio ni RSS (código de
> sipsignal a eliminar).
>
> ✗ No soportará multiples usuarios en v1 (solo el trader propietario).
>
> ✗ No tendrá sistema de pagos (Telegram Stars se elimina).
>
> ✗ No dará soporte a acciones, ETFs ni forex en esta versión.

**1.8 Criterios de Éxito**

**Latencia de señal:** Menos de 30 segundos entre detección y recepción
en Telegram

**Disponibilidad:** 99% uptime en VPS con systemd y auto-reinicio

**Precisión técnica:** Indicadores calculados correctamente validados
contra TradingView

**Falsos positivos:** Reducidos al mínimo mediante filtro
multi-timeframe

**Usabilidad:** El trader puede operar el bot únicamente desde el móvil

**1.9 Restricciones y Suposiciones**

> ● El VPS tiene Ubuntu 22.04 o superior con Python 3.12+.
>
> ● El trader tiene cuentas activas en Binance y TradingView (plan
> gratuito o pago).
>
> ● La API de Binance se usa solo para consulta de datos (sin permisos
> de trading en esta versión).
>
> ● Se requiere una API key de Groq (gratuita disponible) para el
> análisis con IA.
>
> ● La estrategia de trading inicial la define el usuario y se
> implementa como módulo configurable.

**SECCIÓN 2 --- FLUJO DE LA APLICACIÓN (APPFLOW)**

**2.1 Visión General del Flujo**

El sistema opera en dos modos simultáneos y complementarios: el modo
autónomo (ciclos de análisis programados que corren en segundo plano) y
el modo interactivo (respuesta a comandos del usuario en Telegram).
Ambos convergen en el Motor de Señales y comparten la misma base de
datos PostgreSQL.

**2.2 Flujo Principal: Detección Autónoma de Señales**

*Paso 1 --- Iniciación del ciclo:*

> ● El scheduler interno (APScheduler o asyncio) activa el ciclo cada N
> minutos configurables.
>
> ● El ciclo inicia el cliente de Binance y solicita datos OHLCV para
> BTC/USDT en múltiples timeframes.

*Paso 2 --- Recolección de datos:*

> ● Binance API devuelve velas (candlesticks) históricas y actuales.
>
> ● Los datos se cargan en estructuras Pandas para procesamiento
> eficiente.
>
> ● Se verifica integridad de datos (sin valores nulos, secuencia
> temporal correcta).

*Paso 3 --- Cálculo de indicadores:*

> ● El módulo de análisis técnico calcula: RSI, MACD, Bollinger Bands,
> EMA 20/50/200, ATR, VWAP, volumen.
>
> ● Se obtiene el contexto macro: tendencia dominante en 4H y 1D.
>
> ● Se identifican soportes y resistencias clave automáticamente.

*Paso 4 --- Motor de estrategia:*

> ● La lógica de estrategia definida evalúa las condiciones actuales de
> los indicadores.
>
> ● Comprueba confluencia: la señal en 15m es confirmada por la
> tendencia en 1H y 4H.
>
> ● Si hay señal válida: se marca como BUY o SELL con nivel de confianza
> (Alta / Media / Baja).
>
> ● Si no hay señal: el ciclo termina silenciosamente y espera el
> siguiente.

*Paso 5 --- Generación del mensaje de alerta:*

> ● Se construye el mensaje estructurado: dirección, precio, stop-loss
> sugerido, target, ratio R:R.
>
> ● Se solicita captura de gráfico a TradingView con el timeframe
> principal.
>
> ● Se envía los datos al módulo de IA (Groq) para generar el resumen de
> contexto en lenguaje natural.

*Paso 6 --- Envío al Telegram:*

> ● El bot envía el mensaje formateado al chat del trader.
>
> ● Se adjunta el gráfico como imagen.
>
> ● La señal se registra en la base de datos PostgreSQL con timestamp,
> precio y contexto.

**2.3 Flujo Interactivo: Comandos del Trader**

El trader puede interactuar con el bot en cualquier momento. Cada
comando activa su propio flujo, siempre validando que la solicitud venga
del chat autorizado.

**/signal:** Activa el análisis técnico completo de forma manual y
devuelve señal o estado de mercado

**/chart \[1h\]:** Captura el gráfico en el timeframe indicado y lo
envía como imagen

**/risk \[x\] \[y\] \[z\]:** Calcula ratio R:R y tamaño de posición
recomendado para las variables dadas

**/journal:** Recupera de PostgreSQL las últimas 10 señales emitidas con
su resultado

**/scenario:** Envía análisis de IA con escenario alcista, neutral y
bajista para BTC

**/status:** Muestra si el sistema está activo, el último ciclo
ejecutado y la conexión con Binance

**2.4 Diagrama de Componentes (Descripción Textual)**

*Capa de Datos (Fuentes Externas):*

> ● Binance API → datos de precio OHLCV y volumen en tiempo real
>
> ● TradingView Screenshot API → capturas de gráficos con indicadores
> visuales
>
> ● Groq API → motor de lenguaje natural para análisis contextual con IA

*Capa de Procesamiento (VPS):*

> ● data_fetcher.py → cliente Binance, descarga y valida datos OHLCV
>
> ● technical_analysis.py → cálculo de todos los indicadores técnicos
>
> ● strategy_engine.py → lógica de señal, filtro de confluencia, nivel
> de confianza
>
> ● signal_builder.py → construcción del mensaje, cálculo de R:R,
> generación de contexto IA
>
> ● chart_capture.py → captura y gestión de gráficos desde TradingView
>
> ● scheduler.py → coordinación del ciclo de análisis autónomo

*Capa de Persistencia:*

> ● PostgreSQL → tabla signals, tabla users, tabla config
>
> ● Logs → archivos rotativos en /var/log/sipsignal/

*Capa de Interfaz (Telegram):*

> ● bot_main.py → punto de entrada, inicialización del bot y registro de
> handlers
>
> ● handlers/ → módulo separado por cada comando (/signal, /chart,
> /risk, etc.)
>
> ● notifier.py → envío de mensajes, imágenes y formateo Markdown

**2.5 Estados del Sistema**

**IDLE:** Sin señal detectada. El ciclo corre normalmente cada N minutos

**SIGNAL_DETECTED:** Señal encontrada. Se construye y envía el mensaje

**WAITING_CONFIRMATION:** Señal en timeframe menor. Esperando
confirmación en timeframe mayor

**ERROR:** Fallo de conexión o error de API. Se loguea y se reintenta en
el siguiente ciclo

**MAINTENANCE:** Modo silencioso activado por el trader vía comando
/pause

**SECCIÓN 3 --- STACK TECNOLÓGICO**

**3.1 Lenguaje y Runtime**

**Python 3.12+:** Lenguaje principal. Uso de async/await nativo para I/O
concurrente

**AsyncIO:** Event loop para manejo eficiente de Telegram, Binance y
tareas programadas

**3.2 APIs Externas**

**Binance REST API + WebSocket:** Fuente de datos OHLCV en tiempo real.
Biblioteca: python-binance

**Telegram Bot API:** Comunicación con el trader. Biblioteca:
python-telegram-bot v20.x

**TradingView Screenshot API:** Captura de gráficos con indicadores
(servicio externo como screenshotapi.net o playwright headless)

**Groq API:** LLM para análisis contextual y generación de texto.
Modelo: llama3-70b o mixtral. Tier gratuito disponible

**3.3 Análisis Técnico**

**Pandas:** Procesamiento y manipulación de datos de velas (DataFrames)

**TA-Lib o pandas-ta:** Cálculo optimizado de indicadores técnicos: RSI,
MACD, BB, ATR, EMA

**NumPy:** Operaciones vectorizadas para cálculos matemáticos de
soporte/resistencia

**3.4 Base de Datos**

**PostgreSQL 15+:** Base de datos principal para persistencia de
señales, historial y configuración

**asyncpg:** Driver async para PostgreSQL --- alta performance con el
event loop de Python

**Alembic:** Migraciones de base de datos controladas por versiones

**3.5 Infraestructura VPS**

**Ubuntu 22.04 LTS:** Sistema operativo del VPS recomendado

**systemd:** Gestión del servicio: auto-inicio, reinicio ante fallos,
logs del sistema

**Python venv:** Entorno virtual aislado para dependencias del proyecto

**UFW (firewall):** Solo puertos SSH y salida HTTPS abiertos

**3.6 Logging y Monitoreo**

**Python logging:** Logs estructurados con niveles INFO/WARNING/ERROR

**RotatingFileHandler:** Rotación automática de archivos de log para
evitar llenar el disco

**journalctl:** Integración con systemd para consulta de logs del
servicio

**3.7 Configuración y Seguridad**

**python-dotenv:** Carga de variables de entorno desde archivo .env

**Variables .env:** API keys, tokens, credenciales de BD --- nunca en el
código

**.gitignore:** .env y archivos sensibles excluidos del repositorio

**Validación de chat_id:** Solo el chat_id del trader puede ejecutar
comandos

**3.8 Herramientas de Desarrollo**

**Git + GitHub:** Control de versiones y colaboración

**pytest + pytest-asyncio:** Tests unitarios e integración de funciones
async

**Black + isort:** Formateo y ordenado de imports automático

**3.9 Resumen de Dependencias Python (requirements.txt final)**

> ● python-telegram-bot\[job-queue\]\>=20.0
>
> ● python-binance\>=1.0.19
>
> ● pandas\>=2.0
>
> ● pandas-ta\>=0.3.14b
>
> ● numpy\>=1.26
>
> ● asyncpg\>=0.29
>
> ● alembic\>=1.13
>
> ● groq\>=0.4.0 (o openai si se prefiere)
>
> ● python-dotenv\>=1.0
>
> ● aiohttp\>=3.9 (para screenshots y peticiones async)
>
> ● playwright\>=1.40 (opcional, para capturas headless de TradingView)
>
> ● pytest\>=7.0 / pytest-asyncio\>=0.23

**SECCIÓN 4 --- PLAN DE LIMPIEZA, REORGANIZACIÓN Y REESTRUCTURACIÓN**

**4.1 Filosofía de Limpieza**

El repositorio sipsignal (fork de bbalert) contiene código valioso para
criptomonedas y análisis técnico, mezclado con funcionalidades que no
necesitamos: clima, tasas de cambio de Cuba, pagos Telegram Stars,
sistema RSS, recordatorios y más. La estrategia es eliminar
quirúrgicamente lo que no sirve, conservar y refactorizar lo que sí
sirve, y migrar el almacenamiento de JSON a PostgreSQL.

**4.2 Inventario de Código Existente --- Qué Conservar vs Eliminar**

*CONSERVAR y adaptar:*

> ● core/api_client.py → cliente Binance y llamadas de precio
> (refactorizar para async puro)
>
> ● handlers/trading.py → comandos /ta, /p --- base de los nuevos
> handlers de señal
>
> ● utils/logger.py → sistema de logging (adaptarlo para rotación y
> nuevos módulos)
>
> ● core/config.py → gestión de configuración (migrar a dotenv +
> PostgreSQL)
>
> ● core/i18n.py → si se quiere mantener español/inglés (opcional,
> simplificable)
>
> ● systemd/ → archivos de servicio (adaptar nombre y rutas)
>
> ● mbot.sh → script de gestión (adaptar para nuevas dependencias)
>
> ● core/btc_loop.py → lógica de monitoreo BTC (rediseñar como
> strategy_engine.py)

*ELIMINAR completamente:*

> ● core/weather_loop_v2.py --- todo el sistema de clima
>
> ● handlers/weather.py --- handlers de clima
>
> ● utils/weather_manager.py --- gestión de alertas meteorológicas
>
> ● core/valerts_loop.py --- sistema de alertas multi-moneda PRO (lo
> reemplazamos)
>
> ● handlers/alerts.py --- alertas de precio genéricas (reemplazadas por
> señales)
>
> ● handlers/admin.py --- comandos de admin masivo (/ms, /ad) --- no
> necesarios
>
> ● data/\*.json --- todos los archivos JSON de almacenamiento (migrar a
> PostgreSQL)
>
> ● locales/ --- sistema de internacionalización Babel (simplificar a
> solo español)
>
> ● core/loops.py --- bucles genéricos mezclados (separar y reescribir)
>
> ● Todo lo relacionado a: RSS, recordatorios, tasas de cambio Cuba
> (/tasa), Telegram Stars (/shop)
>
> ● data-example/ --- datos de ejemplo del proyecto original

**4.3 Nueva Estructura de Carpetas Propuesta**

La nueva estructura es más clara, modular y orientada exclusivamente a
trading:

sipsignal/

> ├─ bot_main.py → punto de entrada principal del bot
>
> ├─ scheduler.py → coordinador de ciclos de análisis
>
> ├─ requirements.txt
>
> ├─ .env.example → plantilla de variables de entorno
>
> ├─ .gitignore
>
> ├─ core/
>
> │ ├─ config.py → carga y validación de configuración
>
> │ ├─ database.py → pool de conexiones PostgreSQL
>
> │ └─ logger.py → configuración de logging con rotación
>
> ├─ trading/
>
> │ ├─ data_fetcher.py → descarga datos OHLCV desde Binance
>
> │ ├─ technical_analysis.py → cálculo RSI, MACD, BB, EMA, ATR, VWAP
>
> │ ├─ strategy_engine.py → lógica de señal, confluencia, confianza
>
> │ ├─ signal_builder.py → construcción del mensaje de alerta
>
> │ └─ chart_capture.py → capturas de gráficos TradingView
>
> ├─ ai/
>
> │ ├─ groq_client.py → cliente Groq para análisis con LLM
>
> │ └─ prompts.py → prompts para cada tipo de análisis
>
> ├─ handlers/
>
> │ ├─ signal_handler.py → /signal, responde análisis completo
>
> │ ├─ chart_handler.py → /chart \[tf\]
>
> │ ├─ risk_handler.py → /risk \[entrada\] \[sl\] \[tp\]
>
> │ ├─ journal_handler.py → /journal, historial de señales
>
> │ └─ scenario_handler.py → /scenario, análisis alcista/bajista
>
> ├─ db/
>
> │ ├─ migrations/ → scripts Alembic de migración
>
> │ └─ models.py → definición de tablas (signals, users, config)
>
> ├─ tests/
>
> │ ├─ test_technical.py → tests de indicadores técnicos
>
> │ └─ test_strategy.py → tests de lógica de señal
>
> └─ systemd/
>
> └─ sipsignal.service → archivo de servicio systemd adaptado

**4.4 Migración de Almacenamiento: JSON → PostgreSQL**

El sistema original usa archivos JSON para persistencia. La migración
implica:

> ● Tabla \'signals\': id, timestamp, direction (BUY/SELL), price,
> stop_loss, take_profit, confidence, timeframe, indicators_snapshot
> (JSONB), sent_at
>
> ● Tabla \'users\': chat_id, username, created_at, is_active,
> preferences (JSONB)
>
> ● Tabla \'config\': key, value, updated_at (para configuración
> dinámica sin reinicio)
>
> ● No se migran datos anteriores --- base de datos nueva desde cero

**SECCIÓN 5 --- FASES DE IMPLEMENTACIÓN**

**Visión General del Roadmap**

El proyecto se divide en 5 fases progresivas. Cada fase produce un
entregable funcional y verificable antes de avanzar a la siguiente. Este
enfoque garantiza que siempre haya un sistema operativo y reduce el
riesgo de retrabajos.

**FASE 1 --- LIMPIEZA Y ANDAMIAJE BASE (Semana 1)**

*Objetivo: Tener el repositorio limpio, la infraestructura base
configurada y el bot de Telegram respondiendo.*

Tarea 1.1 --- Fork y clonado local del repositorio sipsignal:

> ● Clonar el repositorio en el VPS en la ruta de trabajo.
>
> ● Crear rama \'cleanup\' para hacer todos los cambios de limpieza.
>
> ● Hacer primer commit documentando el estado inicial.

Tarea 1.2 --- Eliminación de código no deseado:

> ● Borrar todos los archivos listados en la sección 4.2 como
> \'ELIMINAR\'.
>
> ● Eliminar imports y referencias cruzadas a los módulos eliminados.
>
> ● Limpiar requirements.txt: eliminar dependencias de clima, pagos y
> RSS.
>
> ● Limpiar bbalert.py (entry point) dejando solo el esqueleto del bot.

Tarea 1.3 --- Crear nueva estructura de carpetas:

> ● Crear los directorios: trading/, ai/, handlers/, db/, tests/ según
> sección 4.3.
>
> ● Crear archivos \_\_init\_\_.py en cada módulo.
>
> ● Renombrar bbalert.py → bot_main.py.

Tarea 1.4 --- Configuración del entorno:

> ● Crear .env.example con todas las variables necesarias documentadas.
>
> ● Configurar python-dotenv en core/config.py.
>
> ● Instalar PostgreSQL en el VPS y crear la base de datos sipsignal_db.
>
> ● Crear el entorno virtual Python y el requirements.txt limpio.

Tarea 1.5 --- Bot funcional mínimo:

> ● El bot responde al comando /start y /status con mensaje de
> confirmación.
>
> ● Verificar que el bot se inicia sin errores con el nuevo
> requirements.txt.
>
> ● Configurar el servicio systemd con el nuevo nombre
> sipsignal.service.

*Entregable de Fase 1:*

> ● Repositorio limpio sin código de clima/alertas/pagos. Bot arrancando
> en VPS.

**FASE 2 --- MOTOR DE DATOS Y ANÁLISIS TÉCNICO (Semanas 2-3)**

*Objetivo: El sistema puede descargar datos de Binance, calcular
indicadores y mostrarlos en Telegram.*

Tarea 2.1 --- Cliente Binance (data_fetcher.py):

> ● Implementar función async que descarga velas OHLCV para BTC/USDT en
> múltiples timeframes.
>
> ● Manejo de errores de red con reintentos exponenciales.
>
> ● Retorna DataFrame de Pandas con columnas: open, high, low, close,
> volume, timestamp.

Tarea 2.2 --- Módulo de indicadores (technical_analysis.py):

> ● Implementar cálculo de RSI(14), MACD(12,26,9), Bollinger
> Bands(20,2), EMA 20/50/200.
>
> ● Implementar ATR(14) para cálculo dinámico de stop-loss.
>
> ● Implementar detección automática de soportes y resistencias por
> máximos/mínimos locales.
>
> ● Implementar función de contexto de tendencia: retorna BULLISH /
> BEARISH / NEUTRAL por timeframe.

Tarea 2.3 --- Captura de gráficos (chart_capture.py):

> ● Integrar con ScreenshotAPI o implementar Playwright headless para
> capturar TradingView.
>
> ● Función que recibe símbolo y timeframe, devuelve imagen en bytes.
>
> ● Cache temporal de gráficos para evitar capturas duplicadas en menos
> de 5 minutos.

Tarea 2.4 --- Handler /signal y /chart:

> ● Implementar /signal: ejecuta análisis técnico manual y envía
> resultado formateado al chat.
>
> ● Implementar /chart \[tf\]: captura y envía gráfico del timeframe
> solicitado.
>
> ● Formatear respuesta en Markdown con emojis, tabla de indicadores y
> nivel de tendencia.

Tarea 2.5 --- Tests de análisis técnico:

> ● Tests unitarios para cada indicador usando datos históricos
> conocidos de BTC.
>
> ● Validar resultados contra cálculos manuales o exportaciones de
> TradingView.

*Entregable de Fase 2:*

> ● El trader puede enviar /signal al bot y recibir análisis técnico
> completo con gráfico adjunto.

**FASE 3 --- MOTOR DE ESTRATEGIA Y SEÑALES AUTOMÁTICAS (Semanas 4-5)**

*Objetivo: El sistema detecta señales según la estrategia definida y las
envía automáticamente.*

Tarea 3.1 --- Definición de la estrategia (strategy_engine.py):

> ● Trabajar con el trader para definir las condiciones exactas de
> entrada BUY/SELL.
>
> ● Implementar las condiciones como funciones booleanas evaluables
> sobre el DataFrame de indicadores.
>
> ● Implementar filtro de confluencia multi-timeframe (ej: señal en 15m
> confirmada por 1H).
>
> ● Implementar sistema de nivel de confianza: ALTA, MEDIA, BAJA según
> cantidad de condiciones cumplidas.
>
> ● Implementar cooldown: no emitir señal duplicada dentro de N horas
> configurables.

Tarea 3.2 --- Constructor de alertas (signal_builder.py):

> ● Función que recibe señal y construye el mensaje completo de
> Telegram.
>
> ● Incluir: dirección, precio actual, stop-loss dinámico (basado en
> ATR), target sugerido, ratio R:R.
>
> ● Incluir resumen de indicadores clave en el mensaje.
>
> ● Formateo profesional con separadores, emojis y sección de
> advertencia de riesgo.

Tarea 3.3 --- Integración con IA (groq_client.py + prompts.py):

> ● Implementar cliente async para Groq API.
>
> ● Crear prompt de análisis de contexto: recibe indicadores y devuelve
> párrafo de análisis en español.
>
> ● Crear prompt de escenarios: alcista, neutral y bajista con
> probabilidades estimadas.
>
> ● Implementar fallback si Groq falla: el mensaje se envía sin análisis
> IA.

Tarea 3.4 --- Scheduler autónomo (scheduler.py):

> ● Implementar ciclo de análisis cada N minutos (configurable, por
> defecto 15 minutos).
>
> ● El scheduler llama a data_fetcher → technical_analysis →
> strategy_engine → signal_builder → notifier.
>
> ● Manejo de excepciones: si un ciclo falla, logear y continuar con el
> siguiente sin detener el sistema.

*Entregable de Fase 3:*

> ● El sistema detecta y envía señales automáticamente 24/7. El trader
> recibe alertas ricas con IA.

**FASE 4 --- BASE DE DATOS Y COMANDOS AVANZADOS (Semana 6)**

*Objetivo: Persistencia completa en PostgreSQL y todos los comandos
interactivos funcionando.*

Tarea 4.1 --- Base de datos (db/):

> ● Crear esquema PostgreSQL con tablas signals, users, config usando
> Alembic.
>
> ● Implementar pool de conexiones async con asyncpg en
> core/database.py.
>
> ● Funciones CRUD: guardar señal, obtener historial, actualizar
> configuración.

Tarea 4.2 --- Handler /risk:

> ● Parsear parámetros: entrada, stop-loss, take-profit.
>
> ● Calcular ratio R:R, porcentaje de pérdida máxima y tamaño de
> posición recomendado.
>
> ● Devolver tabla formateada con los cálculos en Telegram.

Tarea 4.3 --- Handler /journal:

> ● Consultar PostgreSQL para obtener las últimas 10 señales emitidas.
>
> ● Mostrar para cada señal: fecha, dirección, precio, nivel de
> confianza.
>
> ● Opción de ver detalle de una señal específica.

Tarea 4.4 --- Handler /scenario:

> ● Solicitar a Groq análisis de escenarios para BTC en los próximos 3-6
> meses.
>
> ● Incluir datos macroeconómicos relevantes en el prompt (si están
> disponibles).
>
> ● Formatear respuesta en tres bloques: Alcista, Neutral, Bajista.

*Entregable de Fase 4:*

> ● Sistema completo con historial persistente y todos los comandos
> documentados operativos.

**FASE 5 --- ESTABILIZACIÓN, TESTS Y DESPLIEGUE PRODUCCIÓN (Semana
7-8)**

*Objetivo: Sistema robusto, probado y documentado listo para uso
continuo en producción.*

Tarea 5.1 --- Suite de tests:

> ● Tests unitarios de strategy_engine con datos históricos reales.
>
> ● Tests de integración de la cadena completa: fetch → análisis → señal
> → mensaje.
>
> ● Tests de handlers de Telegram con mocks de la API.

Tarea 5.2 --- Hardening de seguridad:

> ● Revisión final de que no hay credenciales en el código.
>
> ● Validación estricta de chat_id en todos los handlers.
>
> ● Configurar rate limiting para evitar abuso de comandos.
>
> ● Revisar permisos de archivos en VPS (chmod 600 para .env).

Tarea 5.3 --- Documentación:

> ● README.md actualizado con instrucciones de instalación paso a paso.
>
> ● Documentar cada comando del bot con ejemplos.
>
> ● Documentar cómo configurar y personalizar la estrategia en
> strategy_engine.py.
>
> ● CHANGELOG.md para versiones futuras.

Tarea 5.4 --- Despliegue final en VPS:

> ● Instalar todas las dependencias en el VPS con entorno virtual.
>
> ● Configurar PostgreSQL con usuario dedicado y contraseña segura.
>
> ● Activar sipsignal.service con systemd: auto-inicio en reboot.
>
> ● Verificar logs durante 48 horas de operación continua.
>
> ● Ajustar parámetros de la estrategia según observaciones iniciales.

*Entregable de Fase 5:*

> ● Sistema en producción estable, documentado y funcionando
> autónomamente 24/7 en el VPS.

**SECCIÓN 6 --- DESARROLLO DE LAS 7 IDEAS PROFESIONALES**

Esta sección detalla cómo se implementará cada una de las ideas
propuestas dentro del sistema.

**Idea 1 --- Analizador de Contexto de Mercado**

Se implementa como un sub-módulo de groq_client.py. Antes de emitir cada
señal, el sistema envía al LLM (Groq) un prompt estructurado con los
valores actuales de los indicadores más relevantes y solicita un
análisis del contexto macro de BTC. El análisis incluye: tendencia
dominante, momentum, divergencias y posibles riesgos. El resultado se
adjunta al mensaje de señal como sección \'Contexto de Mercado\'.

**Idea 2 --- Framework de Análisis Profundo de Acción**

Aunque SipSignal trabaja exclusivamente con BTC (no con acciones), este
framework se adapta al análisis de BTC. El comando /signal activa este
análisis: evalúa el precio actual vs medias móviles (EMA 20/50/200),
volumen relativo, posición respecto a Bollinger Bands, y momentum MACD.
El resultado es un desglose completo enviado al Telegram con semáforo
visual (verde/amarillo/rojo) por cada dimensión.

**Idea 3 --- Calculadora Riesgo-Beneficio**

Implementada como handler independiente (/risk) y también incluida
automáticamente en cada señal emitida. Para las señales automáticas, el
stop-loss se calcula dinámicamente usando el ATR(14) multiplicado por un
factor configurable (por defecto 1.5×ATR). El take-profit se calcula
para mantener un ratio R:R mínimo de 2:1. El mensaje muestra: precio de
entrada, SL, TP, ratio R:R y porcentaje de capital en riesgo.

**Idea 4 --- Escáner de Configuración Técnica**

Es el núcleo de technical_analysis.py. El módulo escanea el gráfico de
BTC automáticamente cada ciclo e identifica: soportes y resistencias por
máximos/mínimos locales de las últimas 50 velas, señales de tendencia
(cruce de medias, MACD crossover, RSI en zonas clave), y patrones de
vela importantes (martillo, envolvente, doji). Esta información forma la
base del análisis de confluencia del strategy_engine.

**Idea 5 --- Motor de Planificación de Escenarios**

Implementado como el comando /scenario. Al ejecutarlo, el sistema envía
al LLM un prompt especializado con: precio actual de BTC, indicadores
técnicos del timeframe diario, posición en el ciclo de mercado estimado,
y niveles clave de soporte/resistencia. La IA devuelve tres escenarios
formateados: Alcista (condiciones necesarias y target), Neutral (rango
esperado) y Bajista (niveles de ruptura y targets a la baja). Este
análisis se puede solicitar manualmente o programar semanalmente.

**Idea 6 --- Revisor de Diario de Trading**

Se implementa en Fase 2 avanzada usando la tabla \'signals\' de
PostgreSQL. El comando /journal muestra el historial de señales. En
fases futuras, el trader podrá marcar el resultado de cada operación
(ganadora/perdedora/cancelada), y el sistema enviará mensualmente un
análisis con IA que identifica patrones: ¿En qué timeframes falla más?
¿Hay sesgo hacia señales BUY o SELL? ¿Las señales de alta confianza
tienen mejor tasa de éxito? Este módulo convierte el bot en una
herramienta de mejora continua del trading.

**Idea 7 --- Constructor de Sistema de Trading (NO SALTARSE)**

Este es el corazón de strategy_engine.py y el elemento más crítico del
proyecto. El sistema de trading se diseña siguiendo tres pilares:

> ● Criterios de entrada claros: combinación específica de indicadores
> que deben cumplirse simultáneamente para generar una señal válida.
> Mínimo 3 condiciones de confluencia requeridas.
>
> ● Reglas de gestión de riesgo: stop-loss dinámico basado en ATR,
> tamaño de posición máximo configurable como porcentaje del capital,
> cooldown entre señales para evitar sobretrading.
>
> ● Proceso de revisión incorporado: cada señal queda registrada en BD
> con todos sus parámetros para revisión posterior. El sistema aprende
> del historial acumulado.

La estrategia inicial se define en colaboración con el trader antes del
inicio de la Fase 3. Se implementa como un archivo de configuración
(strategy_config.py) que permite modificar los parámetros sin tocar el
código del motor, facilitando el backtesting y la optimización.

*SipSignal Trading Bot · Documento de Planificación v1.0 · Confidencial*
