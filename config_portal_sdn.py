# ==================================================
# CONFIGURACIÓN DEL PORTAL CAUTIVO SDN - GRUPO 2
# ==================================================
# 
# Este archivo contiene la configuración principal del sistema.
# Modifica los valores según tu entorno específico.

# ==================================================
# CONFIGURACIÓN DE RED
# ==================================================

# IP del servidor donde se ejecuta el portal cautivo (h1)
PORTAL_HOST="10.0.0.1"
PORTAL_PORT=5000

# IP del servidor donde se ejecuta el controlador SDN (h2)
SDN_CONTROLLER_HOST="10.0.0.2"
SDN_CONTROLLER_PORT=8081

# URL de Floodlight (ajustar según tu instalación)
FLOODLIGHT_URL="http://localhost:8080"

# Redes permitidas/denegadas por defecto
ALLOWED_NETWORKS=["0.0.0.0/0"]  # Permitir todo por defecto
BLOCKED_NETWORKS=["169.254.0.0/16", "224.0.0.0/4"]  # Bloquear link-local y multicast

# ==================================================
# CONFIGURACIÓN DE RADIUS
# ==================================================

# Servidor RADIUS (FreeRADIUS)
RADIUS_SERVER="localhost"
RADIUS_PORT=1812
RADIUS_SECRET="radius_secret_sdn"
RADIUS_TIMEOUT=10

# Base de datos MySQL para RADIUS
MYSQL_HOST="localhost"
MYSQL_PORT=3306
MYSQL_USER="radius"
MYSQL_PASSWORD="radius_password"
MYSQL_DATABASE="radius"

# ==================================================
# CONFIGURACIÓN DE USUARIOS Y ROLES
# ==================================================

# Roles disponibles y sus configuraciones
ROLES = {
    "ROLE_ADMIN": {
        "vlan_id": 10,
        "priority": 1000,
        "description": "Administrador con acceso completo",
        "session_timeout": 28800,  # 8 horas
        "internet_access": True,
        "internal_access": True,
        "ssh_access": True,
        "allowed_ports": [22, 53, 80, 443, 8080, 8443]
    },
    
    "ROLE_PROFESOR": {
        "vlan_id": 15,
        "priority": 800,
        "description": "Profesor con acceso extendido",
        "session_timeout": 14400,  # 4 horas
        "internet_access": True,
        "internal_access": True,
        "ssh_access": True,
        "allowed_ports": [22, 53, 80, 443, 993, 995]
    },
    
    "ROLE_ESTUDIANTE": {
        "vlan_id": 20,
        "priority": 600,
        "description": "Estudiante con acceso web básico",
        "session_timeout": 7200,   # 2 horas
        "internet_access": True,
        "internal_access": False,
        "ssh_access": False,
        "allowed_ports": [53, 80, 443]
    },
    
    "ROLE_GUEST": {
        "vlan_id": 30,
        "priority": 400,
        "description": "Invitado con acceso limitado",
        "session_timeout": 3600,   # 1 hora
        "internet_access": True,
        "internal_access": False,
        "ssh_access": False,
        "allowed_ports": [53, 80, 443],
        "bandwidth_limit": "10Mbps"
    },
    
    "ROLE_IOT": {
        "vlan_id": 40,
        "priority": 200,
        "description": "Dispositivo IoT restringido",
        "session_timeout": 86400,  # 24 horas
        "internet_access": False,
        "internal_access": True,
        "ssh_access": False,
        "allowed_ports": [53, 1883, 8883],  # DNS, MQTT
        "allowed_servers": ["10.0.0.100"]   # Solo servidor IoT
    },
    
    "ROLE_SOPORTE": {
        "vlan_id": 50,
        "priority": 700,
        "description": "Soporte técnico",
        "session_timeout": 14400,  # 4 horas
        "internet_access": True,
        "internal_access": True,
        "ssh_access": True,
        "allowed_ports": [22, 23, 53, 80, 161, 443, 3389]  # SSH, Telnet, SNMP, RDP
    }
}

