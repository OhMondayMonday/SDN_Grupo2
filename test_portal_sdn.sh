#!/bin/bash

##############################################
# Script de Pruebas del Portal Cautivo SDN
# Grupo 2 - Verificación Completa del Sistema
##############################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PORTAL_IP="10.0.0.1"
PORTAL_PORT="5000"
CONTROLLER_IP="10.0.0.1"
CONTROLLER_PORT="8081"
RADIUS_SERVER="localhost"
RADIUS_SECRET="radius_secret_sdn"

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

# Función para verificar que un servicio esté ejecutándose
check_service() {
    local service_name=$1
    local process_name=$2
    
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        log_success "Servicio $service_name está ejecutándose"
        return 0
    elif pgrep -f "$process_name" > /dev/null; then
        log_success "Proceso $process_name está ejecutándose"
        return 0
    else
        log_error "Servicio/proceso $service_name/$process_name NO está ejecutándose"
        return 1
    fi
}

# Función para verificar conectividad HTTP
check_http_endpoint() {
    local url=$1
    local description=$2
    
    log_info "Verificando $description: $url"
    
    if curl -s --connect-timeout 5 "$url" > /dev/null; then
        log_success "$description respondiendo correctamente"
        return 0
    else
        log_error "$description NO responde o no está disponible"
        return 1
    fi
}

# Función para verificar RADIUS
test_radius_auth() {
    local username=$1
    local password=$2
    local expected_result=$3
    
    log_info "Probando autenticación RADIUS: $username"
    
    if command -v radtest > /dev/null; then
        local result=$(radtest "$username" "$password" "$RADIUS_SERVER" 1812 "$RADIUS_SECRET" 2>/dev/null)
        
        if [[ "$expected_result" == "accept" ]] && echo "$result" | grep -q "Access-Accept"; then
            log_success "Autenticación exitosa para $username"
            return 0
        elif [[ "$expected_result" == "reject" ]] && echo "$result" | grep -q "Access-Reject"; then
            log_success "Rechazo correcto para credenciales inválidas"
            return 0
        else
            log_error "Resultado inesperado para $username"
            echo "Resultado: $result"
            return 1
        fi
    else
        log_warning "radtest no está instalado, saltando prueba RADIUS"
        return 1
    fi
}

# Función para probar API del controlador SDN
test_sdn_controller_api() {
    local base_url="http://$CONTROLLER_IP:$CONTROLLER_PORT"
    
    log_info "Probando API del controlador SDN..."
    
    # Probar endpoint de estado
    if curl -s "$base_url/api/status" | jq . > /dev/null 2>&1; then
        log_success "API del controlador SDN responde correctamente"
        
        # Obtener información del estado
        local status=$(curl -s "$base_url/api/status")
        echo "Estado del controlador: $status"
        
        return 0
    else
        log_error "API del controlador SDN no responde o devuelve JSON inválido"
        return 1
    fi
}

# Función para simular autenticación completa
simulate_user_login() {
    local username=$1
    local password=$2
    
    log_info "Simulando login completo para usuario: $username"
    
    # URL del portal
    local portal_url="http://$PORTAL_IP:$PORTAL_PORT"
    
    # Crear sesión temporal
    local cookie_jar=$(mktemp)
    
    # 1. Obtener página de login
    log_info "Paso 1: Obteniendo página de login..."
    if curl -s -c "$cookie_jar" "$portal_url/" > /dev/null; then
        log_success "Página de login obtenida"
    else
        log_error "No se pudo obtener la página de login"
        rm -f "$cookie_jar"
        return 1
    fi
    
    # 2. Enviar credenciales
    log_info "Paso 2: Enviando credenciales..."
    local login_response=$(curl -s -b "$cookie_jar" -c "$cookie_jar" \
        -X POST \
        -d "username=$username&password=$password&client_mac=00:00:00:00:00:01" \
        "$portal_url/authenticate")
    
    if echo "$login_response" | grep -q "Conexión Exitosa\|success\|Bienvenido"; then
        log_success "Login exitoso para $username"
        
        # 3. Verificar estado de sesión
        log_info "Paso 3: Verificando estado de sesión..."
        local status_response=$(curl -s -b "$cookie_jar" "$portal_url/status")
        
        if echo "$status_response" | grep -q "authenticated.*true"; then
            log_success "Sesión verificada correctamente"
        else
            log_warning "Sesión no verificada (puede ser normal según implementación)"
        fi
        
        # 4. Hacer logout
        log_info "Paso 4: Cerrando sesión..."
        curl -s -b "$cookie_jar" "$portal_url/logout" > /dev/null
        log_success "Logout completado"
        
    else
        log_error "Login falló para $username"
        echo "Respuesta: $(echo "$login_response" | head -n 5)"
        rm -f "$cookie_jar"
        return 1
    fi
    
    # Limpiar archivo temporal
    rm -f "$cookie_jar"
    return 0
}

