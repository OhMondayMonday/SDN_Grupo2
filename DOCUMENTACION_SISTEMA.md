# 📋 Documentación Completa - Sistema RADIUS y Portal Cautivo SDN

**Proyecto:** Portal Cautivo con Autenticación RADIUS para Redes SDN  
**Fecha:** Julio 2025  
**Servidor:** h1 (10.0.0.1)

---

## 🔑 Credenciales del Sistema

### **Base de Datos MySQL**
| Servicio | Usuario | Contraseña | Base de Datos | Puerto |
|----------|---------|------------|---------------|--------|
| **MySQL Root** | `root` | `root123` | - | 3306 |
| **MySQL RADIUS** | `radius` | `radius` | `radius` | 3306 |

### **FreeRADIUS**
| Parámetro | Valor |
|-----------|-------|
| **RADIUS Secret** | `radius_secret_sdn` |
| **Servidor** | `localhost` (desde h1) |
| **Puerto Auth** | `1812` |
| **Puerto Acct** | `1813` |

### **Portal Cautivo**
| Parámetro | Valor |
|-----------|-------|
| **IP Portal** | `10.0.0.1` |
| **Puerto** | `80` |
| **RADIUS Server** | `localhost` |

---

## 👥 Usuarios Configurados por Rol

### **👑 ADMINISTRADORES (VLAN 10)**
| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `admin` | `admin123` | Administrador principal |
| `superadmin` | `super123` | Super administrador |

**Configuración:**
- 🌐 **VLAN:** 10
- ⏱️ **Sesión:** 8 horas (28800 seg)
- 🔒 **Rol:** `ROLE_ADMIN`
- 🛡️ **Filtro:** `admin_full_access`
- ✅ **Internet:** Acceso completo
- ✅ **Red Interna:** Acceso completo
- 🎯 **Prioridad:** 1000

---

### **👨‍🏫 PROFESORES (VLAN 15)**
| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `profesor1` | `prof123` | Profesor 1 |
| `profesor2` | `prof456` | Profesor 2 |
| `docente` | `doc123` | Docente general |

**Configuración:**
- 🌐 **VLAN:** 15
- ⏱️ **Sesión:** 4 horas (14400 seg)
- 🔒 **Rol:** `ROLE_PROFESOR`
- 🛡️ **Filtro:** `profesor_extended_access`
- ✅ **Internet:** Acceso completo
- ✅ **Red Interna:** Acceso extendido
- 🎯 **Prioridad:** 800

---

### **👤 ESTUDIANTES (VLAN 20)**
| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `estudiante1` | `est123` | Estudiante 1 |
| `estudiante2` | `est456` | Estudiante 2 |
| `alumno1` | `alu123` | Alumno 1 |
| `user1` | `pass123` | Usuario de prueba |

**Configuración:**
- 🌐 **VLAN:** 20
- ⏱️ **Sesión:** 2 horas (7200 seg)
- 🔒 **Rol:** `ROLE_ESTUDIANTE`
- 🛡️ **Filtro:** `estudiante_web_access`
- ✅ **Internet:** Web básico (HTTP/HTTPS)
- ❌ **Red Interna:** Sin acceso
- 🎯 **Prioridad:** 600

---

### **🏠 INVITADOS (VLAN 30)**
| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `guest1` | `guest123` | Invitado 1 |
| `visitante` | `visit123` | Visitante |
| `invitado` | `inv123` | Invitado general |

**Configuración:**
- 🌐 **VLAN:** 30
- ⏱️ **Sesión:** 1 hora (3600 seg)
- 🔒 **Rol:** `ROLE_GUEST`
- 🛡️ **Filtro:** `guest_limited_web`
- ✅ **Internet:** Web limitado
- ❌ **Red Interna:** Sin acceso
- 🎯 **Prioridad:** 400

---

### **🤖 DISPOSITIVOS IoT (VLAN 40)**
| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `iot_sensor1` | `iot123` | Sensor IoT 1 |
| `iot_camera1` | `cam123` | Cámara IoT 1 |
| `iot_device` | `device123` | Dispositivo IoT general |

**Configuración:**
- 🌐 **VLAN:** 40
- ⏱️ **Sesión:** 24 horas (86400 seg)
- 🔒 **Rol:** `ROLE_IOT`
- 🛡️ **Filtro:** `iot_restricted_access`
- ❌ **Internet:** Sin acceso
- ✅ **Red Interna:** Solo servidor IoT
- 🎯 **Prioridad:** 200

---

### **🔧 SOPORTE TÉCNICO (VLAN 50)**
| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `soporte1` | `support123` | Soporte técnico 1 |
| `tecnico` | `tech123` | Técnico general |

**Configuración:**
- 🌐 **VLAN:** 50
- ⏱️ **Sesión:** 3 horas (10800 seg)
- 🔒 **Rol:** `ROLE_SOPORTE`
- 🛡️ **Filtro:** `soporte_network_access`
- ✅ **Internet:** Acceso completo
- ✅ **Red Interna:** Diagnóstico y monitoreo
- 🎯 **Prioridad:** 700

---

## 🌐 Tabla Resumen de VLANs

| VLAN ID | Rol | Usuarios | Sesión | Acceso Internet | Acceso Interno | Prioridad |
|---------|-----|----------|--------|-----------------|----------------|-----------|
| **10** | 👑 Admin | 2 | 8h | ✅ Completo | ✅ Completo | 1000 |
| **15** | 👨‍🏫 Profesor | 3 | 4h | ✅ Completo | ✅ Extendido | 800 |
| **20** | 👤 Estudiante | 4 | 2h | ✅ Web básico | ❌ Sin acceso | 600 |
| **30** | 🏠 Invitado | 3 | 1h | ✅ Web limitado | ❌ Sin acceso | 400 |
| **40** | 🤖 IoT | 3 | 24h | ❌ Sin acceso | ✅ Restringido | 200 |
| **50** | 🔧 Soporte | 2 | 3h | ✅ Completo | ✅ Diagnóstico | 700 |

