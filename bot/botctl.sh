#!/usr/bin/env bash
#
# botctl.sh - Script de Gestión para SipSignal Trading Bot
# Navaja suiza para administrar el bot: entorno, servicio, diagnóstico, mantenimiento
#
# Uso: ./botctl.sh
#

set -euo pipefail

#==============================================================================
# CONFIGURACIÓN
#==============================================================================

# Colores
readonly COLOR_RESET="\033[0m"
readonly COLOR_GREEN="\033[0;32m"
readonly COLOR_RED="\033[0;31m"
readonly COLOR_YELLOW="\033[0;33m"
readonly COLOR_BLUE="\033[0;34m"
readonly COLOR_CYAN="\033[0;36m"
readonly COLOR_BOLD="\033[1m"
readonly COLOR_DIM="\033[2m"

# Configuración del Bot
readonly SERVICE_NAME="sipsignal"
readonly SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
readonly VENV_DIR="venv"
readonly BOT_SCRIPT="sipsignal.py"
readonly WORKING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly USER_RUNNING="${SUDO_USER:-$USER}"

# Archivos
readonly ENV_FILE=".env"
readonly REQUIREMENTS="requirements.txt"
readonly LOGS_DIR="logs"

#==============================================================================
# FUNCIONES DE UTILIDAD VISUAL
#==============================================================================

# Limpiar pantalla y posicionar cursor
clear_screen() {
    printf "\033[2J\033[H"
}

# Imprimir línea horizontal
print_line() {
    local char="${1:-═}"
    local width="${2:-70}"
    printf "${COLOR_CYAN}╔"
    printf "%${width}s" | tr " " "${char}"
    printf "╗${COLOR_RESET}\n"
}

# Imprimir línea de cierre
print_closing_line() {
    local char="${1:-═}"
    local width="${2:-70}"
    printf "${COLOR_CYAN}╚"
    printf "%${width}s" | tr " " "${char}"
    printf "╝${COLOR_RESET}\n"
}

# Imprimir línea de separación
print_separator() {
    local char="${1:-─}"
    local width="${2:-70}"
    printf "${COLOR_CYAN}╠"
    printf "%${width}s" | tr " " "${char}"
    printf "╣${COLOR_RESET}\n"
}