# ==================================================
# CONFIGURACIÓN DE SWITCHES SDN
# ==================================================

# Switches en la topología (ajustar según tu configuración)
SWITCHES = {
    "00:00:00:00:00:00:00:01": {
        "name": "s1",
        "description": "Switch principal",
        "ports": [1, 2, 3, 4],
        "uplink_port": 4
    },
    "00:00:00:00:00:00:00:02": {
        "name": "s2", 
        "description": "Switch de acceso 1",
        "ports": [1, 2, 3, 4],
        "uplink_port": 1
    },
    "00:00:00:00:00:00:00:03": {
        "name": "s3",
        "description": "Switch de acceso 2", 
        "ports": [1, 2, 3, 4],
        "uplink_port": 1
    }
}

# ==================================================
# CONFIGURACIÓN DE POLÍTICAS DE FLUJOS
# ==================================================

# Políticas base por tipo de tráfico
FLOW_POLICIES = {
    "WEB_HTTP": {
        "match": "tp_dst=80",
        "priority": 500,
        "action": "output=normal"
    },
    
    "WEB_HTTPS": {
        "match": "tp_dst=443", 
        "priority": 500,
        "action": "output=normal"
    },
    
    "DNS": {
        "match": "tp_dst=53",
        "priority": 600,
        "action": "output=normal"
    },
    
    "SSH": {
        "match": "tp_dst=22",
        "priority": 400,
        "action": "output=normal"
    },
    
    "BLOCK_INTERNAL": {
        "match": "nw_dst=192.168.0.0/16",
        "priority": 700,
        "action": "drop"
    },
    
    "BLOCK_PRIVATE_10": {
        "match": "nw_dst=10.0.0.0/8",
        "priority": 700, 
        "action": "drop"
    },
    
    "ALLOW_ALL": {
        "match": "",
        "priority": 100,
        "action": "output=normal"
    },
    
    "DENY_ALL": {
        "match": "",
        "priority": 50,
        "action": "drop"
    }
}

# ==================================================
# CONFIGURACIÓN DE LOGGING
# ==================================================