---

## 🗄️ Estructura de Base de Datos

### **Tablas Principales**
```sql
-- Tabla de usuarios y contraseñas
radcheck (username, attribute, op, value)

-- Tabla de respuestas por usuario
radreply (username, attribute, op, value)

-- Tabla de configuración de grupos
radgroupcheck (groupname, attribute, op, value)

-- Tabla de respuestas por grupo
radgroupreply (groupname, attribute, op, value)

-- Tabla de membresía usuario-grupo
radusergroup (username, groupname, priority)
```

### **Grupos Configurados**
- `admin_group` → Administradores
- `profesor_group` → Profesores y docentes
- `estudiante_group` → Estudiantes y alumnos
- `guest_group` → Invitados y visitantes
- `iot_group` → Dispositivos IoT
- `soporte_group` → Personal de soporte

---

## 🧪 Comandos de Prueba

### **Conectar a MySQL**
```bash
# Como root
mysql -u root -proot123

# Como usuario radius
mysql -u radius -pradius radius
```

### **Probar FreeRADIUS**
```bash
# Usuario válido (debe devolver Access-Accept)
radtest user1 pass123 localhost 1812 radius_secret_sdn

# Usuario con contraseña incorrecta (debe devolver Access-Reject)
radtest user1 password_incorrecta localhost 1812 radius_secret_sdn

# Usuario inexistente (debe devolver Access-Reject)
radtest usuario_falso cualquier_password localhost 1812 radius_secret_sdn
```

### **Probar Diferentes Roles**
```bash
# Administrador
radtest admin admin123 localhost 1812 radius_secret_sdn

# Profesor  
radtest profesor1 prof123 localhost 1812 radius_secret_sdn

# Estudiante
radtest estudiante1 est123 localhost 1812 radius_secret_sdn

# Invitado
radtest guest1 guest123 localhost 1812 radius_secret_sdn

# IoT
radtest iot_sensor1 iot123 localhost 1812 radius_secret_sdn

# Soporte
radtest soporte1 support123 localhost 1812 radius_secret_sdn
```

---

## 📊 Respuesta RADIUS Esperada

### **Ejemplo: Usuario Estudiante**
```
Received Access-Accept Id X from 127.0.0.1:1812
    Class = 0x524f4c455f455354554449414e5445  # ROLE_ESTUDIANTE
    Tunnel-Type:0 = VLAN
    Tunnel-Medium-Type:0 = IEEE-802
    Tunnel-Private-Group-Id:0 = "20"
    Session-Timeout = 7200
    Filter-Id = "estudiante_web_access"
```

### **Decodificación de Roles**
| Hex Value | Rol Decodificado |
|-----------|------------------|
| `0x524f4c455f41444d494e` | `ROLE_ADMIN` |
| `0x524f4c455f50524f4645534f52` | `ROLE_PROFESOR` |
| `0x524f4c455f455354554449414e5445` | `ROLE_ESTUDIANTE` |
| `0x524f4c455f4755455354` | `ROLE_GUEST` |
| `0x524f4c455f494f54` | `ROLE_IOT` |
| `0x524f4c455f534f504f525445` | `ROLE_SOPORTE` |

---

## 🔧 Configuración de Servicios

### **Estado de Servicios**
```bash
# Verificar MySQL
sudo systemctl status mysql

# Verificar FreeRADIUS
sudo systemctl status freeradius

# Verificar Portal Cautivo (cuando esté configurado)
sudo systemctl status captive-portal
```

### **Logs Importantes**
```bash
# Logs de FreeRADIUS
sudo tail -f /var/log/freeradius/radius.log

# Logs de MySQL
sudo tail -f /var/log/mysql/error.log

# Debug de FreeRADIUS
sudo freeradius -X
```

---

## 🌐 Arquitectura del Sistema

```
[Cliente] → [Portal Cautivo h1:10.0.0.1] → [FreeRADIUS] → [MySQL]
                     ↓
              [Controlador SDN] → [Floodlight] → [Switches]
```

### **Flujo de Autenticación**
1. Usuario accede a cualquier web → Redirigido al portal
2. Portal presenta formulario de login
3. Credenciales enviadas a FreeRADIUS
4. FreeRADIUS valida contra MySQL
5. Respuesta incluye rol, VLAN, timeout
6. Portal notifica al controlador SDN
7. Controlador instala flujos según rol
8. Usuario obtiene acceso limitado por rol

---

## 📝 Notas Importantes

### **Seguridad**
- ✅ Contraseñas validadas correctamente
- ✅ Usuarios inexistentes rechazados
- ✅ Roles y VLANs asignados automáticamente
- ✅ Sesiones con timeout configurado

### **Mantenimiento**
- Cambiar contraseñas regularmente
- Monitorear logs de autenticación
- Revisar usuarios activos periódicamente
- Actualizar reglas de firewall según roles

### **Backup**
```bash
# Backup de base de datos
mysqldump -u root -proot123 radius > radius_backup_$(date +%Y%m%d).sql

# Restaurar backup
mysql -u root -proot123 radius < radius_backup_YYYYMMDD.sql
```

---

**Última actualización:** Julio 1, 2025  
**Versión:** 1.0  
**Autor:** SDN_Grupo2