# Imprimir texto centrado en caja
print_centered() {
    local text="$1"
    local width="${2:-70}"
    local padding=$(( (width - ${#text}) / 2 ))
    printf "${COLOR_CYAN}║${COLOR_RESET}%${padding}s%s%$(($width - $padding - ${#text}))s${COLOR_CYAN}║${COLOR_RESET}\n" "" "$text" ""
}

# Imprimir banner del sistema
print_banner() {
    clear_screen
    print_line "═" 74
    print_centered " ███████╗██╗██████╗ ███████╗██╗ ███████╗ ███╗   ██╗ █████╗ ██╗         " 74
    print_centered " ██╔════╝██║██╔══██╗██╔════╝██║ ██╔════╝ ████╗  ██║██╔══██╗██║         " 74
    print_centered " ███████╗██║██████╔╝███████╗██║ ███████╗ ██╔██╗ ██║███████║██║         " 74
    print_centered " ╚════██║██║██╔═══╝ ╚════██║██║ ╚════██║ ██║╚██╗██║██╔══██║██║         " 74
    print_centered " ███████║██║██║     ███████║██║ ███████║ ██║ ╚████║██║  ██║███████╗    " 74
    print_centered " ╚══════╝╚═╝╚═╝     ╚══════╝╚═╝ ╚══════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝    " 74
    print_centered "                                                      Manager v1.0     " 74
    print_separator "═" 74
    print_centered "VPS + Telegram · Análisis Técnico BTC Automatizado" 74
    print_closing_line "═" 74
    echo ""
}

#==============================================================================
# FUNCIONES DE VALIDACIÓN
#==============================================================================

# Verificar si se ejecuta como root (para operaciones systemd)
check_root() {
    if [[ $EUID -ne 0 ]]; then
        return 1
    fi
    return 0
}

# Verificar si systemd está disponible
check_systemd() {
    if command -v systemctl &> /dev/null; then
        return 0
    fi
    return 1
}

# Verificar si el entorno virtual existe
check_venv_exists() {
    if [[ -d "${VENV_DIR}" && -f "${VENV_DIR}/bin/activate" ]]; then
        return 0
    fi
    return 1
}

# Verificar si el entorno virtual está activado
check_venv_active() {
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        return 0
    fi
    return 1
}

# Verificar dependencias del sistema
check_dependencies() {
    local missing=()

    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    if ! command -v pip3 &> /dev/null; then
        missing+=("pip3")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${COLOR_RED}❌ Dependencias faltantes: ${missing[*]}${COLOR_RESET}"
        return 1
    fi

    return 0
}

# Verificar existencia de archivos necesarios
check_required_files() {
    if [[ ! -f "${REQUIREMENTS}" ]]; then
        echo -e "${COLOR_RED}❌ No se encontró ${REQUIREMENTS}${COLOR_RESET}"
        return 1
    fi

    if [[ ! -f "${BOT_SCRIPT}" ]]; then
        echo -e "${COLOR_RED}❌ No se encontró ${BOT_SCRIPT}${COLOR_RESET}"
        return 1
    fi

    return 0
}

# Verificar estado del servicio
get_service_status() {
    if ! check_systemd; then
        echo "unavailable"
        return
    fi

    if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
        echo "active"
    elif systemctl is-failed --quiet "${SERVICE_NAME}" 2>/dev/null; then
        echo "failed"
    else
        echo "inactive"
    fi
}

# Obtener PID del servicio
get_service_pid() {
    systemctl show --property=MainPID --value "${SERVICE_NAME}" 2>/dev/null || echo "N/A"
}

# Obtener uptime del servicio
get_service_uptime() {
    local pid
    pid=$(get_service_pid)
    if [[ "$pid" != "N/A" && "$pid" -gt 0 ]]; then
        ps -p "$pid" -o etime= 2>/dev/null | tr -d ' ' || echo "N/A"
    else
        echo "N/A"
    fi
}

#==============================================================================
# FUNCIONES DE GESTIÓN DE ENTORNO
#==============================================================================

# Mostrar spinner durante operaciones largas
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while ps -p $pid > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Instalar dependencias desde requirements.txt
install_deps() {
    echo -e "${COLOR_BLUE}📦 Instalando dependencias...${COLOR_RESET}"

    if ! check_venv_exists; then
        echo -e "${COLOR_YELLOW}⚠️  No se encontró entorno virtual. Creando primero...${COLOR_RESET}"
        create_venv
    fi

    # Activar venv temporalmente para la instalación
    (
        source "${VENV_DIR}/bin/activate"
        pip install -q --upgrade pip
        if pip install -r "${REQUIREMENTS}"; then
            echo -e "${COLOR_GREEN}✅ Dependencias instaladas correctamente${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ Error al instalar dependencias${COLOR_RESET}"
            return 1
        fi
    )
}

# Crear entorno virtual
create_venv() {
    echo -e "${COLOR_BLUE}🔧 Creando entorno virtual...${COLOR_RESET}"

    if check_venv_exists; then
        echo -e "${COLOR_YELLOW}⚠️  El entorno virtual ya existe${COLOR_RESET}"
        read -p "¿Deseas recrearlo? (s/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            return 0
        fi
        rm -rf "${VENV_DIR}"
    fi

    if python3 -m venv "${VENV_DIR}"; then
        echo -e "${COLOR_GREEN}✅ Entorno virtual creado${COLOR_RESET}"
        echo -e "${COLOR_CYAN}📦 Instalando dependencias iniciales...${COLOR_RESET}"
        (
            source "${VENV_DIR}/bin/activate"
            pip install -q --upgrade pip
            pip install -q -r "${REQUIREMENTS}"
        ) &
        spinner $!
        echo -e "${COLOR_GREEN}✅ Entorno listo para usar${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ Error al crear entorno virtual${COLOR_RESET}"
        return 1
    fi
}

# Mostrar instrucciones para activar entorno
show_activate_help() {
    echo -e "${COLOR_CYAN}📋 Para activar el entorno virtual manualmente:${COLOR_RESET}"
    echo -e "   ${COLOR_YELLOW}source ${VENV_DIR}/bin/activate${COLOR_RESET}"
    echo
    echo -e "${COLOR_CYAN}📋 Para desactivar:${COLOR_RESET}"
    echo -e "   ${COLOR_YELLOW}deactivate${COLOR_RESET}"
}

# Activar entorno en subshell
activate_venv() {
    if ! check_venv_exists; then
        echo -e "${COLOR_RED}❌ No existe entorno virtual${COLOR_RESET}"
        return 1
    fi

    if check_venv_active; then
        echo -e "${COLOR_GREEN}✅ El entorno virtual ya está activo${COLOR_RESET}"
        return 0
    fi

    echo -e "${COLOR_BLUE}🔄 Activando entorno virtual...${COLOR_RESET}"
    exec bash -c "source ${VENV_DIR}/bin/activate && exec bash"
}

#==============================================================================
# FUNCIONES DE GESTIÓN DE SERVICIO SYSTEMD
#==============================================================================

# Crear archivo de servicio systemd
create_service() {
    echo -e "${COLOR_BLUE}🔧 Configurando servicio systemd...${COLOR_RESET}"

    if ! check_root; then
        echo -e "${COLOR_YELLOW}⚠️  Se requieren privilegios de root para crear el servicio${COLOR_RESET}"
        echo -e "${COLOR_CYAN}📝 Ejecutando con sudo...${COLOR_RESET}"
        exec sudo "$0" create-service
        return
    fi

    if ! check_venv_exists; then
        echo -e "${COLOR_RED}❌ Debes crear el entorno virtual primero${COLOR_RESET}"
        return 1
    fi

    # Verificar que los archivos existen
    if [[ ! -f "${WORKING_DIR}/${BOT_SCRIPT}" ]]; then
        echo -e "${COLOR_RED}❌ No se encontró el script: ${WORKING_DIR}/${BOT_SCRIPT}${COLOR_RESET}"
        return 1
    fi

    # Crear el archivo de servicio
    cat > "${SERVICE_FILE}" << EOL
[Unit]
Description=SipSignal Trading Bot
After=network.target

[Service]
Type=simple
User=${USER_RUNNING}
WorkingDirectory=${WORKING_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${WORKING_DIR}/${VENV_DIR}/bin/python ${WORKING_DIR}/${BOT_SCRIPT}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

    # Verificar que se creó correctamente
    if [[ ! -f "${SERVICE_FILE}" ]]; then
        echo -e "${COLOR_RED}❌ Error: No se pudo crear el archivo de servicio${COLOR_RESET}"
        return 1
    fi

    # Recargar systemd y habilitar servicio
    if systemctl daemon-reload; then
        echo -e "${COLOR_GREEN}✅ systemd recargado${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ Error al recargar systemd${COLOR_RESET}"
        return 1
    fi

    if systemctl enable "${SERVICE_NAME}"; then
        echo -e "${COLOR_GREEN}✅ Servicio habilitado para inicio automático${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}⚠️  No se pudo habilitar el servicio${COLOR_RESET}"
    fi

    echo -e "${COLOR_GREEN}✅ Servicio creado exitosamente${COLOR_RESET}"
    echo -e "${COLOR_CYAN}📍 Ubicación: ${SERVICE_FILE}${COLOR_RESET}"
    echo ""
    echo -e "${COLOR_YELLOW}💡 Próximos pasos:${COLOR_RESET}"
    echo -e "   1. Verifica que el archivo .env esté configurado"
    echo -e "   2. Inicia el bot con la opción 5 o: sudo systemctl start ${SERVICE_NAME}"
}

# Iniciar servicio
start_bot() {
    local status
    status=$(get_service_status)

    if [[ "$status" == "unavailable" ]]; then
        echo -e "${COLOR_RED}❌ systemd no está disponible${COLOR_RESET}"
        echo -e "${COLOR_YELLOW}💡 Puedes iniciar el bot manualmente:${COLOR_RESET}"
        echo -e "   ${VENV_DIR}/bin/python ${BOT_SCRIPT}"
        return 1
    fi

    if [[ "$status" == "active" ]]; then
        echo -e "${COLOR_YELLOW}⚠️  El bot ya está corriendo${COLOR_RESET}"
        return 0
    fi

    # Verificar si el archivo de servicio existe
    if [[ ! -f "${SERVICE_FILE}" ]]; then
        echo -e "${COLOR_RED}❌ El servicio no está creado${COLOR_RESET}"
        echo -e "${COLOR_YELLOW}💡 Debes crear el servicio primero (Opción 4)${COLOR_RESET}"
        return 1
    fi

    # Verificar permisos de root
    if ! check_root; then
        echo -e "${COLOR_YELLOW}⚠️  Se requieren privilegios de root para iniciar el servicio${COLOR_RESET}"
        echo -e "${COLOR_CYAN}📝 Ejecutando con sudo...${COLOR_RESET}"
        if sudo systemctl start "${SERVICE_NAME}"; then
            echo -e "${COLOR_GREEN}✅ Comando enviado correctamente${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ Error al ejecutar con sudo${COLOR_RESET}"
            return 1
        fi
    else
        echo -e "${COLOR_BLUE}▶️  Iniciando SipSignal Bot...${COLOR_RESET}"
        if systemctl start "${SERVICE_NAME}"; then
            echo -e "${COLOR_GREEN}✅ Comando de inicio enviado${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ Error al iniciar el servicio${COLOR_RESET}"
            return 1
        fi
    fi

    # Verificar que realmente inició
    sleep 2
    status=$(get_service_status)
    if [[ "$status" == "active" ]]; then
        echo -e "${COLOR_GREEN}✅ Bot iniciado correctamente${COLOR_RESET}"
    elif [[ "$status" == "failed" ]]; then
        echo -e "${COLOR_RED}❌ El servicio falló al iniciar${COLOR_RESET}"
        echo -e "${COLOR_CYAN}📋 Logs del error:${COLOR_RESET}"
        journalctl -u "${SERVICE_NAME}" --no-pager -n 10
        echo ""
        echo -e "${COLOR_YELLOW}💡 Posibles causas:${COLOR_RESET}"
        echo "   • Verifica que el archivo .env esté configurado"
        echo "   • Revisa que el entorno virtual exista"
        echo "   • Comprueba permisos del directorio de trabajo"
        return 1
    else
        echo -e "${COLOR_YELLOW}⚠️  El servicio está en estado: ${status}${COLOR_RESET}"
        echo -e "${COLOR_CYAN}📋 Revisa el estado con: sudo systemctl status ${SERVICE_NAME}${COLOR_RESET}"
        return 1
    fi
}

# Detener servicio
stop_bot() {
    local status
    status=$(get_service_status)

    if [[ "$status" == "unavailable" ]]; then
        echo -e "${COLOR_RED}❌ systemd no está disponible${COLOR_RESET}"
        return 1
    fi

    if [[ "$status" == "inactive" ]]; then
        echo -e "${COLOR_YELLOW}⚠️  El bot ya está detenido${COLOR_RESET}"
        return 0
    fi

    echo -e "${COLOR_BLUE}⏹️  Deteniendo SipSignal Bot...${COLOR_RESET}"

    if ! check_root; then
        if sudo systemctl stop "${SERVICE_NAME}"; then
            echo -e "${COLOR_GREEN}✅ Bot detenido${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ Error al detener el servicio${COLOR_RESET}"
            return 1
        fi
    else
        if systemctl stop "${SERVICE_NAME}"; then
            echo -e "${COLOR_GREEN}✅ Bot detenido${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ Error al detener el servicio${COLOR_RESET}"
            return 1
        fi
    fi
}

# Reiniciar servicio
restart_bot() {
    local status
    status=$(get_service_status)

    if [[ "$status" == "unavailable" ]]; then
        echo -e "${COLOR_RED}❌ systemd no está disponible${COLOR_RESET}"
        return 1
    fi

    echo -e "${COLOR_BLUE}🔄 Reiniciando SipSignal Bot...${COLOR_RESET}"

    local cmd_prefix=""
    if ! check_root; then
        cmd_prefix="sudo "
    fi

    if ${cmd_prefix}systemctl restart "${SERVICE_NAME}"; then
        sleep 2
        status=$(get_service_status)
        if [[ "$status" == "active" ]]; then
            echo -e "${COLOR_GREEN}✅ Bot reiniciado correctamente${COLOR_RESET}"
        else
            echo -e "${COLOR_RED}❌ El servicio no se reinició correctamente${COLOR_RESET}"
            echo -e "${COLOR_CYAN}📋 Estado actual: ${status}${COLOR_RESET}"
            return 1
        fi
    else
        echo -e "${COLOR_RED}❌ Error al reiniciar el servicio${COLOR_RESET}"
        return 1
    fi
}

#==============================================================================
# FUNCIONES DE DIAGNÓSTICO
#==============================================================================

# Ver logs en tiempo real
view_logs() {
    local status
    status=$(get_service_status)

    if [[ "$status" == "unavailable" ]]; then
        echo -e "${COLOR_YELLOW}⚠️  systemd no disponible, mostrando logs locales...${COLOR_RESET}"
        if [[ -d "${LOGS_DIR}" ]]; then
            tail -f "${LOGS_DIR}"/*.log 2>/dev/null || echo "No hay logs disponibles"
        else
            echo -e "${COLOR_RED}❌ No se encontró directorio de logs${COLOR_RESET}"
        fi
        return
    fi

    echo -e "${COLOR_BLUE}📋 Mostrando logs (Ctrl+C para salir)...${COLOR_RESET}"
    echo -e "${COLOR_DIM}Últimas 50 líneas, siguiendo en tiempo real${COLOR_RESET}"
    echo ""

    journalctl -u "${SERVICE_NAME}" -n 50 -f
}

# Mostrar estado detallado del servicio
show_status() {
    local status
    status=$(get_service_status)

    print_banner

    echo -e "${COLOR_BOLD}📊 ESTADO DEL SERVICIO${COLOR_RESET}"
    echo ""

    if [[ "$status" == "unavailable" ]]; then
        echo -e "${COLOR_YELLOW}⚠️  systemd no está disponible en este sistema${COLOR_RESET}"
        return 1
    fi

    # Estado con color
    case "$status" in
        active)
            echo -e "  Estado: ${COLOR_GREEN}● Activo${COLOR_RESET}"
            ;;
        failed)
            echo -e "  Estado: ${COLOR_RED}● Fallido${COLOR_RESET}"
            ;;
        inactive)
            echo -e "  Estado: ${COLOR_DIM}○ Inactivo${COLOR_RESET}"
            ;;
        *)
            echo -e "  Estado: ${COLOR_YELLOW}⚠ Desconocido${COLOR_RESET}"
            ;;
    esac

    local pid
    pid=$(get_service_pid)
    echo -e "  PID:    ${COLOR_CYAN}${pid}${COLOR_RESET}"

    local uptime
    uptime=$(get_service_uptime)
    echo -e "  Uptime: ${COLOR_CYAN}${uptime}${COLOR_RESET}"

    echo ""

    # Información adicional
    if [[ "$status" == "active" ]]; then
        echo -e "${COLOR_DIM}  Información del proceso:${COLOR_RESET}"
        ps -p "$pid" -o pid,ppid,cmd,%mem,%cpu 2>/dev/null | tail -n 1
    fi

    # Información del servicio
    if [[ -f "${SERVICE_FILE}" ]]; then
        echo ""
        echo -e "${COLOR_DIM}  Archivo de servicio: ${SERVICE_FILE}${COLOR_RESET}"
    else
        echo ""
        echo -e "${COLOR_YELLOW}  ⚠️  El archivo de servicio no existe${COLOR_RESET}"
        echo -e "${COLOR_DIM}     Crea el servicio con la opción 4${COLOR_RESET}"
    fi

    echo ""
}

# Health check completo
health_check() {
    print_banner

    echo -e "${COLOR_BOLD}🏥 HEALTH CHECK${COLOR_RESET}"
    echo ""

    local checks_passed=0
    local total_checks=6

    # Check 1: Python3
    if command -v python3 &> /dev/null; then
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Python3 instalado"
        ((checks_passed++))
    else
        echo -e "  ${COLOR_RED}✗${COLOR_RESET} Python3 NO instalado"
    fi

    # Check 2: Entorno virtual
    if check_venv_exists; then
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Entorno virtual existe"
        ((checks_passed++))
    else
        echo -e "  ${COLOR_RED}✗${COLOR_RESET} Entorno virtual NO existe"
    fi

    # Check 3: Dependencias instaladas
    if check_venv_exists; then
        if "${VENV_DIR}/bin/python" -c "import telegram" 2>/dev/null; then
            echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Dependencias instaladas"
            ((checks_passed++))
        else
            echo -e "  ${COLOR_RED}✗${COLOR_RESET} Dependencias NO instaladas"
        fi
    else
        echo -e "  ${COLOR_YELLOW}⚠${COLOR_RESET} No se puede verificar dependencias"
    fi

    # Check 4: Archivo .env
    if [[ -f "${ENV_FILE}" ]]; then
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Archivo .env existe"
        ((checks_passed++))
    else
        echo -e "  ${COLOR_RED}✗${COLOR_RESET} Archivo .env NO existe"
    fi

    # Check 5: Servicio systemd
    local status
    status=$(get_service_status)
    if [[ "$status" == "active" ]]; then
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Servicio systemd activo"
        ((checks_passed++))
    elif [[ "$status" == "unavailable" ]]; then
        echo -e "  ${COLOR_YELLOW}⚠${COLOR_RESET} systemd no disponible"
    else
        echo -e "  ${COLOR_RED}✗${COLOR_RESET} Servicio systemd inactivo"
    fi

    # Check 6: Permisos de escritura
    if [[ -w "." ]]; then
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Permisos de escritura OK"
        ((checks_passed++))
    else
        echo -e "  ${COLOR_RED}✗${COLOR_RESET} Sin permisos de escritura"
    fi

    echo ""
    echo -e "${COLOR_BOLD}Resultado: ${checks_passed}/${total_checks} checks pasados${COLOR_RESET}"

    if [[ $checks_passed -eq $total_checks ]]; then
        echo -e "${COLOR_GREEN}✅ Todo está en orden!${COLOR_RESET}"
    elif [[ $checks_passed -ge 4 ]]; then
        echo -e "${COLOR_YELLOW}⚠️  Algunos elementos necesitan atención${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ Hay problemas que deben resolverse${COLOR_RESET}"
    fi

    echo ""
}

#==============================================================================
# FUNCIONES DE MANTENIMIENTO
#==============================================================================

# Limpiar logs antiguos
clean_logs() {
    echo -e "${COLOR_BLUE}🧹 Limpieza de logs...${COLOR_RESET}"

    if [[ -d "${LOGS_DIR}" ]]; then
        local log_count
        log_count=$(find "${LOGS_DIR}" -name "*.log" | wc -l)

        if [[ $log_count -eq 0 ]]; then
            echo -e "${COLOR_YELLOW}⚠️  No hay logs para limpiar${COLOR_RESET}"
            return 0
        fi

        echo -e "Se encontraron ${log_count} archivos de log"
        read -p "¿Deseas eliminar los logs antiguos (>7 días)? (s/N): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Ss]$ ]]; then
            find "${LOGS_DIR}" -name "*.log" -mtime +7 -delete
            echo -e "${COLOR_GREEN}✅ Logs antiguos eliminados${COLOR_RESET}"
        else
            echo -e "${COLOR_DIM}Operación cancelada${COLOR_RESET}"
        fi
    else
        echo -e "${COLOR_YELLOW}⚠️  Directorio de logs no encontrado${COLOR_RESET}"
    fi

    # Limpiar journal systemd si está disponible
    if check_systemd && check_root; then
        echo -e "${COLOR_BLUE}🧹 Limpiando journal systemd...${COLOR_RESET}"
        journalctl --vacuum-time=7d --quiet
        echo -e "${COLOR_GREEN}✅ Journal limpiado${COLOR_RESET}"
    fi
}

# Crear backup de configuración
backup_config() {
    local backup_dir="backups/$(date +%Y-%m-%d-%H%M%S)"

    echo -e "${COLOR_BLUE}💾 Creando backup...${COLOR_RESET}"

    mkdir -p "${backup_dir}"

    # Backup de .env
    if [[ -f "${ENV_FILE}" ]]; then
        cp "${ENV_FILE}" "${backup_dir}/"
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} .env copiado"
    fi

    # Backup de logs recientes
    if [[ -d "${LOGS_DIR}" ]]; then
        cp -r "${LOGS_DIR}" "${backup_dir}/" 2>/dev/null || true
        echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} Logs copiados"
    fi

    # Comprimir
    local tar_file="${backup_dir}.tar.gz"
    tar -czf "${tar_file}" -C "${backup_dir%/*}" "${backup_dir##*/}"
    rm -rf "${backup_dir}"

    echo -e "${COLOR_GREEN}✅ Backup creado: ${tar_file}${COLOR_RESET}"
}

# Reset completo del bot
reset_bot() {
    print_banner

    echo -e "${COLOR_RED}${COLOR_BOLD}⚠️  ADVERTENCIA: RESET COMPLETO${COLOR_RESET}"
    echo ""
    echo -e "${COLOR_YELLOW}Esta acción:${COLOR_RESET}"
    echo "  • Detendrá el bot"
    echo "  • Eliminará el entorno virtual"
    echo "  • Limpiará archivos temporales"
    echo "  • Reinstalará todo desde cero"
    echo ""
    echo -e "${COLOR_RED}Los archivos de configuración (.env) NO se eliminarán${COLOR_RESET}"
    echo ""

    read -p "¿Estás COMPLETAMENTE SEGURO? Escribe 'RESET' para confirmar: " confirm

    if [[ "$confirm" != "RESET" ]]; then
        echo -e "${COLOR_DIM}Operación cancelada${COLOR_RESET}"
        return 0
    fi

    echo -e "${COLOR_BLUE}🔄 Iniciando reset completo...${COLOR_RESET}"

    # 1. Detener servicio
    local status
    status=$(get_service_status)
    if [[ "$status" == "active" ]]; then
        echo -e "  → Deteniendo servicio..."
        systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    fi

    # 2. Limpiar archivos temporales
    echo -e "  → Limpiando archivos temporales..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true

    # 3. Recrear entorno virtual
    echo -e "  → Recreando entorno virtual..."
    rm -rf "${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"

    # 4. Reinstalar dependencias
    echo -e "  → Reinstalando dependencias..."
    (
        source "${VENV_DIR}/bin/activate"
        pip install -q --upgrade pip
        pip install -q -r "${REQUIREMENTS}"
    ) &
    spinner $!

    # 5. Reiniciar servicio
    echo -e "  → Reiniciando servicio..."
    systemctl start "${SERVICE_NAME}" 2>/dev/null || true

    echo ""
    echo -e "${COLOR_GREEN}✅ Reset completo finalizado${COLOR_RESET}"
    echo -e "${COLOR_CYAN}📋 El bot debería estar iniciándose. Verifica el estado con la opción 9.${COLOR_RESET}"

    echo ""
}

#==============================================================================
# SISTEMA DE MENÚS
#==============================================================================

# Mostrar barra de estado superior
show_status_bar() {
    local status
    status=$(get_service_status)
    local status_color
    local status_text

    case "$status" in
        active)
            status_color="$COLOR_GREEN"
            status_text="● Activo"
            ;;
        failed)
            status_color="$COLOR_RED"
            status_text="● Fallido"
            ;;
        inactive)
            status_color="$COLOR_DIM"
            status_text="○ Inactivo"
            ;;
        *)
            status_color="$COLOR_YELLOW"
            status_text="⚠ N/A"
            ;;
    esac

    local pid=$(get_service_pid)
    local uptime=$(get_service_uptime)

    printf "${COLOR_CYAN}║${COLOR_RESET} "
    printf "${COLOR_BOLD}Bot:${COLOR_RESET} ${status_color}%s${COLOR_RESET} | " "$status_text"
    printf "${COLOR_DIM}PID:${COLOR_RESET} %s | " "$pid"
    printf "${COLOR_DIM}Uptime:${COLOR_RESET} %s" "$uptime"
    printf " %$(($(tput cols) - 40))s${COLOR_CYAN}║${COLOR_RESET}\n" ""
}

