#!/usr/bin/env python3
"""
Controlador SDN para Portal Cautivo
Recibe notificaciones del portal y gestiona flujos SDN según roles
Arquitectura: Portal → Este Controlador → Floodlight → Switches
Autor: SDN_Grupo2
Fecha: Julio 2025
"""

import logging
import time
import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import threading

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SDNController:
    def __init__(self):
        # Configuración de Floodlight
        self.FLOODLIGHT_URL = "http://192.168.200.200:8080"  # SDN interno
        
        # Configuración del controlador
        self.CONTROLLER_IP = "0.0.0.0"  # Escuchar en todas las interfaces
        self.CONTROLLER_PORT = 8081
        
        # Almacenamiento de usuarios activos y flujos
        self.active_users = {}
        self.installed_flows = {}
        
        # Configuración de switches - BASADA EN TUS SWITCHES REALES
        self.SWITCHES = {
            # Switch 1 - IP: 192.168.200.202
            "00:00:72:e0:80:7e:85:4c": {
                "name": "Switch-1",
                "ip": "192.168.200.202",
                "ports": {
                    1: "trunk_port",
                    2: "access_port_1", 
                    3: "access_port_2",
                    4: "access_port_3"
                }
            },
            
            # Switch 2 - IP: 192.168.200.203  
            "00:00:f2:20:f9:45:4c:4e": {
                "name": "Switch-2", 
                "ip": "192.168.200.203",
                "ports": {
                    1: "trunk_port",
                    2: "access_port_1",
                    3: "access_port_2", 
                    4: "access_port_3"
                }
            },
            
            # Switch 3 - IP: 192.168.200.205
            "00:00:1a:74:72:3f:ef:44": {
                "name": "Switch-3",
                "ip": "192.168.200.205", 
                "ports": {
                    1: "trunk_port",
                    2: "access_port_1",
                    3: "access_port_2",
                    4: "access_port_3"
                }
            },
            
            # Switch 4 - IP: 192.168.200.201
            "00:00:5e:c7:6e:c6:11:4c": {
                "name": "Switch-4",
                "ip": "192.168.200.201",
                "ports": {
                    1: "trunk_port", 
                    2: "access_port_1",
                    3: "access_port_2",
                    4: "access_port_3"
                }
            },
            
            # Switch 5 - IP: 192.168.200.204
            "00:00:aa:51:aa:ba:72:41": {
                "name": "Switch-5",
                "ip": "192.168.200.204",
                "ports": {
                    1: "trunk_port",
                    2: "access_port_1", 
                    3: "access_port_2",
                    4: "access_port_3"
                }
            }
        }
        
        # Políticas de flujos por rol
        self.FLOW_POLICIES = {
            'ROLE_ADMIN': {
                'priority': 1000,
                'flows': [
                    {'name': 'admin_full_access', 'action': 'output=normal'}
                ]
            },
            'ROLE_PROFESOR': {
                'priority': 800,
                'flows': [
                    {'name': 'profesor_web_http', 'match': 'tp-dst=80', 'action': 'output=normal'},
                    {'name': 'profesor_web_https', 'match': 'tp-dst=443', 'action': 'output=normal'},
                    {'name': 'profesor_dns', 'match': 'tp-dst=53', 'action': 'output=normal'},
                    {'name': 'profesor_ssh', 'match': 'tp-dst=22', 'action': 'output=normal'}
                ]
            },
            'ROLE_ESTUDIANTE': {
                'priority': 600,
                'flows': [
                    {'name': 'estudiante_web_http', 'match': 'tp-dst=80', 'action': 'output=normal'},
                    {'name': 'estudiante_web_https', 'match': 'tp-dst=443', 'action': 'output=normal'},
                    {'name': 'estudiante_dns', 'match': 'tp-dst=53', 'action': 'output=normal'},
                    {'name': 'estudiante_block_internal', 'match': 'nw-dst=192.168.1.0/24', 'action': 'drop', 'priority': 700}
                ]
            },
            'ROLE_GUEST': {
                'priority': 400,
                'flows': [
                    {'name': 'guest_web_http', 'match': 'tp-dst=80', 'action': 'output=normal'},
                    {'name': 'guest_web_https', 'match': 'tp-dst=443', 'action': 'output=normal'},
                    {'name': 'guest_dns', 'match': 'tp-dst=53', 'action': 'output=normal'},
                    {'name': 'guest_block_private1', 'match': 'nw-dst=10.0.0.0/8', 'action': 'drop', 'priority': 500},
                    {'name': 'guest_block_private2', 'match': 'nw-dst=192.168.0.0/16', 'action': 'drop', 'priority': 500},
                    {'name': 'guest_block_private3', 'match': 'nw-dst=172.16.0.0/12', 'action': 'drop', 'priority': 500}
                ]
            },
            'ROLE_IOT': {
                'priority': 200,
                'flows': [
                    {'name': 'iot_server_only', 'match': 'nw-dst=10.0.0.100/32', 'action': 'output=normal'},
                    {'name': 'iot_deny_all', 'match': '', 'action': 'drop', 'priority': 100}
                ]
            },
            'ROLE_SOPORTE': {
                'priority': 700,
                'flows': [
                    {'name': 'soporte_full_access', 'action': 'output=normal'},
                    {'name': 'soporte_icmp', 'match': 'ip-proto=1', 'action': 'output=normal'},
                    {'name': 'soporte_ssh', 'match': 'tp-dst=22', 'action': 'output=normal'}
                ]
            }
        }
    
    def test_floodlight_connection(self):
        """Verificar conectividad con Floodlight"""
        try:
            response = requests.get(f"{self.FLOODLIGHT_URL}/wm/core/controller/switches/json", timeout=5)
            if response.status_code == 200:
                switches = response.json()
                logger.info(f"Connected to Floodlight. Found {len(switches)} switches")
                return True
            else:
                logger.error(f"Floodlight connection failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot connect to Floodlight: {e}")
            return False
    
    def generate_flows_for_user(self, user_data):
        """Generar flujos SDN específicos para un usuario según su rol"""
        role = user_data['role']
        mac_address = user_data['mac_address']
        client_ip = user_data['client_ip']
        vlan_id = user_data['vlan_id']
        
        if role not in self.FLOW_POLICIES:
            logger.warning(f"Unknown role {role}, using GUEST policy")
            role = 'ROLE_GUEST'
        
        policy = self.FLOW_POLICIES[role]
        flows = []
        
        # Generar flujos para cada switch
        for switch_dpid in self.SWITCHES.keys():
            for flow_template in policy['flows']:
                flow = {
                    "switch": switch_dpid,
                    "name": f"{flow_template['name']}_{mac_address.replace(':', '')}",
                    "priority": flow_template.get('priority', policy['priority']),
                    "src-mac": mac_address,
                    "actions": flow_template['action']
                }
                
                # Agregar criterios de match si existen
                if 'match' in flow_template and flow_template['match']:
                    match_parts = flow_template['match'].split('=')
                    if len(match_parts) == 2:
                        key, value = match_parts
                        flow[key] = value
                
                # Agregar VLAN si corresponde
                if vlan_id and vlan_id != '0':
                    flow["vlan-id"] = vlan_id
                
                flows.append(flow)
        
        return flows
    
    def install_flows_to_floodlight(self, flows):
        """Instalar flujos en Floodlight"""
        results = []
        
        for flow in flows:
            try:
                # URL para instalar flujo estático en Floodlight
                url = f"{self.FLOODLIGHT_URL}/wm/staticflowpusher/json"
                
                response = requests.post(url, json=flow, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"✅ Flujo instalado en switch {flow['switch']}: {flow['name']}")
                    results.append({"switch": flow['switch'], "status": "success"})
                else:
                    logger.error(f"❌ Error instalando flujo: {response.text}")
                    results.append({"switch": flow['switch'], "status": "error", "error": response.text})
                    
            except Exception as e:
                logger.error(f"❌ Excepción instalando flujo: {str(e)}")
                results.append({"switch": flow['switch'], "status": "exception", "error": str(e)})
        
        return results
    
    def remove_flows_from_floodlight(self, flow_names):
        """Remover flujos específicos de Floodlight"""
        removed_count = 0
        
        for flow_name in flow_names:
            try:
                # ✅ MÉTODO ALTERNATIVO: Usar DELETE con parámetros
                url = f"{self.FLOODLIGHT_URL}/wm/staticflowpusher/json"
                
                # Crear payload para remover flujo específico
                payload = {
                    "name": flow_name,
                    "switch": "all"  # O especificar switch específico
                }
                
                response = requests.delete(url, json=payload, timeout=5)
                
                if response.status_code == 200:
                    removed_count += 1
                    logger.info(f"✅ Flow removed: {flow_name}")
                else:
                    logger.error(f"❌ Failed to remove flow {flow_name}: HTTP {response.status_code}")
                    logger.debug(f"Response: {response.text}")
                    
            except Exception as e:
                logger.error(f"❌ Error removing flow {flow_name}: {e}")
    
        return removed_count
    
    def cleanup_expired_users(self):
        """Limpiar usuarios expirados y sus flujos"""
        current_time = time.time()
        expired_users = []
        
        for client_ip, user_data in self.active_users.items():
            if current_time > user_data.get('expires_at', 0):
                expired_users.append(client_ip)
        
        for client_ip in expired_users:
            user_data = self.active_users[client_ip]
            logger.info(f"Session expired for user {user_data['username']}")
            
            # Remover flujos
            if client_ip in self.installed_flows:
                flow_names = self.installed_flows[client_ip]
                self.remove_flows_from_floodlight(flow_names)
                del self.installed_flows[client_ip]
            
            # Remover usuario
            del self.active_users[client_ip]

    def generate_flows_for_role(self, role, vlan_id, client_ip, mac_address, switch_dpid, in_port):
        """Generar flujos SDN según el rol del usuario"""
        flows = []
        
        # Configuración base según rol
        role_config = {
            'ROLE_ADMIN': {
                'priority': 1000,
                'internet_access': True,
                'internal_access': True,
                'bandwidth_limit': None
            },
            'ROLE_PROFESOR': {
                'priority': 800, 
                'internet_access': True,
                'internal_access': True,
                'bandwidth_limit': "100Mbps"
            },
            'ROLE_ESTUDIANTE': {
                'priority': 600,
                'internet_access': True, 
                'internal_access': False,
                'bandwidth_limit': "50Mbps"
            },
            'ROLE_GUEST': {
                'priority': 400,
                'internet_access': True,
                'internal_access': False, 
                'bandwidth_limit': "10Mbps"
            },
            'ROLE_IOT': {
                'priority': 200,
                'internet_access': False,
                'internal_access': True,
                'bandwidth_limit': "1Mbps"
            },
            'ROLE_SOPORTE': {
                'priority': 700,
                'internet_access': True,
                'internal_access': True,
                'bandwidth_limit': "200Mbps"
            }
        }
        
        config = role_config.get(role, role_config['ROLE_GUEST'])
        
        # ✅ CORRECCIÓN: Usar self.SWITCHES en lugar de self.SWITCH_CONFIG
        for dpid in self.SWITCHES:
            # Flujo de entrada - asignar VLAN
            flow_in = {
                "switch": dpid,
                "name": f"vlan_tag_{mac_address.replace(':', '')}",
                "cookie": "0",
                "priority": str(config['priority']),
                "in_port": str(in_port) if dpid == switch_dpid else "1",
                "eth_src": mac_address,
                "eth_type": "0x0800",
                "active": "true",
                "actions": f"set_vlan_vid={vlan_id},output=flood"
            }
            
            # Flujo de salida - remover VLAN tag
            flow_out = {
                "switch": dpid,
                "name": f"vlan_untag_{mac_address.replace(':', '')}", 
                "cookie": "0",
                "priority": str(config['priority']),
                "vlan_vid": str(vlan_id),
                "eth_dst": mac_address,
                "active": "true",
                "actions": f"strip_vlan,output={in_port}" if dpid == switch_dpid else "output=1"
            }
            
            flows.extend([flow_in, flow_out])
            
            # Agregar restricciones según rol
            if not config['internet_access']:
                # Bloquear tráfico hacia internet
                block_internet = {
                    "switch": dpid,
                    "name": f"block_internet_{mac_address.replace(':', '')}",
                    "priority": str(config['priority'] + 100),
                    "eth_src": mac_address,
                    "eth_type": "0x0800", 
                    "ipv4_dst": "0.0.0.0/0",
                    "active": "true",
                    "actions": ""  # Drop
                }
                flows.append(block_internet)
        
        return flows

    def validate_switch_dpid(self, dpid):
        """Validar que el DPID existe en la configuración"""
        valid_dpids = [
            "00:00:72:e0:80:7e:85:4c",
            "00:00:f2:20:f9:45:4c:4e", 
            "00:00:1a:74:72:3f:ef:44",
            "00:00:5e:c7:6e:c6:11:4c",
            "00:00:aa:51:aa:ba:72:41"
        ]
        return dpid in valid_dpids

    def start_controller(self):
        """Iniciar el controlador SDN"""
        
        # 1. Instalar flujos de bloqueo por defecto al iniciar
        logger.info("🔒 Instalando flujos de seguridad por defecto...")
        blocked_flows = self.install_default_blocking_flows()
        logger.info(f"✅ Instalados {blocked_flows} flujos de bloqueo")
        
        # 2. Iniciar API server
        logger.info(f"🚀 Iniciando API server en {self.CONTROLLER_IP}:{self.CONTROLLER_PORT}")
        app.run(host=self.CONTROLLER_IP, port=self.CONTROLLER_PORT, debug=False)

    def user_authenticated_handler(self, user_data):
        """Cuando un usuario se autentica exitosamente"""
        
        client_ip = user_data['client_ip']
        mac_address = user_data['mac_address']
        role = user_data['role']
        vlan_id = user_data.get('vlan_id')
        
        # 1. Remover flujos de bloqueo para este usuario
        exceptions_installed = self.remove_user_blocking_flows(client_ip, mac_address)
        logger.info(f"✅ Installed {exceptions_installed} exception flows for {mac_address}")
        
        # 2. Instalar flujos según el rol
        flows = self.generate_flows_for_user(user_data)
        results = self.install_flows_to_floodlight(flows)
        
        return len([r for r in results if r.get('status') == 'success'])

    def install_default_blocking_flows(self):
        """Instalar flujos que bloquean todo excepto portal cautivo"""
        
        default_flows = []
        
        for switch_dpid in self.SWITCHES.keys():
            # 1. ✅ PERMITIR acceso al portal cautivo (puerto 5000)
            allow_portal = {
                "switch": switch_dpid,
                "name": "allow_captive_portal",
                "priority": "2000",  # Prioridad alta
                "eth_type": "0x0800",
                "ipv4_dst": "10.0.0.1",
                "ip_proto": "6",  # TCP
                "tp_dst": "5000",
                "active": "true",
                "actions": "output=normal"
            }
            
            # 2. ✅ PERMITIR DNS (necesario para resolución)
            allow_dns = {
                "switch": switch_dpid,
                "name": "allow_dns",
                "priority": "1900",
                "eth_type": "0x0800",
                "ip_proto": "17",  # UDP
                "tp_dst": "53",
                "active": "true", 
                "actions": "output=normal"
            }
            
            # 3. ✅ PERMITIR DHCP (para obtener IP)
            allow_dhcp_client = {
                "switch": switch_dpid,
                "name": "allow_dhcp_client",
                "priority": "1900",
                "eth_type": "0x0800",
                "ip_proto": "17",  # UDP
                "tp_src": "68",
                "tp_dst": "67",
                "active": "true",
                "actions": "output=normal"
            }
            
            allow_dhcp_server = {
                "switch": switch_dpid,
                "name": "allow_dhcp_server",
                "priority": "1900",
                "eth_type": "0x0800",
                "ip_proto": "17",  # UDP
                "tp_src": "67",
                "tp_dst": "68",
                "active": "true",
                "actions": "output=normal"
            }
            
            # 4. 🔄 REDIRIGIR tráfico HTTP/HTTPS al portal cautivo
            redirect_http = {
                "switch": switch_dpid,
                "name": "redirect_http_to_portal",
                "priority": "1000",
                "eth_type": "0x0800",
                "ip_proto": "6",  # TCP
                "tp_dst": "80",
                "active": "true",
                "actions": f"set_nw_dst=10.0.0.1,set_tp_dst=5000,output=normal"
            }
            
            redirect_https = {
                "switch": switch_dpid,
                "name": "redirect_https_to_portal", 
                "priority": "1000",
                "eth_type": "0x0800",
                "ip_proto": "6",  # TCP
                "tp_dst": "443",
                "active": "true",
                "actions": f"set_nw_dst=10.0.0.1,set_tp_dst=5000,output=normal"
            }
            
            # 5. 🔄 REDIRIGIR acceso a 10.0.0.1:8080 al portal
            redirect_8080 = {
                "switch": switch_dpid,
                "name": "redirect_8080_to_portal",
                "priority": "1500",  # Prioridad alta para capturar antes
                "eth_type": "0x0800",
                "ipv4_dst": "10.0.0.1",
                "ip_proto": "6",  # TCP
                "tp_dst": "8080",
                "active": "true",
                "actions": "set_tp_dst=5000,output=normal"
            }
            
            # 6. ❌ BLOQUEAR todo lo demás
            block_all = {
                "switch": switch_dpid,
                "name": "block_unauthorized",
                "priority": "100",  # Prioridad baja
                "eth_type": "0x0800",
                "active": "true",
                "actions": ""  # Drop (sin action = drop)
            }
            
            default_flows.extend([
                allow_portal, 
                allow_dns, 
                allow_dhcp_client, 
                allow_dhcp_server,
                redirect_http,
                redirect_https, 
                redirect_8080,
                block_all
            ])
        
        # Instalar flujos de bloqueo por defecto
        results = self.install_flows_to_floodlight(default_flows)
        return len([r for r in results if r.get('status') == 'success'])

    def remove_user_blocking_flows(self, client_ip, mac_address):
        """Remover flujos de bloqueo para un usuario específico autenticado"""
        
        # Crear flujos que permitan acceso completo para este usuario
        user_exception_flows = []
        
        for switch_dpid in self.SWITCHES.keys():
            # Permitir todo el tráfico de este usuario (prioridad muy alta)
            allow_user = {
                "switch": switch_dpid,
                "name": f"allow_authenticated_{mac_address.replace(':', '')}",
                "priority": "3000",  # Prioridad MUY alta
                "eth_src": mac_address,
                "active": "true",
                "actions": "output=normal"
            }
            
            user_exception_flows.append(allow_user)
        
        # Instalar excepciones para el usuario autenticado
        results = self.install_flows_to_floodlight(user_exception_flows)
        return len([r for r in results if r.get('status') == 'success'])

