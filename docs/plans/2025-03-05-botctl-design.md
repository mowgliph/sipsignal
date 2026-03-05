# Diseño: botctl.sh - Script de Gestión para SipSignal

**Fecha:** 2025-03-05  
**Estado:** Aprobado para implementación  
**Autor:** Kilo

---

## 1. Resumen

Script bash tipo "navaja suiza" para gestionar el bot de trading SipSignal. Incluye menú interactivo con interfaz visual atractiva, gestión de dependencias, entorno virtual, servicio systemd y herramientas de diagnóstico/mantenimiento.

---

## 2. Arquitectura

### 2.1 Estructura del Script

```
botctl.sh
├── Configuración Inicial
│   ├── Variables de entorno (colores, paths)
│   └── Definición de constantes
├── Utilidades Visuales
│   ├── print_banner() - Logo ASCII animado
│   ├── print_menu() - Menú principal formateado
│   └── print_status() - Estados con iconos y colores
├── Funciones de Validación
│   ├── check_root() - Verificar permisos sudo
│   ├── check_systemd() - Detectar disponibilidad systemd
│   ├── check_venv() - Verificar entorno virtual
│   └── check_dependencies() - Validar python3, pip3
├── Funciones de Acción
│   ├── install_deps() - Instalar requirements.txt
│   ├── create_venv() - Crear entorno virtual
│   ├── create_service() - Generar sipsignal.service
│   ├── start_bot() - Iniciar servicio
│   ├── stop_bot() - Detener servicio
│   ├── restart_bot() - Reiniciar servicio
│   ├── view_logs() - Ver logs en tiempo real
│   ├── check_status() - Estado del servicio
│   ├── health_check() - Validar funcionamiento
│   ├── clean_logs() - Rotar/limpiar logs
│   ├── backup_config() - Backup de .env y configs
│   └── reset_bot() - Reset completo
└── Sistema de Menús
    ├── show_main_menu() - Dashboard principal
    └── handle_input() - Procesar selección
```

### 2.2 Variables de Configuración

```bash
# Configuración del Bot
SERVICE_NAME="sipsignal"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="venv"
BOT_SCRIPT="sipsignal.py"
WORKING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_RUNNING="${SUDO_USER:-$USER}"

# Archivos de configuración
ENV_FILE=".env"
REQUIREMENTS="requirements.txt"
LOGS_DIR="logs"

# Colores
COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_RED="\033[0;31m"
COLOR_YELLOW="\033[0;33m"
COLOR_BLUE="\033[0;34m"
COLOR_CYAN="\033[0;36m"
COLOR_BOLD="\033[1m"
```

---

## 3. Diseño de Interfaz

### 3.1 Logo ASCII

```
╔══════════════════════════════════════════════════════════╗
║   ███████╗██╗██████╗ ███████╗██╗ ███████╗ ███╗   ██╗ █████╗ ██╗         ║
║   ██╔════╝██║██╔══██╗██╔════╝██║ ██╔════╝ ████╗  ██║██╔══██╗██║         ║
║   ███████╗██║██████╔╝███████╗██║ ███████╗ ██╔██╗ ██║███████║██║         ║
║   ╚════██║██║██╔═══╝ ╚════██║██║ ╚════██║ ██║╚██╗██║██╔══██║██║         ║
║   ███████║██║██║     ███████║██║ ███████║ ██║ ╚████║██║  ██║███████╗    ║
║   ╚══════╝╚═╝╚═╝     ╚══════╝╚═╝ ╚══════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝    ║
║                                                      Manager v1.0         ║
╚══════════════════════════════════════════════════════════╝
```

### 3.2 Menú Principal

```
╔══════════════════════════════════════════════════════════╗
║  📊 ESTADO DEL SERVICIO                                  ║
║  ├── Bot: ● Activo (PID: 12345)                          ║
║  ├── Uptime: 2h 34m                                      ║
║  └── Último reinicio: 2025-03-05 09:15                   ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  🟢 ENTORNO                    🔵 SERVICIO              ║
║  [1] Instalar dependencias     [4] Crear servicio systemd║
║  [2] Crear virtualenv          [5] Iniciar bot          ║
║  [3] Activar entorno           [6] Detener bot          ║
║                                [7] Reiniciar bot        ║
║                                                          ║
║  🟡 DIAGNÓSTICO                🔴 MANTENIMIENTO         ║
║  [8] Ver logs en vivo          [11] Limpiar logs       ║
║  [9] Estado del servicio       [12] Backup config      ║
║  [10] Health check             [13] Reset completo     ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║  [0] Salir    [h] Ayuda    [v] Ver versión               ║
╚══════════════════════════════════════════════════════════╝
```

### 3.3 Leyenda de Colores

- 🟢 **Verde**: Operación exitosa, servicio activo
- 🔴 **Rojo**: Error, servicio detenido
- 🟡 **Amarillo**: Advertencia, requiere atención
- 🔵 **Azul**: Información, proceso en curso
- ⚪ **Gris**: Inactivo, no disponible

