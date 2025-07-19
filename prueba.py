import requests
import json

FLOODLIGHT_URL = "http://192.168.200.200:8080/wm/staticflowpusher/json"

# Ejemplo: Instalar reglas en Switch-1 (DPID: 00:00:72:e0:80:7e:85:4c)
flows = [
    {'switch': '00:00:5e:c7:6e:c6:11:4c', 'name': 'estudiante_portal_8080_fa163ed6a2a3', 'priority': '600', 'eth_src': 'fa:16:3e:d6:a2:a3', 'eth_type': '0x0800', 'active': 'true', 'ipv4_dst': '10.0.0.1', 'ip_proto': '6', 'tp_dst': '8080', 'actions': 'output=normal', 'vlan_vid': '20'}
]

print("Instalando flujos en el controlador Floodlight...")
print(json.dumps(flows, indent=4))
for flow in flows:
    print(f"Instalando flujo: {json.dumps(flow)}")
    response = requests.post(
        FLOODLIGHT_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(flow)
    )
    if response.status_code == 200:
        print(f"✅ Flujo instalado: {flow['name']}")
    else:
        print(f"❌ Error instalando {flow['name']}: {response.text}")