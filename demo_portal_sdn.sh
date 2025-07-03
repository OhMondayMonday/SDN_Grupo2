#!/bin/bash

##############################################
# Demostración del Portal Cautivo SDN
# Grupo 2 - Guía de Uso y Configuración
##############################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con estilo
print_header() {
    echo -e "\n${PURPLE}============================================="
    echo -e "$1"
    echo -e "=============================================${NC}\n"
}

print_step() {
    echo -e "${CYAN}[PASO $1]${NC} $2"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_command() {
    echo -e "${YELLOW}$ $1${NC}"
}

# Función para esperar input del usuario
wait_for_user() {
    echo -e "\n${CYAN}Presiona ENTER para continuar...${NC}"
    read
}

# Función de demostración principal
demo_sistema_completo() {
    print_header "🌐 DEMOSTRACIÓN DEL PORTAL CAUTIVO SDN - GRUPO 2"
    
    echo "Este script te guiará a través de todo el proceso de configuración"
    echo "y uso del sistema de portal cautivo con controlador SDN."
    echo ""
    echo "🎯 Objetivos de la demostración:"
    echo "  1. Configuración inicial del sistema"
    echo "  2. Verificación de servicios"
    echo "  3. Pruebas de autenticación RADIUS"
    echo "  4. Demostración del portal web"
    echo "  5. Gestión de flujos SDN"
    echo "  6. Monitoreo y logs"
    
    wait_for_user
    
    # Paso 1: Verificación del entorno
    print_header "🔍 PASO 1: VERIFICACIÓN DEL ENTORNO"
    
    print_step "1.1" "Verificando sistema operativo y dependencias"
    print_command "cat /etc/os-release | grep PRETTY_NAME"
    cat /etc/os-release | grep PRETTY_NAME
    
    print_command "python3 --version"
    python3 --version
    
    print_command "mysql --version"
    mysql --version 2>/dev/null || print_warning "MySQL no encontrado"
    
    print_command "systemctl status freeradius --no-pager -l"
    systemctl status freeradius --no-pager -l || print_warning "FreeRADIUS no está ejecutándose"
    
    wait_for_user
    
    # Paso 2: Configuración de la red
    print_header "🌐 PASO 2: CONFIGURACIÓN DE RED"
    
    print_step "2.1" "Verificando configuración de red actual"
    print_command "ip addr show"
    ip addr show | grep -E "(inet|UP|DOWN)" | head -10
    
    print_step "2.2" "Verificando conectividad entre componentes"
    PORTAL_IP="10.0.0.1"
    CONTROLLER_IP="10.0.0.2"
    
    print_info "Portal Cautivo: $PORTAL_IP:5000"
    print_info "Controlador SDN: $CONTROLLER_IP:8081"
    
    print_command "ping -c 3 $CONTROLLER_IP"
    ping -c 3 $CONTROLLER_IP 2>/dev/null && print_success "Conectividad OK" || print_warning "Controlador no alcanzable"
    
    wait_for_user
    
    # Paso 3: Configuración de FreeRADIUS
    print_header "🔐 PASO 3: CONFIGURACIÓN DE RADIUS"
    
    print_step "3.1" "Verificando configuración de FreeRADIUS"
    print_command "radtest admin admin123 localhost 1812 radius_secret_sdn"
    
    echo "Probando autenticación RADIUS con usuario 'admin'..."
    if radtest admin admin123 localhost 1812 radius_secret_sdn 2>/dev/null | grep -q "Access-Accept"; then
        print_success "Autenticación RADIUS exitosa"
    else
        print_error "Fallo en autenticación RADIUS"
        echo "Verifica que FreeRADIUS esté configurado correctamente"
    fi
    
    print_step "3.2" "Probando otros usuarios de prueba"
    for user in "profesor1:prof123" "estudiante1:est123" "invitado1:inv123"; do
        username=$(echo $user | cut -d: -f1)
        password=$(echo $user | cut -d: -f2)
        
        print_command "radtest $username $password localhost 1812 radius_secret_sdn"
        if radtest $username $password localhost 1812 radius_secret_sdn 2>/dev/null | grep -q "Access-Accept"; then
            print_success "✅ Usuario $username: Autenticación exitosa"
        else
            print_warning "❌ Usuario $username: Fallo en autenticación"
        fi
    done
    
    wait_for_user
    
    # Paso 4: Iniciando servicios
    print_header "🚀 PASO 4: INICIANDO SERVICIOS DEL SISTEMA"
    
    print_step "4.1" "Iniciando el Portal Cautivo"
    print_command "cd /opt/sdn_grupo2 && python3 captive_portal.py &"
    
    if [[ -f "/opt/sdn_grupo2/captive_portal.py" ]]; then
        echo "Iniciando portal cautivo en background..."
        cd /opt/sdn_grupo2
        python3 captive_portal.py > /var/log/captive_portal_demo.log 2>&1 &
        PORTAL_PID=$!
        sleep 3
        
        if kill -0 $PORTAL_PID 2>/dev/null; then
            print_success "Portal Cautivo iniciado (PID: $PORTAL_PID)"
        else
            print_error "Error al iniciar el Portal Cautivo"
        fi
    else
        print_warning "Archivo captive_portal.py no encontrado en /opt/sdn_grupo2"
        print_info "Usando archivo local si existe..."
        if [[ -f "captive_portal.py" ]]; then
            python3 captive_portal.py > /tmp/captive_portal_demo.log 2>&1 &
            PORTAL_PID=$!
            sleep 3
            print_success "Portal Cautivo iniciado localmente (PID: $PORTAL_PID)"
        fi
    fi
    
    print_step "4.2" "Iniciando el Controlador SDN"
    print_command "python3 sdn_controller.py &"
    
    if [[ -f "/opt/sdn_grupo2/sdn_controller.py" ]]; then
        cd /opt/sdn_grupo2
        python3 sdn_controller.py > /var/log/sdn_controller_demo.log 2>&1 &
        CONTROLLER_PID=$!
        sleep 3
        
        if kill -0 $CONTROLLER_PID 2>/dev/null; then
            print_success "Controlador SDN iniciado (PID: $CONTROLLER_PID)"
        else
            print_error "Error al iniciar el Controlador SDN"
        fi
    else
        print_warning "Archivo sdn_controller.py no encontrado en /opt/sdn_grupo2"
        if [[ -f "sdn_controller.py" ]]; then
            python3 sdn_controller.py > /tmp/sdn_controller_demo.log 2>&1 &
            CONTROLLER_PID=$!
            sleep 3
            print_success "Controlador SDN iniciado localmente (PID: $CONTROLLER_PID)"
        fi
    fi
    
    wait_for_user
    
    # Paso 5: Probando conectividad HTTP
    print_header "🌐 PASO 5: PROBANDO CONECTIVIDAD HTTP"
    
    print_step "5.1" "Verificando que el portal responda"
    print_command "curl -s http://localhost:5000/"
    
    if curl -s --connect-timeout 5 http://localhost:5000/ > /dev/null; then
        print_success "Portal Cautivo respondiendo en http://localhost:5000/"
        
        # Mostrar extracto de la respuesta
        echo -e "\n${CYAN}Extracto de la página de login:${NC}"
        curl -s http://localhost:5000/ | grep -o '<title>[^<]*</title>' || echo "Portal funcionando"
    else
        print_error "Portal Cautivo no responde"
    fi
    
    print_step "5.2" "Verificando API del controlador SDN"
    print_command "curl -s http://localhost:8081/health"
    
    if curl -s --connect-timeout 5 http://localhost:8081/health > /dev/null; then
        print_success "Controlador SDN respondiendo en http://localhost:8081/"
        
        # Mostrar estado del controlador
        echo -e "\n${CYAN}Estado del controlador:${NC}"
        curl -s http://localhost:8081/health | python3 -m json.tool 2>/dev/null || echo "Controlador funcionando"
    else
        print_error "Controlador SDN no responde"
    fi
    
    wait_for_user
    
    # Paso 6: Demostración de autenticación web
    print_header "🔐 PASO 6: DEMOSTRACIÓN DE AUTENTICACIÓN WEB"
    
    print_step "6.1" "Simulando login de usuario via HTTP"
    
    # Crear archivo temporal para cookies
    COOKIE_FILE=$(mktemp)
    
    print_command "curl -c cookies.txt http://localhost:5000/"
    curl -s -c "$COOKIE_FILE" http://localhost:5000/ > /dev/null
    
    print_step "6.2" "Enviando credenciales de usuario 'admin'"
    print_command "curl -b cookies.txt -d 'username=admin&password=admin123' http://localhost:5000/authenticate"
    
    LOGIN_RESPONSE=$(curl -s -b "$COOKIE_FILE" -c "$COOKIE_FILE" \
        -X POST \
        -d "username=admin&password=admin123&client_mac=00:11:22:33:44:55" \
        http://localhost:5000/authenticate)
    
    if echo "$LOGIN_RESPONSE" | grep -q -i "bienvenido\|success\|exitosa"; then
        print_success "✅ Login exitoso para usuario 'admin'"
        echo -e "\n${CYAN}Respuesta del servidor (extracto):${NC}"
        echo "$LOGIN_RESPONSE" | grep -o -i "bienvenido[^<]*" | head -1
    else
        print_warning "❌ Login falló o respuesta inesperada"
        echo "Respuesta del servidor (primeras líneas):"
        echo "$LOGIN_RESPONSE" | head -3
    fi
    
    # Limpiar archivo temporal
    rm -f "$COOKIE_FILE"
    
    wait_for_user
    
    # Paso 7: Verificando logs
    print_header "📊 PASO 7: VERIFICANDO LOGS DEL SISTEMA"
    
    print_step "7.1" "Logs del Portal Cautivo"
    if [[ -f "/var/log/captive_portal_demo.log" ]]; then
        print_command "tail -10 /var/log/captive_portal_demo.log"
        tail -10 /var/log/captive_portal_demo.log
    elif [[ -f "/tmp/captive_portal_demo.log" ]]; then
        print_command "tail -10 /tmp/captive_portal_demo.log"
        tail -10 /tmp/captive_portal_demo.log
    else
        print_warning "No se encontraron logs del portal cautivo"
    fi
    
    print_step "7.2" "Logs del Controlador SDN"
    if [[ -f "/var/log/sdn_controller_demo.log" ]]; then
        print_command "tail -10 /var/log/sdn_controller_demo.log"
        tail -10 /var/log/sdn_controller_demo.log
    elif [[ -f "/tmp/sdn_controller_demo.log" ]]; then
        print_command "tail -10 /tmp/sdn_controller_demo.log"
        tail -10 /tmp/sdn_controller_demo.log
    else
        print_warning "No se encontraron logs del controlador SDN"
    fi
    
    print_step "7.3" "Logs de FreeRADIUS (últimas autenticaciones)"
    if [[ -f "/var/log/freeradius/radius.log" ]]; then
        print_command "tail -5 /var/log/freeradius/radius.log"
        tail -5 /var/log/freeradius/radius.log | grep -i "accept\|reject" || echo "No se encontraron registros recientes"
    else
        print_warning "No se encontraron logs de FreeRADIUS"
    fi
    
    wait_for_user
    
    # Paso 8: APIs y monitoreo
    print_header "📡 PASO 8: APIs DE MONITOREO"
    
    print_step "8.1" "Estado del Portal Cautivo"
    print_command "curl -s http://localhost:5000/status"
    
    PORTAL_STATUS=$(curl -s --connect-timeout 5 http://localhost:5000/status 2>/dev/null)
    if [[ -n "$PORTAL_STATUS" ]]; then
        echo "$PORTAL_STATUS" | python3 -m json.tool 2>/dev/null || echo "$PORTAL_STATUS"
    else
        print_warning "No se pudo obtener estado del portal"
    fi
    
    print_step "8.2" "Estado del Controlador SDN"
    print_command "curl -s http://localhost:8081/api/status"
    
    CONTROLLER_STATUS=$(curl -s --connect-timeout 5 http://localhost:8081/api/status 2>/dev/null)
    if [[ -n "$CONTROLLER_STATUS" ]]; then
        echo "$CONTROLLER_STATUS" | python3 -m json.tool 2>/dev/null || echo "$CONTROLLER_STATUS"
    else
        print_warning "No se pudo obtener estado del controlador"
    fi
    
    print_step "8.3" "Usuarios activos"
    print_command "curl -s http://localhost:8081/api/users"
    
    ACTIVE_USERS=$(curl -s --connect-timeout 5 http://localhost:8081/api/users 2>/dev/null)
    if [[ -n "$ACTIVE_USERS" ]]; then
        echo "$ACTIVE_USERS" | python3 -m json.tool 2>/dev/null || echo "$ACTIVE_USERS"
    else
        print_warning "No se pudo obtener lista de usuarios activos"
    fi
    
    wait_for_user
    
    # Paso 9: Limpieza
    print_header "🧹 PASO 9: LIMPIEZA Y FINALIZACIÓN"
    
    print_step "9.1" "Deteniendo servicios de demostración"
    
    if [[ -n "$PORTAL_PID" ]] && kill -0 $PORTAL_PID 2>/dev/null; then
        print_command "kill $PORTAL_PID"
        kill $PORTAL_PID
        print_success "Portal Cautivo detenido"
    fi
    
    if [[ -n "$CONTROLLER_PID" ]] && kill -0 $CONTROLLER_PID 2>/dev/null; then
        print_command "kill $CONTROLLER_PID"
        kill $CONTROLLER_PID
        print_success "Controlador SDN detenido"
    fi
    
    print_step "9.2" "Limpiando archivos temporales"
    rm -f /tmp/captive_portal_demo.log /tmp/sdn_controller_demo.log
    print_success "Archivos temporales eliminados"
    
    # Resumen final
    print_header "✅ DEMOSTRACIÓN COMPLETADA"
    
    echo "🎉 ¡Felicidades! Has completado la demostración del Portal Cautivo SDN."
    echo ""
    echo "📋 Resumen de lo que se demostró:"
    echo "  ✅ Verificación del entorno y dependencias"
    echo "  ✅ Configuración de red y conectividad"
    echo "  ✅ Autenticación RADIUS con FreeRADIUS"
    echo "  ✅ Funcionamiento del Portal Cautivo web"
    echo "  ✅ Comunicación con el Controlador SDN"
    echo "  ✅ APIs de monitoreo y estado"
    echo "  ✅ Verificación de logs del sistema"
    echo ""
    echo "🚀 Próximos pasos recomendados:"
    echo "  1. Instalar el sistema completo: sudo ./install_portal_sdn.sh"
    echo "  2. Configurar tu topología SDN específica"
    echo "  3. Ajustar políticas de flujos según tus necesidades"
    echo "  4. Realizar pruebas con usuarios reales"
    echo "  5. Configurar monitoreo y alertas en producción"
    echo ""
    echo "📚 Documentación adicional:"
    echo "  • DOCUMENTACION_SISTEMA.md - Guía completa del sistema"
    echo "  • config_portal_sdn.py - Archivo de configuración"
    echo "  • test_portal_sdn.sh - Script de pruebas automatizadas"
    echo ""
    print_success "¡Gracias por probar nuestro Portal Cautivo SDN!"
}

# Función para demostración rápida
demo_rapido() {
    print_header "⚡ DEMOSTRACIÓN RÁPIDA - PORTAL CAUTIVO SDN"
    
    echo "Esta es una versión rápida de la demostración."
    echo "Se ejecutarán las pruebas principales sin pausas."
    echo ""
    
    # Verificar servicios principales
    print_info "Verificando servicios..."
    systemctl is-active freeradius >/dev/null && print_success "✅ FreeRADIUS activo" || print_warning "❌ FreeRADIUS inactivo"
    systemctl is-active mysql >/dev/null && print_success "✅ MySQL activo" || print_warning "❌ MySQL inactivo"
    
    # Probar autenticación RADIUS
    print_info "Probando RADIUS..."
    if radtest admin admin123 localhost 1812 radius_secret_sdn 2>/dev/null | grep -q "Access-Accept"; then
        print_success "✅ Autenticación RADIUS funcional"
    else
        print_error "❌ Problema con autenticación RADIUS"
    fi
    
    # Verificar archivos del proyecto
    print_info "Verificando archivos del proyecto..."
    [[ -f "captive_portal.py" ]] && print_success "✅ captive_portal.py encontrado" || print_error "❌ captive_portal.py no encontrado"
    [[ -f "sdn_controller.py" ]] && print_success "✅ sdn_controller.py encontrado" || print_error "❌ sdn_controller.py no encontrado"
    [[ -d "templates" ]] && print_success "✅ Templates encontrados" || print_error "❌ Templates no encontrados"
    
    # Verificar conectividad de red
    print_info "Verificando red..."
    ping -c 1 localhost >/dev/null && print_success "✅ Conectividad local OK"
    
    print_success "Demostración rápida completada"
}

# Función para mostrar ayuda
show_help() {
    echo "============================================="
    echo "  DEMOSTRACIÓN PORTAL CAUTIVO SDN - AYUDA"
    echo "============================================="
    echo ""
    echo "Uso: $0 [opción]"
    echo ""
    echo "Opciones disponibles:"
    echo "  demo      - Demostración completa paso a paso (por defecto)"
    echo "  quick     - Demostración rápida sin pausas"
    echo "  install   - Guía de instalación"
    echo "  test      - Ejecutar pruebas del sistema"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0              # Demostración completa"
    echo "  $0 quick        # Demostración rápida"
    echo "  $0 install      # Guía de instalación"
    echo ""
}

# Función para guía de instalación
guide_installation() {
    print_header "📦 GUÍA DE INSTALACIÓN - PORTAL CAUTIVO SDN"
    
    echo "Esta guía te ayudará a instalar el sistema paso a paso."
    echo ""
    
    print_step "1" "Preparar el sistema"
    echo "  • Asegúrate de tener Ubuntu/Debian actualizado"
    echo "  • Necesitas permisos de root (sudo)"
    echo "  • Conexión a Internet para descargar dependencias"
    echo ""
    
    print_step "2" "Instalar dependencias básicas"
    print_command "sudo apt update"
    print_command "sudo apt install -y python3 python3-pip mysql-server freeradius freeradius-mysql"
    echo ""
    
    print_step "3" "Instalar dependencias de Python"
    print_command "pip3 install flask requests mysql-connector-python"
    echo ""
    
    print_step "4" "Configurar FreeRADIUS"
    echo "  • Editar /etc/freeradius/3.0/clients.conf"
    echo "  • Configurar base de datos en /etc/freeradius/3.0/mods-available/sql"
    echo "  • Crear usuarios en la base de datos"
    echo ""
    
    print_step "5" "Instalar el sistema"
    print_command "sudo ./install_portal_sdn.sh"
    echo ""
    
    print_step "6" "Iniciar servicios"
    print_command "sudo systemctl start captive-portal-sdn"
    print_command "sudo systemctl start sdn-controller"
    echo ""
    
    print_step "7" "Verificar instalación"
    print_command "./test_portal_sdn.sh all"
    echo ""
    
    print_success "Para más detalles, consulta DOCUMENTACION_SISTEMA.md"
}

# Función principal - manejar argumentos
main() {
    case "${1:-demo}" in
        demo)
            demo_sistema_completo
            ;;
        quick)
            demo_rapido
            ;;
        install)
            guide_installation
            ;;
        test)
            if [[ -f "test_portal_sdn.sh" ]]; then
                ./test_portal_sdn.sh all
            else
                print_error "Script de pruebas no encontrado"
                exit 1
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Opción no válida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Verificar que el script se ejecute en el directorio correcto
if [[ ! -f "captive_portal.py" ]] && [[ ! -f "/opt/sdn_grupo2/captive_portal.py" ]]; then
    print_error "Este script debe ejecutarse desde el directorio del proyecto"
    print_error "o después de instalar el sistema en /opt/sdn_grupo2/"
    exit 1
fi

# Ejecutar función principal
main "$@"
