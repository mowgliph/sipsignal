# Prompt 31: Limpiar `bot/utils/file_manager.py`

**Fecha:** 2026-03-08  
**Tipo:** chore  
**Estado:** Pendiente

## 📋 Descripción

Limpiar el archivo `bot/utils/file_manager.py` eliminando funciones que no están siendo utilizadas en el proyecto.

## 🔍 Análisis de Uso

### Funciones Usadas (MANTENER)

| Función | Archivos que la importan |
|---------|-------------------------|
| `cargar_usuarios` | `handlers/admin.py`, `main.py`, `utils/telemetry.py` |
| `migrate_user_timestamps` | `handlers/admin.py` (también llamada internamente por `cargar_usuarios`) |
| `get_user_language` | `handlers/user_settings.py` |
| `set_user_language` | `handlers/user_settings.py` |
| `registrar_uso_comando` | `handlers/ta.py` |
| `add_log_line` | `main.py` |
| `guardar_usuarios` | `main.py` |
| `obtener_datos_usuario_seguro` | Uso interno (`check_feature_access`, `registrar_uso_comando`, `add_subscription_days`) |
| `check_feature_access` | `handlers/general.py` (línea 87) |
| `obtener_monedas_usuario` | `handlers/general.py` (línea 98) |
| `load_last_prices_status` | `handlers/general.py` (línea 121) |
| `obtener_datos_usuario` | `handlers/general.py` (línea 189) |
| `add_subscription_days` | Uso interno (posible uso desde handlers) |
| `registrar_usuario` | Uso interno (posible uso desde handlers) |
| `actualizar_monedas` | Uso interno (posible uso desde handlers) |

### Funciones No Usadas (ELIMINAR)

| Función | Razón |
|---------|-------|
| `inicializar_archivos` | Solo contiene `pass`, no hace nada útil |
| `save_last_prices_status` | No tiene ningún uso detectado en el proyecto |

## ✅ Tareas

1. [ ] Eliminar función `inicializar_archivos()` y su llamada al inicio del módulo
2. [ ] Eliminar función `save_last_prices_status()`
3. [ ] Ejecutar tests para verificar que no hay regresiones
4. [ ] Ejecutar linting (ruff check/format)

## 🧪 Verificación

```bash
# Verificar imports
grep -r "from bot.utils.file_manager import\|from utils.file_manager import" bot/ --include="*.py"

# Ejecutar tests
pytest

# Linting
ruff check . --fix
ruff format .
```

## 📝 Notas

- No eliminar funciones que tienen uso interno aunque no sean importadas directamente
- Mantener compatibilidad con handlers existentes
