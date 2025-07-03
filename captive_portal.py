#!/usr/bin/env python3
"""
Portal Cautivo SDN con autenticación RADIUS
Arquitectura: Portal (h1) → FreeRADIUS (localhost) → Controlador SDN
Autor: SDN_Grupo2
Fecha: Julio 2025
"""

import logging
import time
import subprocess
import requests
import json
import re
from flask import Flask, render_template, request, redirect, session, jsonify
from functools import wraps

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CaptivePortalController:
    def __init__(self):
        # Configuración RADIUS
        self.RADIUS_SERVER = "localhost"  # FreeRADIUS en el mismo servidor
        self.RADIUS_SECRET = "radius_secret_sdn"
        self.RADIUS_PORT = 1812
        
        # Configuración del controlador SDN
        self.CONTROLLER_URL = "http://192.168.200.200:8081"  # IP del controlador
        
        # Configuración del portal
        self.PORTAL_IP = "10.0.0.1"
        self.PORTAL_PORT = 5000
        self.SUCCESS_REDIRECT = "http://www.google.com"
        
        # Almacenamiento de sesiones
        self.authenticated_devices = {}
        
        # Mapeo de roles a configuraciones
        self.ROLE_CONFIG = {
            'ROLE_ADMIN': {
                'vlan': 10,
                'priority': 1000,
                'internet_access': True,
                'internal_access': True,
                'description': 'Administrador con acceso completo'
            },
            'ROLE_PROFESOR': {
                'vlan': 15,
                'priority': 800,
                'internet_access': True,
                'internal_access': True,
                'description': 'Profesor con acceso extendido'
            },
            'ROLE_ESTUDIANTE': {
                'vlan': 20,
                'priority': 600,
                'internet_access': True,
                'internal_access': False,
                'description': 'Estudiante con acceso web básico'
            },
            'ROLE_GUEST': {
                'vlan': 30,
                'priority': 400,
                'internet_access': True,
                'internal_access': False,
                'description': 'Invitado con acceso limitado'
            },
            'ROLE_IOT': {
                'vlan': 40,
                'priority': 200,
                'internet_access': False,
                'internal_access': True,
                'description': 'Dispositivo IoT restringido'
            },
            'ROLE_SOPORTE': {
                'vlan': 50,
                'priority': 700,
                'internet_access': True,
                'internal_access': True,
                'description': 'Soporte técnico'
            }
        }
    
    def get_client_mac(self, client_ip):
        """Obtener MAC address del cliente por IP"""
        try:
            result = subprocess.run(
                ['arp', '-n', client_ip],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if client_ip in line:
                        mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                        if mac_match:
                            return mac_match.group(0)
            
            # Si no se encuentra, generar MAC basada en IP
            ip_parts = client_ip.split('.')
            return f"00:00:00:00:{int(ip_parts[-2]):02x}:{int(ip_parts[-1]):02x}"
            
        except Exception as e:
            logger.error(f"Error getting MAC for {client_ip}: {e}")
            return f"00:00:00:00:00:00"
    
    def radius_authenticate(self, username, password, client_ip, mac_address):
        """Autenticar usuario contra FreeRADIUS"""
        try:
            cmd = [
                'radtest', username, password,
                self.RADIUS_SERVER, str(self.RADIUS_PORT),
                self.RADIUS_SECRET
            ]
            
            result = subprocess.run(cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=10)
            
            if result.returncode == 0 and "Access-Accept" in result.stdout:
                # Parsear respuesta RADIUS
                attributes = self.parse_radius_response(result.stdout)
                
                return {
                    'authenticated': True,
                    'role': attributes.get('role', 'ROLE_GUEST'),
                    'vlan_id': attributes.get('vlan_id', '30'),
                    'session_timeout': attributes.get('session_timeout', 3600),
                    'filter_id': attributes.get('filter_id', 'default'),
                    'attributes': attributes
                }
            else:
                logger.warning(f"RADIUS authentication failed for {username}: {result.stdout}")
                return {'authenticated': False, 'error': 'Invalid credentials'}
                
        except subprocess.TimeoutExpired:
            logger.error("RADIUS authentication timeout")
            return {'authenticated': False, 'error': 'Authentication timeout'}
        except Exception as e:
            logger.error(f"RADIUS authentication error: {e}")
            return {'authenticated': False, 'error': str(e)}
    
    def parse_radius_response(self, radius_output):
        """Parsear respuesta de FreeRADIUS para extraer atributos"""
        attributes = {}
        
        try:
            # Extraer Class (rol) - formato hex
            class_match = re.search(r'Class = (0x[0-9a-fA-F]+)', radius_output)
            if class_match:
                role_hex = class_match.group(1).replace('0x', '')
                try:
                    role = bytes.fromhex(role_hex).decode('utf-8')
                    attributes['role'] = role
                except:
                    attributes['role'] = 'ROLE_GUEST'
            
            # Extraer VLAN ID
            vlan_match = re.search(r'Tunnel-Private-Group-Id.*?= "?(\d+)"?', radius_output)
            if vlan_match:
                attributes['vlan_id'] = vlan_match.group(1)
            
            # Extraer Session-Timeout
            timeout_match = re.search(r'Session-Timeout = (\d+)', radius_output)
            if timeout_match:
                attributes['session_timeout'] = int(timeout_match.group(1))
            
            # Extraer Filter-Id
            filter_match = re.search(r'Filter-Id = "([^"]+)"', radius_output)
            if filter_match:
                attributes['filter_id'] = filter_match.group(1)
                
        except Exception as e:
            logger.error(f"Error parsing RADIUS response: {e}")
        
        return attributes
    
    def notify_controller(self, user_data):
        """Notificar al controlador SDN sobre usuario autenticado"""
        try:
            controller_data = {
                'action': 'user_authenticated',
                'timestamp': time.time(),
                'username': user_data['username'],
                'client_ip': user_data['client_ip'],
                'mac_address': user_data['mac_address'],
                'role': user_data['role'],
                'vlan_id': user_data['vlan_id'],
                'session_timeout': user_data['session_timeout'],
                'filter_id': user_data['filter_id'],
                'role_config': self.ROLE_CONFIG.get(user_data['role'], {})
            }
            
            logger.info(f"Notifying controller for user {user_data['username']} with role {user_data['role']}")
            
            response = requests.post(
                f"{self.CONTROLLER_URL}/api/user_authenticated",
                json=controller_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Controller responded: {result}")
                return True
            else:
                logger.error(f"Controller error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error notifying controller: {e}")
            # Permitir acceso aunque el controlador falle (modo degradado)
            logger.warning("Allowing access in degraded mode (controller unavailable)")
            return True
        except Exception as e:
            logger.error(f"Unexpected error notifying controller: {e}")
            return True
    
    def notify_controller_logout(self, user_data):
        """Notificar al controlador sobre logout de usuario"""
        try:
            controller_data = {
                'action': 'user_logout',
                'timestamp': time.time(),
                'username': user_data['username'],
                'client_ip': user_data['client_ip'],
                'mac_address': user_data['mac_address'],
                'role': user_data['role']
            }
            
            response = requests.post(
                f"{self.CONTROLLER_URL}/api/user_logout",
                json=controller_data,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error notifying controller logout: {e}")
            return True

# Inicializar Flask app
app = Flask(__name__)
app.secret_key = 'sdn_captive_portal_secret_key_2025'

# Instancia global del controlador
portal = CaptivePortalController()

def is_authenticated():
    """Verificar si el cliente está autenticado"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    return client_ip in portal.authenticated_devices and session.get('authenticated', False)

@app.route('/')
def index():
    """Página principal del portal cautivo"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if is_authenticated():
        # Usuario ya autenticado, redirigir a internet
        return redirect(portal.SUCCESS_REDIRECT)
    
    # Mostrar página de login
    return render_template('login.html', client_ip=client_ip)

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Procesar autenticación de usuario"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if not username or not password:
        return render_template('login.html', 
                             error="Usuario y contraseña son requeridos",
                             client_ip=client_ip)
    
    # Obtener MAC address
    mac_address = portal.get_client_mac(client_ip)
    
    # Autenticar contra RADIUS
    auth_result = portal.radius_authenticate(username, password, client_ip, mac_address)
    
    if auth_result['authenticated']:
        # Crear sesión de usuario
        session_data = {
            'username': username,
            'client_ip': client_ip,
            'mac_address': mac_address,
            'role': auth_result['role'],
            'vlan_id': auth_result['vlan_id'],
            'authenticated_at': time.time(),
            'expires_at': time.time() + auth_result['session_timeout'],
            'session_timeout': auth_result['session_timeout'],
            'filter_id': auth_result['filter_id'],
            'attributes': auth_result['attributes']
        }
        
        # Notificar al controlador SDN
        controller_success = portal.notify_controller(session_data)
        
        if controller_success:
            # Guardar sesión
            portal.authenticated_devices[client_ip] = session_data
            session['authenticated'] = True
            session['username'] = username
            session['role'] = auth_result['role']
            
            logger.info(f"User {username} authenticated successfully with role {auth_result['role']}")
            
            # Mostrar página de éxito
            return render_template('success.html',
                                 username=username,
                                 role=auth_result['role'],
                                 vlan_id=auth_result['vlan_id'],
                                 session_timeout=auth_result['session_timeout'],
                                 client_ip=client_ip,
                                 mac_address=mac_address)
        else:
            logger.error(f"Failed to configure network access for {username}")
            return render_template('login.html',
                                 error="Error configurando acceso de red",
                                 client_ip=client_ip)
    else:
        logger.warning(f"Failed authentication for {username} from {client_ip}")
        return render_template('login.html',
                             error="Credenciales inválidas",
                             client_ip=client_ip)

@app.route('/logout')
def logout():
    """Cerrar sesión de usuario"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if client_ip in portal.authenticated_devices:
        user_data = portal.authenticated_devices[client_ip]
        
        # Notificar al controlador
        portal.notify_controller_logout(user_data)
        
        # Limpiar sesión
        del portal.authenticated_devices[client_ip]
        session.clear()
        
        logger.info(f"User {user_data['username']} logged out")
    
    return render_template('logout.html')

@app.route('/status')
def status():
    """API para verificar estado de autenticación"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if client_ip in portal.authenticated_devices:
        user_data = portal.authenticated_devices[client_ip]
        current_time = time.time()
        
        # Verificar si la sesión ha expirado
        if current_time > user_data['expires_at']:
            del portal.authenticated_devices[client_ip]
            session.clear()
            return jsonify({
                'authenticated': False,
                'message': 'Session expired'
            })
        
        return jsonify({
            'authenticated': True,
            'username': user_data['username'],
            'role': user_data['role'],
            'vlan_id': user_data['vlan_id'],
            'time_remaining': int(user_data['expires_at'] - current_time),
            'session_info': {
                'authenticated_at': user_data['authenticated_at'],
                'expires_at': user_data['expires_at']
            }
        })
    else:
        return jsonify({
            'authenticated': False,
            'message': 'No authenticated session'
        })

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas del portal"""
    current_time = time.time()
    active_users = 0
    
    # Contar usuarios activos (no expirados)
    for client_ip, user_data in list(portal.authenticated_devices.items()):
        if current_time <= user_data['expires_at']:
            active_users += 1
        else:
            # Limpiar sesiones expiradas
            del portal.authenticated_devices[client_ip]
    
    return jsonify({
        'active_users': active_users,
        'total_devices': len(portal.authenticated_devices),
        'portal_uptime': int(current_time - app.start_time) if hasattr(app, 'start_time') else 0,
        'roles_distribution': {
            role: len([u for u in portal.authenticated_devices.values() if u['role'] == role])
            for role in portal.ROLE_CONFIG.keys()
        }
    })

@app.route('/<path:path>')
def catch_all(path):
    """Capturar todo el tráfico HTTP y redirigir al portal"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if is_authenticated():
        # Usuario autenticado, permitir acceso
        original_url = request.url
        return redirect(original_url.replace(request.host, 'www.google.com', 1))
    
    # Usuario no autenticado, redirigir al portal
    return redirect('/')

if __name__ == '__main__':
    app.start_time = time.time()
    
    logger.info("=== Portal Cautivo SDN ===")
    logger.info(f"RADIUS Server: {portal.RADIUS_SERVER}:{portal.RADIUS_PORT}")
    logger.info(f"Controller URL: {portal.CONTROLLER_URL}")
    logger.info(f"Portal URL: http://{portal.PORTAL_IP}:{portal.PORTAL_PORT}")
    logger.info("Starting Captive Portal...")
    
    app.run(
        host=portal.PORTAL_IP,
        port=portal.PORTAL_PORT,
        debug=False,
        threaded=True
    )