# Inicializar Flask app
app = Flask(__name__)

# Instancia global del controlador
controller = SDNController()

@app.route('/api/user_authenticated', methods=['POST'])
def user_authenticated():
    """API para recibir notificaciones de autenticación exitosa"""
    try:
        data = request.json
        
        if not data or 'username' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        username = data['username']
        role = data['role']
        client_ip = data['client_ip']
        mac_address = data['mac_address']
        
        logger.info(f"🔐 Processing authentication for user {username} ({role}) from {client_ip}")
        
        # Verificar conectividad con Floodlight
        floodlight_available = controller.test_floodlight_connection()
        
        if floodlight_available:
            # Configurar acceso para usuario autenticado
            flows_installed = controller.user_authenticated_handler(data)
            
            if flows_installed > 0:
                # Guardar información del usuario
                controller.active_users[client_ip] = {
                    'username': username,
                    'role': role,
                    'mac_address': mac_address,
                    'vlan_id': data.get('vlan_id'),
                    'authenticated_at': time.time(),
                    'expires_at': time.time() + data.get('session_timeout', 3600),
                    'session_timeout': data.get('session_timeout', 3600)
                }
                
                logger.info(f"✅ Successfully configured network access for user {username}")
                
                return jsonify({
                    'status': 'success',
                    'flows_installed': flows_installed,
                    'message': f'Network access configured for {username}'
                })
            else:
                logger.error(f"❌ Failed to configure flows for user {username}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to configure network flows'
                }), 500
        else:
            logger.warning(f"⚠️ Floodlight unavailable, degraded mode for {username}")
            return jsonify({
                'status': 'success',
                'degraded_mode': True,
                'message': f'Access granted in degraded mode for {username}'
            })
            
    except Exception as e:
        logger.error(f"❌ Error processing user authentication: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user_logout', methods=['POST'])
def user_logout():
    """API para recibir notificaciones de logout"""
    try:
        data = request.json
        
        if not data or 'client_ip' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        client_ip = data['client_ip']
        username = data.get('username', 'unknown')
        
        logger.info(f"Processing logout for user {username} from {client_ip}")
        
        # Remover flujos si existen
        if client_ip in controller.installed_flows:
            flow_names = controller.installed_flows[client_ip]
            removed_count = controller.remove_flows_from_floodlight(flow_names)
            del controller.installed_flows[client_ip]
            logger.info(f"Removed {removed_count} flows for user {username}")
        
        # Remover usuario activo
        if client_ip in controller.active_users:
            del controller.active_users[client_ip]
        
        return jsonify({
            'status': 'success',
            'message': f'User {username} logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Error processing user logout: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status', methods=['GET'])
def controller_status():
    """API para obtener estado del controlador"""
    controller.cleanup_expired_users()
    
    return jsonify({
        'controller_status': 'running',
        'floodlight_connected': controller.test_floodlight_connection(),
        'active_users': len(controller.active_users),
        'total_flows': sum(len(flows) for flows in controller.installed_flows.values()),
        'uptime': int(time.time() - app.start_time) if hasattr(app, 'start_time') else 0,
        'users_by_role': {
            role: len([u for u in controller.active_users.values() if u.get('role') == role])
            for role in controller.FLOW_POLICIES.keys()
        }
    })

@app.route('/api/users', methods=['GET'])
def list_active_users():
    """API para listar usuarios activos"""
    controller.cleanup_expired_users()
    
    users = []
    for client_ip, user_data in controller.active_users.items():
        users.append({
            'username': user_data['username'],
            'role': user_data['role'],
            'client_ip': client_ip,
            'mac_address': user_data.get('mac_address'),
            'vlan_id': user_data.get('vlan_id'),
            'authenticated_at': user_data['authenticated_at'],
            'expires_at': user_data['expires_at'],
            'flows_count': len(controller.installed_flows.get(client_ip, [])),
            'degraded_mode': user_data.get('degraded_mode', False)
        })
    
    return jsonify({
        'active_users': users,
        'total_count': len(users)
    })

@app.route('/api/flows', methods=['GET'])
def list_flows():
    """API para listar flujos instalados"""
    return jsonify({
        'installed_flows': controller.installed_flows,
        'total_flows': sum(len(flows) for flows in controller.installed_flows.values())
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'floodlight_status': 'connected' if controller.test_floodlight_connection() else 'disconnected'
    })

def periodic_cleanup():
    """Tarea periódica para limpiar usuarios expirados"""
    while True:
        try:
            controller.cleanup_expired_users()
            time.sleep(60)  # Ejecutar cada minuto
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
            time.sleep(60)

if __name__ == '__main__':
    app.start_time = time.time()
    
    logger.info("=== Controlador SDN para Portal Cautivo ===")
    logger.info(f"Floodlight URL: {controller.FLOODLIGHT_URL}")
    logger.info(f"Controller API: http://{controller.CONTROLLER_IP}:{controller.CONTROLLER_PORT}")
    logger.info(f"Configured switches: {list(controller.SWITCHES.keys())}")
    
    # Verificar conexión inicial con Floodlight
    if controller.test_floodlight_connection():
        logger.info("✅ Floodlight connection successful")
    else:
        logger.warning("⚠️ Floodlight not available - will run in degraded mode")
    
    # Iniciar tarea de limpieza en background
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    logger.info("Starting SDN Controller...")
    
    app.run(
        host=controller.CONTROLLER_IP,
        port=controller.CONTROLLER_PORT,
        debug=False,
        threaded=True
    )
