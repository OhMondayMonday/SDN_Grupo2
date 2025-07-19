import logging
import time
import json
import requests
import hashlib
from flask import Flask, request, jsonify
from datetime import datetime
import threading

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

FLOODLIGHT_URL = "http://192.168.200.200:8080"
CONTROLLER_IP = "192.168.201.200"
CONTROLLER_PORT = 8081

SWITCHES = [
    "00:00:72:e0:80:7e:85:4c",
    "00:00:f2:20:f9:45:4c:4e",
    "00:00:1a:74:72:3f:ef:44",
    "00:00:aa:51:aa:ba:72:41",
    "00:00:5e:c7:6e:c6:11:4c"
]

def generate_unique_cookie(flow_name, switch):
    """Generar cookie única basada en el hash del nombre del flujo + switch"""
    # Combinar nombre del flujo + switch para garantizar unicidad por switch
    unique_string = f"{flow_name}_{switch}"
    hash_obj = hashlib.md5(unique_string.encode())
    # Usar los primeros 6 caracteres del hash para asegurar que sea menor a 2^31-1
    cookie_hex = hash_obj.hexdigest()[:6]
    # Convertir a número decimal para Floodlight (máximo ~16 millones)
    cookie_int = int(cookie_hex, 16)
    # Asegurar que esté dentro del rango de int32 positivo de Java
    cookie_final = str(cookie_int % 2147483647)
    
    # Debug: mostrar qué cookie se genera para cada combinación
    print(f"🔍 Cookie generada para '{flow_name}' en switch '{switch[-8:]}': {cookie_final}")
    
    return cookie_final

def generate_flows_for_role(role, mac_address, switch):
    """Generar flujos específicos según el rol del usuario"""
    flows = []
    # Obtener los últimos 4 caracteres del switch para el nombre
    switch_suffix = switch[-4:]
    
    if role == 'ROLE_ADMIN':
        # Permite todo el tráfico IPv4 desde la MAC del usuario
        flow_name = f"admin_full_access_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "priority": "1000",
            "actions": "output=normal",
            "active": "true"
        })
        
    elif role == 'ROLE_PROFESOR':
        # HTTP
        flow_name = f"profesor_http_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ip_proto": "6",
            "tp_dst": "80",
            "priority": "800",
            "actions": "output=normal",
            "active": "true"
        })
        # HTTPS
        flow_name = f"profesor_https_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ip_proto": "6",
            "tp_dst": "443",
            "priority": "800",
            "actions": "output=normal",
            "active": "true"
        })
        # DNS UDP
        flow_name = f"profesor_dns_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ip_proto": "17",
            "tp_dst": "53",
            "priority": "800",
            "actions": "output=normal",
            "active": "true"
        })
        # SSH
        flow_name = f"profesor_ssh_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ip_proto": "6",
            "tp_dst": "22",
            "priority": "800",
            "actions": "output=normal",
            "active": "true"
        })
        
    elif role == 'ROLE_ESTUDIANTE':
        # Portal específico: acceso a 10.0.0.1:8080 con VLAN 20
        flow_name = f"estudiante_portal_8080_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ipv4_dst": "10.0.0.1",
            "ip_proto": "6",
            "tp_dst": "8080",
            "priority": "600",
            "actions": "output=normal",
            "active": "true",
        })
        
    elif role == 'ROLE_GUEST':
        # Acceso web básico
        flow_name = f"guest_http_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ip_proto": "6",
            "tp_dst": "80",
            "priority": "400",
            "actions": "output=normal",
            "active": "true"
        })
        flow_name = f"guest_https_{mac_address.replace(':', '')}_{switch_suffix}"
        flows.append({
            "switch": switch,
            "name": flow_name,
            "cookie": generate_unique_cookie(flow_name, switch),
            "eth_type": "0x0800",
            "eth_src": mac_address,
            "ip_proto": "6",
            "tp_dst": "443",
            "priority": "400",
            "actions": "output=normal",
            "active": "true"
        })
    
    return flows

app = Flask(__name__)

active_users = {}

@app.route('/api/user_authenticated', methods=['POST'])
def user_authenticated():
    data = request.json
    username = data.get('username')
    role = data.get('role')
    mac_address = data.get('mac_address')
    client_ip = data.get('client_ip')
    logger.info(f"Recibida autenticación: {username} ({role}) {mac_address}")

    # Generar flujos según rol usando la nueva función
    flows = []
    for switch in SWITCHES:
        role_flows = generate_flows_for_role(role, mac_address, switch)
        flows.extend(role_flows)

    # Instalar flujos en Floodlight (formato simple compatible)
    FLOODLIGHT_URL = "http://192.168.200.200:8080/wm/staticflowpusher/json"
    installed_count = 0
    for flow in flows:
        print("Enviando flujo:", json.dumps(flow, indent=2))
        try:
            response = requests.post(
                FLOODLIGHT_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(flow),
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Flujo instalado: {flow['name']}")
                logger.info(f"✅ Flujo instalado: {flow['name']} en {flow['switch']}")
                installed_count += 1
            else:
                print(f"❌ Error instalando {flow['name']}: HTTP {response.status_code} - {response.text}")
                logger.error(f"❌ Error instalando {flow['name']}: HTTP {response.status_code} - {response.text}")
            # Pequeño delay entre instalaciones para evitar problemas de concurrencia
            time.sleep(0.1)
        except Exception as e:
            print(f"❌ Excepción instalando {flow['name']}: {e}")
            logger.error(f"❌ Excepción instalando {flow['name']}: {e}")
    
    logger.info(f"Instalados {installed_count}/{len(flows)} flujos correctamente")

    # Guardar usuario activo
    active_users[client_ip] = {
        "username": username,
        "role": role,
        "mac_address": mac_address,
        "authenticated_at": time.time()
    }
    return jsonify({"status": "success", "flows_installed": installed_count})

@app.route('/api/user_logout', methods=['POST'])
def user_logout():
    data = request.json
    client_ip = data.get('client_ip')
    user = active_users.get(client_ip)
    if not user:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    
    # Solo remover usuario de la lista activa, sin eliminar flujos por ahora
    username = user.get('username', 'unknown')
    logger.info(f"Usuario {username} deslogueado - flujos mantenidos")
    
    del active_users[client_ip]
    return jsonify({"status": "success", "message": f"Usuario {username} deslogueado"})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "active_users": list(active_users.values()),
        "total_users": len(active_users)
    })

@app.route('/health', methods=['GET'])
def health():
    try:
        r = requests.get(f"{FLOODLIGHT_URL}/wm/core/controller/switches/json", timeout=3)
        connected = r.status_code == 200
    except Exception:
        connected = False
    return jsonify({"status": "healthy", "floodlight_connected": connected, "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    logger.info("=== Nuevo Controlador SDN para Portal Cautivo ===")
    app.run(host=CONTROLLER_IP, port=CONTROLLER_PORT, debug=False, threaded=False)