# Función principal de pruebas
run_all_tests() {
    echo "============================================="
    echo "  PRUEBAS DEL PORTAL CAUTIVO SDN - GRUPO 2"
    echo "============================================="
    echo ""
    
    local total_tests=0
    local passed_tests=0
    
    # Test 1: Verificar servicios
    log_info "=== PRUEBA 1: VERIFICACIÓN DE SERVICIOS ==="
    total_tests=$((total_tests + 4))
    
    check_service "freeradius" "freeradius" && passed_tests=$((passed_tests + 1))
    check_service "mysql" "mysql" && passed_tests=$((passed_tests + 1))
    check_service "captive-portal-sdn" "captive_portal.py" && passed_tests=$((passed_tests + 1))
    check_service "sdn-controller" "sdn_controller.py" && passed_tests=$((passed_tests + 1))
    
    echo ""
    
    # Test 2: Verificar conectividad HTTP
    log_info "=== PRUEBA 2: CONECTIVIDAD HTTP ==="
    total_tests=$((total_tests + 3))
    
    check_http_endpoint "http://$PORTAL_IP:$PORTAL_PORT/" "Portal Cautivo" && passed_tests=$((passed_tests + 1))
    check_http_endpoint "http://$PORTAL_IP:$PORTAL_PORT/status" "API Estado Portal" && passed_tests=$((passed_tests + 1))
    check_http_endpoint "http://$CONTROLLER_IP:$CONTROLLER_PORT/health" "Health Check Controlador" && passed_tests=$((passed_tests + 1))
    
    echo ""
    
    # Test 3: Autenticación RADIUS
    log_info "=== PRUEBA 3: AUTENTICACIÓN RADIUS ==="
    total_tests=$((total_tests + 3))
    
    test_radius_auth "admin" "admin123" "accept" && passed_tests=$((passed_tests + 1))
    test_radius_auth "estudiante1" "est123" "accept" && passed_tests=$((passed_tests + 1))
    test_radius_auth "usuario_inexistente" "password_malo" "reject" && passed_tests=$((passed_tests + 1))
    
    echo ""
    
    # Test 4: API del controlador SDN
    log_info "=== PRUEBA 4: API CONTROLADOR SDN ==="
    total_tests=$((total_tests + 1))
    
    test_sdn_controller_api && passed_tests=$((passed_tests + 1))
    
    echo ""
    
    # Test 5: Flujo completo de autenticación
    log_info "=== PRUEBA 5: FLUJO COMPLETO DE AUTENTICACIÓN ==="
    total_tests=$((total_tests + 2))
    
    simulate_user_login "admin" "admin123" && passed_tests=$((passed_tests + 1))
    simulate_user_login "estudiante1" "est123" && passed_tests=$((passed_tests + 1))
    
    echo ""
    
    # Mostrar resultados
    echo "============================================="
    echo "  RESUMEN DE PRUEBAS"
    echo "============================================="
    echo ""
    echo "✅ Pruebas exitosas: $passed_tests"
    echo "❌ Pruebas fallidas: $((total_tests - passed_tests))"
    echo "📊 Total de pruebas: $total_tests"
    echo ""
    
    if [[ $passed_tests -eq $total_tests ]]; then
        log_success "¡TODAS LAS PRUEBAS PASARON! El sistema está funcionando correctamente."
        return 0
    else
        log_warning "Algunas pruebas fallaron. Revisar los logs para más detalles."
        return 1
    fi
}

# Función para pruebas específicas de rendimiento
performance_tests() {
    log_info "=== PRUEBAS DE RENDIMIENTO ==="
    
    # Probar múltiples conexiones simultáneas
    log_info "Probando 10 conexiones simultáneas al portal..."
    
    for i in {1..10}; do
        curl -s "http://$PORTAL_IP:$PORTAL_PORT/" > /dev/null &
    done
    
    wait
    log_success "Prueba de conexiones simultáneas completada"
    
    # Probar tiempo de respuesta
    log_info "Midiendo tiempo de respuesta..."
    local response_time=$(curl -s -w "%{time_total}" -o /dev/null "http://$PORTAL_IP:$PORTAL_PORT/")
    log_info "Tiempo de respuesta del portal: ${response_time}s"
    
    if (( $(echo "$response_time < 2.0" | bc -l) )); then
        log_success "Tiempo de respuesta aceptable"
    else
        log_warning "Tiempo de respuesta alto: ${response_time}s"
    fi
}