# Mostrar menú principal
show_main_menu() {
    print_banner

    print_line "═" 74
    show_status_bar
    print_separator "═" 74

    # Sección Entorno
    echo -e "${COLOR_CYAN}║${COLOR_RESET}                                                                         ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}  ${COLOR_GREEN}🟢 ENTORNO${COLOR_RESET}                                               ${COLOR_BLUE}🔵 SERVICIO${COLOR_RESET}        ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_BOLD}[1]${COLOR_RESET} Instalar dependencias                      ${COLOR_BOLD}[4]${COLOR_RESET} Crear servicio      ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_BOLD}[2]${COLOR_RESET} Crear virtualenv                           ${COLOR_BOLD}[5]${COLOR_RESET} Iniciar bot         ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_BOLD}[3]${COLOR_RESET} Activar entorno                            ${COLOR_BOLD}[6]${COLOR_RESET} Detener bot         ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}                                                          ${COLOR_BOLD}[7]${COLOR_RESET} Reiniciar bot       ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}                                                                         ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}  ${COLOR_YELLOW}🟡 DIAGNÓSTICO${COLOR_RESET}                                           ${COLOR_RED}🔴 MANTENIMIENTO${COLOR_RESET}   ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_BOLD}[8]${COLOR_RESET}  Ver logs en vivo                          ${COLOR_BOLD}[11]${COLOR_RESET} Limpiar logs       ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_BOLD}[9]${COLOR_RESET}  Estado del servicio                       ${COLOR_BOLD}[12]${COLOR_RESET} Backup config      ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_BOLD}[10]${COLOR_RESET} Health check                              ${COLOR_BOLD}[13]${COLOR_RESET} Reset completo     ${COLOR_CYAN}║${COLOR_RESET}"
    echo -e "${COLOR_CYAN}║${COLOR_RESET}                                                                         ${COLOR_CYAN}║${COLOR_RESET}"
    print_separator "═" 74
    echo -e "${COLOR_CYAN}║${COLOR_RESET}    ${COLOR_DIM}[0]${COLOR_RESET} Salir    ${COLOR_DIM}[h]${COLOR_RESET} Ayuda    ${COLOR_DIM}[v]${COLOR_RESET} Versión                            ${COLOR_CYAN}║${COLOR_RESET}"
    print_closing_line "═" 74
}

