#!/bin/bash

##############################################
# Script de Instalación del Portal Cautivo SDN
# Grupo 2 - Configuración Completa del Sistema
##############################################

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si se ejecuta como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script debe ejecutarse como root (usar sudo)"
        exit 1
    fi
}

# Función para instalar dependencias Python
install_python_dependencies() {
    log_info "Instalando dependencias de Python..."
    
    # Actualizar pip
    python3 -m pip install --upgrade pip
    
    # Instalar dependencias del proyecto
    pip3 install flask requests subprocess32 mysql-connector-python
    
    log_success "Dependencias de Python instaladas"
}

# Función para configurar FreeRADIUS si no está configurado
setup_freeradius() {
    log_info "Verificando configuración de FreeRADIUS..."
    
    if ! systemctl is-active --quiet freeradius; then
        log_warning "FreeRADIUS no está ejecutándose. Iniciando configuración..."
        
        # Instalar FreeRADIUS si no está instalado
        if ! command -v freeradius &> /dev/null; then
            log_info "Instalando FreeRADIUS..."
            apt-get update
            apt-get install -y freeradius freeradius-mysql mysql-server
        fi
        
        # Configurar y reiniciar FreeRADIUS
        systemctl enable freeradius
        systemctl start freeradius
        
        log_success "FreeRADIUS configurado e iniciado"
    else
        log_success "FreeRADIUS ya está ejecutándose"
    fi
}

# Función para verificar configuración de red
check_network_config() {
    log_info "Verificando configuración de red..."
    
    # Verificar IP del host
    HOST_IP=$(hostname -I | awk '{print $1}')
    log_info "IP del host: $HOST_IP"
    
    # Verificar conectividad con el controlador SDN (si está configurado)
    CONTROLLER_IP="10.0.0.2"  # Ajustar según tu configuración
    if ping -c 1 $CONTROLLER_IP &> /dev/null; then
        log_success "Conectividad con controlador SDN ($CONTROLLER_IP) verificada"
    else
        log_warning "No se puede alcanzar el controlador SDN en $CONTROLLER_IP"
        log_warning "Asegúrate de que el controlador esté ejecutándose"
    fi
}

# Función para configurar iptables para portal cautivo
setup_iptables() {
    log_info "Configurando reglas de iptables para portal cautivo..."
    
    # Limpiar reglas existentes (opcional, comentar si no deseas esto)
    # iptables -F
    # iptables -t nat -F
    
    # Redirigir tráfico HTTP al portal cautivo
    iptables -t nat -I PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:5000
    iptables -t nat -I PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.0.0.1:5000
    
    # Permitir tráfico hacia el portal
    iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
    
    # Permitir DNS
    iptables -I INPUT -p udp --dport 53 -j ACCEPT
    iptables -I OUTPUT -p udp --dport 53 -j ACCEPT
    
    log_success "Reglas de iptables configuradas"
}

# Función para crear archivos de configuración
create_config_files() {
    log_info "Creando archivos de configuración..."
    
    # Crear archivo de configuración del portal
    cat > /etc/captive-portal-sdn.conf << EOF
# Configuración del Portal Cautivo SDN
# Grupo 2

[RADIUS]
server = localhost
port = 1812
secret = radius_secret_sdn

[PORTAL]
host = 0.0.0.0
port = 5000
debug = false

[SDN_CONTROLLER]
url = http://10.0.0.2:8081
timeout = 10

[LOGGING]
level = INFO
file = /var/log/captive_portal_sdn.log
EOF

    # Crear directorio de logs
    mkdir -p /var/log
    touch /var/log/captive_portal_sdn.log
    chmod 644 /var/log/captive_portal_sdn.log
    
    log_success "Archivos de configuración creados"
}

# Función para crear servicios systemd
create_systemd_services() {
    log_info "Creando servicios systemd..."
    
    # Servicio para el portal cautivo
    cat > /etc/systemd/system/captive-portal-sdn.service << EOF
[Unit]
Description=Portal Cautivo SDN - Grupo 2
After=network.target freeradius.service mysql.service
Wants=freeradius.service mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sdn_grupo2
ExecStart=/usr/bin/python3 /opt/sdn_grupo2/captive_portal.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Servicio para el controlador SDN
    cat > /etc/systemd/system/sdn-controller.service << EOF
[Unit]
Description=Controlador SDN para Portal Cautivo - Grupo 2
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sdn_grupo2
ExecStart=/usr/bin/python3 /opt/sdn_grupo2/sdn_controller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Recargar systemd
    systemctl daemon-reload
    
    log_success "Servicios systemd creados"
}

