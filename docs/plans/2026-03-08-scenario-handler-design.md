# Diseño: scenario_handler.py

## Objetivo

Crear el handler `bot/handlers/scenario_handler.py` para el comando `/scenario` que analiza escenarios de mercado.

## Contexto

- El proyecto ya tiene un contenedor de dependencias (`Container`) con `get_scenario_analysis` configurado
- Existe el caso de uso `GetScenarioAnalysis` que retorna análisis de mercado
- El patrón de handlers existentes (ej. `signal_handler.py`) debe seguirse

## Estructura del Archivo

```python
# bot/handlers/scenario_handler.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.core.config import settings


async def scenario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Implementación...


scenario_handlers_list = [
    CommandHandler("scenario", scenario_command),
]
```

## Flujo de Ejecución

1. Verificar acceso de admin con `settings.admin_chat_ids`
2. Enviar mensaje "Analizando escenarios de mercado... ⏳"
3. Obtener container: `container = context.bot_data["container"]`
4. Ejecutar análisis: `text = await container.get_scenario_analysis.execute()`
5. Responder con `parse_mode="Markdown"`
6. Si falla, enviar mensaje de error genérico

## Manejo de Errores

- Acceso denegado: "⛔ Acceso denegado."
- Error en análisis: "⚠️ Error en el análisis: {detalle}"

## Criterios de Éxito

- El comando `/scenario` responde con análisis de mercado
- Usa Markdown para el formato
- Verifica acceso de admin
- Maneja errores gracefully