# Mostrar ayuda
show_help() {
    print_banner

    echo -e "${COLOR_BOLD}📖 AYUDA DE BOTCTL${COLOR_RESET}"
    echo ""
    echo "Este script te permite gestionar fácilmente el bot SipSignal."
    echo ""
    echo -e "${COLOR_GREEN}Flujo recomendado para primera instalación:${COLOR_RESET}"
    echo "  1. Crear entorno virtual (Opción 2)"
    echo "  2. Instalar dependencias (Opción 1)"
    echo "  3. Configurar archivo .env con tus credenciales"
    echo "  4. Crear servicio systemd (Opción 4) - requiere sudo"
    echo "  5. Iniciar el bot (Opción 5)"
    echo ""
    echo -e "${COLOR_YELLOW}Comandos útiles:${COLOR_RESET}"
    echo "  sudo systemctl status sipsignal  - Ver estado detallado"
    echo "  sudo journalctl -u sipsignal -f  - Ver logs en tiempo real"
    echo "  sudo systemctl enable sipsignal  - Habilitar inicio automático"
    echo ""
}

# Mostrar versión
show_version() {
    echo -e "${COLOR_CYAN}botctl.sh v1.0 - SipSignal Manager${COLOR_RESET}"
    echo -e "${COLOR_DIM}Para el bot de trading SipSignal${COLOR_RESET}"
}