# Configuración de logs
LOGGING = {
    "level": "INFO",                                    # DEBUG, INFO, WARNING, ERROR
    "file": "/var/log/captive_portal_sdn.log",
    "max_size": "10MB",
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# Logs específicos
RADIUS_LOG = "/var/log/freeradius/radius.log"
CONTROLLER_LOG = "/var/log/sdn_controller.log"
FLOODLIGHT_LOG = "/var/log/floodlight/floodlight.log"

# ==================================================
# CONFIGURACIÓN DE SEGURIDAD
# ==================================================

# Configuración de sesiones
SESSION_CONFIG = {
    "secret_key": "sdn_captive_portal_secret_key_grupo2_2025",
    "session_timeout_default": 3600,  # 1 hora por defecto
    "max_concurrent_sessions": 1000,
    "cleanup_interval": 300,          # Limpiar cada 5 minutos
    "remember_me_days": 0             # No recordar sesiones
}

# Configuración de seguridad
SECURITY = {
    "max_login_attempts": 3,
    "lockout_duration": 300,          # 5 minutos
    "password_min_length": 6,
    "require_https": False,           # Cambiar a True en producción
    "allowed_redirect_domains": ["google.com", "wikipedia.org"]
}

# ==================================================
# CONFIGURACIÓN DE IPTABLES
# ==================================================

# Reglas de iptables para portal cautivo
IPTABLES_RULES = [
    # Permitir tráfico local
    "iptables -I INPUT -i lo -j ACCEPT",
    
    # Permitir conexiones establecidas
    "iptables -I INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
    
    # Permitir SSH (puerto 22)
    "iptables -I INPUT -p tcp --dport 22 -j ACCEPT",
    
    # Permitir portal cautivo (puerto 5000)
    "iptables -I INPUT -p tcp --dport 5000 -j ACCEPT", 
    
    # Permitir controlador SDN (puerto 8081)
    "iptables -I INPUT -p tcp --dport 8081 -j ACCEPT",
    
    # Permitir DNS
    "iptables -I INPUT -p udp --dport 53 -j ACCEPT",
    "iptables -I OUTPUT -p udp --dport 53 -j ACCEPT",
    
    # Redirigir HTTP al portal cautivo
    "iptables -t nat -I PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:5000",
    
    # Redirigir puerto 8080 al portal cautivo  
    "iptables -t nat -I PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.0.0.1:5000"
]

# ==================================================
# CONFIGURACIÓN DE MONITOREO
# ==================================================

# Configuración de monitoreo y alertas
MONITORING = {
    "health_check_interval": 30,      # Segundos
    "max_response_time": 2.0,         # Segundos
    "alert_on_failures": True,
    "notification_email": "admin@universidad.edu",
    "metrics_retention_days": 30
}

# Umbrales de alertas
ALERT_THRESHOLDS = {
    "active_users": 1000,
    "failed_authentications_per_minute": 10,
    "memory_usage_percent": 80,
    "disk_usage_percent": 85,
    "response_time_ms": 2000
}

# ==================================================
# CONFIGURACIÓN DE DESARROLLO/DEBUG
# ==================================================

# Configuración para desarrollo
DEBUG_CONFIG = {
    "flask_debug": False,
    "test_users_enabled": True,
    "mock_radius_responses": False,
    "verbose_logging": False,
    "profile_requests": False
}

# Usuarios de prueba (solo para desarrollo)
TEST_USERS = {
    "admin": {
        "password": "admin123", 
        "role": "ROLE_ADMIN"
    },
    "profesor1": {
        "password": "prof123",
        "role": "ROLE_PROFESOR" 
    },
    "estudiante1": {
        "password": "est123",
        "role": "ROLE_ESTUDIANTE"
    },
    "invitado1": {
        "password": "inv123",
        "role": "ROLE_GUEST"
    },
    "soporte1": {
        "password": "sop123", 
        "role": "ROLE_SOPORTE"
    },
    "iot1": {
        "password": "iot123",
        "role": "ROLE_IOT"
    }
}

# ==================================================
# CONFIGURACIÓN DE INTEGRACIÓN
# ==================================================

# URLs de servicios externos
EXTERNAL_SERVICES = {
    "success_redirect": "http://www.google.com",
    "failure_redirect": "http://10.0.0.1:5000",
    "support_url": "http://help.universidad.edu",
    "terms_of_service": "http://www.universidad.edu/terms"
}

# APIs externas (si es necesario)
EXTERNAL_APIS = {
    "user_directory": {
        "enabled": False,
        "url": "https://api.universidad.edu/users",
        "api_key": "",
        "timeout": 10
    },
    
    "notification_service": {
        "enabled": False,
        "url": "https://notifications.universidad.edu/send", 
        "api_key": "",
        "timeout": 5
    }
}

# ==================================================
# CONFIGURACIÓN DE BACKUP Y MANTENIMIENTO
# ==================================================

# Configuración de backup
BACKUP_CONFIG = {
    "enabled": True,
    "backup_dir": "/var/backups/captive_portal_sdn",
    "retention_days": 30,
    "backup_schedule": "0 2 * * *",  # Cron: 2 AM diario
    "include_logs": True,
    "include_database": True
}

# Configuración de mantenimiento
MAINTENANCE = {
    "auto_restart_enabled": True,
    "restart_schedule": "0 4 * * 0",  # Cron: 4 AM domingos
    "log_rotation_enabled": True,
    "database_cleanup_enabled": True,
    "session_cleanup_interval": 3600  # 1 hora
}