---

## 4. Funcionalidades

### 4.1 Gestión de Entorno

#### Instalar Dependencias (Opción 1)
- Verifica existencia de `requirements.txt`
- Detecta si hay venv activo o lo activa automáticamente
- Ejecuta `pip install -r requirements.txt`
- Muestra progreso con spinner
- Valida instalación exitosa

#### Crear VirtualEnv (Opción 2)
- Verifica si `venv/` ya existe (advertir)
- Crea entorno con `python3 -m venv venv`
- Instala dependencias automáticamente
- Muestra instrucciones de activación

#### Activar Entorno (Opción 3)
- Verifica si venv existe
- Muestra comando de activación
- Opción para activar en subshell

### 4.2 Gestión de Servicio Systemd

#### Crear Servicio (Opción 4)
- Verifica permisos root/sudo
- Genera archivo `/etc/systemd/system/sipsignal.service`:

```ini
[Unit]
Description=SipSignal Trading Bot
After=network.target

[Service]
Type=simple
User=${USER_RUNNING}
WorkingDirectory=${WORKING_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${WORKING_DIR}/venv/bin/python ${WORKING_DIR}/sipsignal.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

- Recarga systemd: `systemctl daemon-reload`
- Habilita inicio automático

#### Iniciar/Detener/Reiniciar (Opciones 5-7)
- Ejecuta comandos systemctl correspondientes
- Muestra spinner durante la operación
- Verifica estado final y reporta

### 4.3 Diagnóstico

#### Ver Logs (Opción 8)
- Modo follow: `journalctl -f -u sipsignal`
- Opción para ver últimas N líneas
- Opción para exportar logs a archivo

#### Estado del Servicio (Opción 9)
- Ejecuta `systemctl status sipsignal`
- Formatea salida con colores
- Muestra tiempo de actividad, uso de recursos

#### Health Check (Opción 10)
- Verifica que el proceso esté corriendo
- Verifica que los archivos de config existan
- Verifica espacio en disco
- Verifica permisos de directorios
- Reporte visual con checkmarks

### 4.4 Mantenimiento

#### Limpiar Logs (Opción 11)
- Rotar logs antiguos en `logs/`
- Limpiar journal systemd: `journalctl --vacuum-time=7d`
- Confirmación antes de ejecutar

#### Backup Config (Opción 12)
- Crea directorio `backups/YYYY-MM-DD/`
- Copia `.env`
- Copia directorio `logs/`
- Comprime en tar.gz
- Muestra ubicación del backup

#### Reset Completo (Opción 13)
- **ADVERTENCIA**: Requiere confirmación doble
- Detiene el servicio
- Limpia __pycache__ y archivos .pyc
- Elimina y recrea venv
- Reinstala dependencias
- Reinicia el servicio
- Verifica funcionamiento

---

## 5. Manejo de Errores

### 5.1 Validaciones Previas

| Verificación | Comando | Acción si falla |
|-------------|---------|-----------------|
| Python 3 instalado | `command -v python3` | Abortar con error 2 |
| pip3 disponible | `command -v pip3` | Sugerir instalación |
| systemd disponible | `command -v systemctl` | Modo degradado |
| Permisos de escritura | `test -w .` | Abortar con error 3 |
| Archivo .env existe | `test -f .env` | Advertencia amarilla |

### 5.2 Códigos de Salida

- `0`: Ejecución exitosa
- `1`: Error general
- `2`: Dependencia faltante (python3/pip3)
- `3`: Permisos insuficientes
- `4`: Servicio no encontrado
- `130`: Interrupción por usuario (Ctrl+C)

### 5.3 Logging del Script

- Archivo: `~/.botctl.log`
- Formato: `[YYYY-MM-DD HH:MM:SS] [NIVEL] Mensaje`
- Niveles: DEBUG, INFO, WARN, ERROR

---

## 6. Consideraciones de Seguridad

- No almacenar credenciales en el script
- Validar todas las entradas de usuario
- Usar `set -euo pipefail` para modo estricto
- No ejecutar como root a menos que sea necesario
- Confirmar acciones destructivas

---

## 7. Requisitos Técnicos

### 7.1 Dependencias del Sistema
- `bash` >= 4.0
- `python3` >= 3.8
- `pip3`
- `systemd` (opcional, para gestión de servicios)
- `journalctl` (para logs)

### 7.2 Permisos Necesarios
- Lectura/escritura en directorio del proyecto
- `sudo` para operaciones systemd (crear servicio)

---

## 8. Futuras Mejoras (Opcional)

- [ ] Soporte para múltiples instancias del bot
- [ ] Integración con notificaciones (telegram/email)
- [ ] Dashboard web embebido
- [ ] Autocompletado con TAB
- [ ] Modo silencioso para CI/CD
- [ ] Soporte para Docker

---

## 9. Aprobación

**Diseño aprobado por:** Usuario  
**Fecha de aprobación:** 2025-03-05  
**Estado:** ✅ Listo para implementación