# Función para copiar archivos al directorio de instalación
install_files() {
    log_info "Instalando archivos del sistema..."
    
    # Crear directorio de instalación
    INSTALL_DIR="/opt/sdn_grupo2"
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/templates
    
    # Copiar archivos Python
    if [[ -f "captive_portal.py" ]]; then
        cp captive_portal.py $INSTALL_DIR/
        chmod +x $INSTALL_DIR/captive_portal.py
    else
        log_error "No se encontró captive_portal.py en el directorio actual"
        exit 1
    fi
    
    if [[ -f "sdn_controller.py" ]]; then
        cp sdn_controller.py $INSTALL_DIR/
        chmod +x $INSTALL_DIR/sdn_controller.py
    else
        log_error "No se encontró sdn_controller.py en el directorio actual"
        exit 1
    fi
    
    # Copiar templates si existen
    if [[ -d "templates" ]]; then
        cp -r templates/* $INSTALL_DIR/templates/
    else
        log_warning "No se encontró el directorio templates"
    fi
    
    # Establecer permisos
    chown -R root:root $INSTALL_DIR
    chmod -R 755 $INSTALL_DIR
    
    log_success "Archivos instalados en $INSTALL_DIR"
}

# Función para verificar el estado del sistema
verify_installation() {
    log_info "Verificando instalación..."
    
    # Verificar archivos
    if [[ -f "/opt/sdn_grupo2/captive_portal.py" ]] && [[ -f "/opt/sdn_grupo2/sdn_controller.py" ]]; then
        log_success "Archivos principales encontrados"
    else
        log_error "Faltan archivos principales"
        return 1
    fi
    
    # Verificar servicios
    if systemctl list-unit-files | grep -q "captive-portal-sdn.service"; then
        log_success "Servicio del portal cautivo instalado"
    else
        log_error "Servicio del portal cautivo no encontrado"
        return 1
    fi
    
    if systemctl list-unit-files | grep -q "sdn-controller.service"; then
        log_success "Servicio del controlador SDN instalado"
    else
        log_error "Servicio del controlador SDN no encontrado"
        return 1
    fi
    
    log_success "Instalación verificada correctamente"
}

# Función para mostrar información post-instalación
show_post_install_info() {
    echo ""
    echo "============================================="
    echo "  INSTALACIÓN COMPLETADA - PORTAL CAUTIVO SDN"
    echo "============================================="
    echo ""
    echo "📋 SERVICIOS INSTALADOS:"
    echo "  • Portal Cautivo: captive-portal-sdn.service"
    echo "  • Controlador SDN: sdn-controller.service"
    echo ""
    echo "📂 ARCHIVOS INSTALADOS EN:"
    echo "  • /opt/sdn_grupo2/"
    echo "  • /etc/captive-portal-sdn.conf"
    echo "  • /var/log/captive_portal_sdn.log"
    echo ""
    echo "🚀 COMANDOS PARA INICIAR:"
    echo "  sudo systemctl start captive-portal-sdn"
    echo "  sudo systemctl start sdn-controller"
    echo ""
    echo "📊 COMANDOS PARA MONITOREAR:"
    echo "  sudo systemctl status captive-portal-sdn"
    echo "  sudo systemctl status sdn-controller"
    echo "  sudo tail -f /var/log/captive_portal_sdn.log"
    echo ""
    echo "🌐 URLS DEL SISTEMA:"
    echo "  • Portal Cautivo: http://10.0.0.1:5000"
    echo "  • API Controlador SDN: http://10.0.0.1:8081"
    echo "  • Estado del sistema: http://10.0.0.1:5000/status"
    echo ""
    echo "⚙️ CONFIGURACIÓN:"
    echo "  • Editar: /etc/captive-portal-sdn.conf"
    echo "  • Logs: /var/log/captive_portal_sdn.log"
    echo ""
    echo "📚 DOCUMENTACIÓN:"
    echo "  • Ver DOCUMENTACION_SISTEMA.md para más detalles"
    echo "  • Usuarios de prueba configurados en FreeRADIUS"
    echo ""
    echo "✅ Sistema listo para usar!"
    echo "============================================="
}

# Función principal
main() {
    echo "============================================="
    echo "  INSTALADOR DEL PORTAL CAUTIVO SDN - GRUPO 2"
    echo "============================================="
    echo ""
    
    check_root
    
    log_info "Iniciando instalación del Portal Cautivo SDN..."
    
    # Ejecutar pasos de instalación
    install_python_dependencies
    setup_freeradius
    check_network_config
    create_config_files
    install_files
    create_systemd_services
    setup_iptables
    verify_installation
    
    show_post_install_info
    
    echo ""
    log_success "¡Instalación completada exitosamente!"
    echo ""
}

# Función para desinstalación
uninstall() {
    log_info "Desinstalando Portal Cautivo SDN..."
    
    # Parar servicios
    systemctl stop captive-portal-sdn 2>/dev/null || true
    systemctl stop sdn-controller 2>/dev/null || true
    
    # Deshabilitar servicios
    systemctl disable captive-portal-sdn 2>/dev/null || true
    systemctl disable sdn-controller 2>/dev/null || true
    
    # Eliminar archivos de servicio
    rm -f /etc/systemd/system/captive-portal-sdn.service
    rm -f /etc/systemd/system/sdn-controller.service
    
    # Eliminar archivos de instalación
    rm -rf /opt/sdn_grupo2
    rm -f /etc/captive-portal-sdn.conf
    
    # Recargar systemd
    systemctl daemon-reload
    
    log_success "Desinstalación completada"
}

# Verificar argumentos de línea de comandos
case "${1:-install}" in
    install)
        main
        ;;
    uninstall)
        check_root
        uninstall
        ;;
    status)
        echo "=== ESTADO DEL SISTEMA ==="
        systemctl status captive-portal-sdn --no-pager || echo "Portal Cautivo: No instalado"
        systemctl status sdn-controller --no-pager || echo "Controlador SDN: No instalado"
        ;;
    *)
        echo "Uso: $0 {install|uninstall|status}"
        echo ""
        echo "  install   - Instalar el sistema completo"
        echo "  uninstall - Desinstalar el sistema"
        echo "  status    - Mostrar estado de los servicios"
        exit 1
        ;;
esac