# Función para verificar logs
check_logs() {
    log_info "=== VERIFICACIÓN DE LOGS ==="
    
    local log_files=(
        "/var/log/captive_portal_sdn.log"
        "/var/log/freeradius/radius.log"
        "/var/log/syslog"
    )
    
    for log_file in "${log_files[@]}"; do
        if [[ -f "$log_file" ]]; then
            local lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
            log_info "$log_file: $lines líneas"
            
            # Buscar errores recientes
            local errors=$(grep -i error "$log_file" | tail -n 5 2>/dev/null || echo "")
            if [[ -n "$errors" ]]; then
                log_warning "Errores recientes en $log_file:"
                echo "$errors"
            fi
        else
            log_warning "Log no encontrado: $log_file"
        fi
    done
}

# Función para mostrar información del sistema
show_system_info() {
    echo "============================================="
    echo "  INFORMACIÓN DEL SISTEMA"
    echo "============================================="
    echo ""
    echo "🖥️ SISTEMA:"
    echo "  • OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "  • Kernel: $(uname -r)"
    echo "  • Uptime: $(uptime -p)"
    echo ""
    echo "🌐 RED:"
    echo "  • IP Principal: $(hostname -I | awk '{print $1}')"
    echo "  • Hostname: $(hostname)"
    echo ""
    echo "📊 RECURSOS:"
    echo "  • Memoria: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
    echo "  • Disco: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " usado)"}')"
    echo "  • CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
    echo ""
    echo "🐍 PYTHON:"
    echo "  • Versión: $(python3 --version)"
    echo "  • Pip: $(pip3 --version | awk '{print $2}')"
    echo ""
}

# Función de menú principal
main_menu() {
    echo "============================================="
    echo "  HERRAMIENTAS DE PRUEBA - PORTAL CAUTIVO SDN"
    echo "============================================="
    echo ""
    echo "Selecciona una opción:"
    echo ""
    echo "1) Ejecutar todas las pruebas"
    echo "2) Pruebas de servicios únicamente"
    echo "3) Pruebas de conectividad HTTP"
    echo "4) Pruebas RADIUS"
    echo "5) Pruebas de rendimiento"
    echo "6) Verificar logs"
    echo "7) Información del sistema"
    echo "8) Simular login de usuario"
    echo "9) Salir"
    echo ""
    read -p "Opción [1-9]: " choice
    
    case $choice in
        1) run_all_tests ;;
        2) 
            check_service "freeradius" "freeradius"
            check_service "mysql" "mysql"
            check_service "captive-portal-sdn" "captive_portal.py"
            check_service "sdn-controller" "sdn_controller.py"
            ;;
        3)
            check_http_endpoint "http://$PORTAL_IP:$PORTAL_PORT/" "Portal Cautivo"
            check_http_endpoint "http://$PORTAL_IP:$PORTAL_PORT/status" "API Estado Portal"
            check_http_endpoint "http://$CONTROLLER_IP:$CONTROLLER_PORT/health" "Health Check Controlador"
            ;;
        4)
            test_radius_auth "admin" "admin123" "accept"
            test_radius_auth "estudiante1" "est123" "accept"
            test_radius_auth "usuario_inexistente" "password_malo" "reject"
            ;;
        5) performance_tests ;;
        6) check_logs ;;
        7) show_system_info ;;
        8)
            read -p "Usuario: " username
            read -s -p "Contraseña: " password
            echo ""
            simulate_user_login "$username" "$password"
            ;;
        9) exit 0 ;;
        *) 
            log_error "Opción inválida"
            main_menu
            ;;
    esac
}

# Verificar argumentos de línea de comandos
case "${1:-menu}" in
    all|test)
        run_all_tests
        ;;
    performance)
        performance_tests
        ;;
    logs)
        check_logs
        ;;
    info)
        show_system_info
        ;;
    menu)
        main_menu
        ;;
    *)
        echo "Uso: $0 {all|performance|logs|info|menu}"
        echo ""
        echo "  all         - Ejecutar todas las pruebas"
        echo "  performance - Pruebas de rendimiento"
        echo "  logs        - Verificar logs del sistema"
        echo "  info        - Mostrar información del sistema"
        echo "  menu        - Mostrar menú interactivo"
        exit 1
        ;;
esac