#==============================================================================
# MAIN LOOP
#==============================================================================

main() {
    # Verificar dependencias básicas
    if ! check_dependencies; then
        exit 2
    fi

    # Si se pasaron argumentos, ejecutar comando directamente
    case "${1:-}" in
        install|deps)
            install_deps
            exit 0
            ;;
        venv)
            create_venv
            exit 0
            ;;
        start)
            start_bot
            exit 0
            ;;
        stop)
            stop_bot
            exit 0
            ;;
        restart)
            restart_bot
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        logs)
            view_logs
            exit 0
            ;;
        create-service)
            create_service
            exit 0
            ;;
        health)
            health_check
            exit 0
            ;;
        backup)
            backup_config
            exit 0
            ;;
        clean)
            clean_logs
            exit 0
            ;;
        reset)
            reset_bot
            exit 0
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        version|--version|-v)
            show_version
            exit 0
            ;;
    esac

    # Modo interactivo
    while true; do
        show_main_menu
        echo ""
        read -p "Selecciona una opción: " choice

        case $choice in
            1) install_deps ;;
            2) create_venv ;;
            3) activate_venv ;;
            4) create_service ;;
            5) start_bot ;;
            6) stop_bot ;;
            7) restart_bot ;;
            8) view_logs ;;
            9) show_status ;;
            10) health_check ;;
            11) clean_logs ;;
            12) backup_config ;;
            13) reset_bot ;;
            0|q|Q)
                echo -e "${COLOR_GREEN}👋 ¡Hasta luego!${COLOR_RESET}"
                exit 0
                ;;
            h|H) show_help ;;
            v|V) show_version ;;
            *)
                echo -e "${COLOR_RED}❌ Opción inválida${COLOR_RESET}"
                sleep 1
                ;;
        esac

        echo ""
        if [[ "$choice" != "8" && "$choice" != "q" && "$choice" != "Q" ]]; then
            read -n 1 -s -r -p "Presiona cualquier tecla para continuar..."
        fi
    done
}

# Capturar Ctrl+C para salida limpia
trap 'echo -e "\n${COLOR_YELLOW}⚠️  Interrumpido por usuario${COLOR_RESET}"; exit 130' INT

# Ejecutar main
main "$@"
