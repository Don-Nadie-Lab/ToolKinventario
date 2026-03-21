# 🔧 ToolKinventario

**Sistema de Gestión de Inventario para Windows**

[![Windows](https://img.shields.io/badge/Windows-7/8/10/11-blue.svg)](https://microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)](https://sqlite.org)

---

## 🚀 Instalación Rápida

1. **Descargue** el proyecto desde GitHub
2. **Ejecute** `preparar_entorno.bat` para instalar Python y dependencias
3. **Ejecute** `crear_accesos_directos.bat` para crear iconos en el escritorio
4. **Inicie** el sistema con el icono de ToolKinventario

## 🎯 Acceso

- **URL**: `http://127.0.0.1:5050` (desde el mismo equipo)
- **Usuario**: `admin`
- **Contraseña**: `admin123`

> ⚠️ Cambie la contraseña del administrador después del primer inicio de sesión.

---

## 👥 Niveles de Usuario

ToolKinventario cuenta con **3 niveles de acceso** para mayor seguridad:

| Nivel | Rol | Permisos |
|:-----:|:---:|:---------|
| 👑 | **Administrador** | Control total: crear, editar, eliminar, gestionar usuarios, respaldos, mantenimiento |
| 👤 | **Usuario** | Operador estándar: crear/editar productos, registrar movimientos |
| 📦 | **Maestro Carga** | Solo cargas masivas: importar productos desde CSV |

---

## 📦 Funcionalidades

### 📊 Dashboard
Panel principal con resumen del sistema:
- Estadísticas en tiempo real
- Valor total del inventario
- Alertas de stock bajo
- Productos más movidos
- Últimos movimientos

### 📦 Gestión de Productos
- ✅ Crear, editar y eliminar productos
- 🏷️ Códigos de producto únicos
- 🗂️ Categorización por categorías
- 📍 Control de ubicación (estante, anaquel)
- 📈 Control de stock mínimo (alertas)
- 💰 Precios de venta y costo
- 📅 Fecha de vencimiento
- 📋 Historial completo de movimientos

### 🔧 Gestión de Repuestos
- ✨ Cálculo automático de precio de venta
- 💵 Margen de ganancia configurable (%)
- 📦 Dos tipos de posesión:
  - **Propio (Reventa)**
  - **Consignación**
- 🔗 Vinculación con proveedores

### 📋 Movimientos de Inventario
Tipos de movimiento:
- ➕ **Entrada** - Compra, donación, producción
- ➖ **Salida** - Venta, mermas, consumo
- 🔄 **Ajuste** - Corrección manual de stock
- 📥 **Inicial** - Carga inicial de productos

Características:
- 📸 Escaner de códigos de barras (cámara)
- 📝 Referencias (facturas, órdenes)
- 🕐 Historial completo con trazabilidad
- 🔍 Filtros por fecha, producto, tipo

### 🏷️ Categorías
- ➕ Crear categorías para organizar productos
- ✏️ Editar y organizar
- 🔍 Filtrar productos por categoría

### 👥 Proveedores
- 📋 Gestión de datos de contacto
- 📞 Teléfono, email, dirección
- 🔗 Vinculación con productos y repuestos

### 📁 Importar / Exportar
- ⬆️ **Importar** productos desde archivo CSV
- ⬇️ **Exportar** todos los productos a CSV
- 🔄 Actualización masiva de inventario

### 💾 Respaldos (Solo Admin)
- 💾 Crear respaldos manuales
- 📥 Descargar respaldos
- 🗑️ Eliminar respaldos antiguos
- 🔧 Mantenimiento de base de datos

---

## 🖥️ Gestión del Servidor

### Scripts Disponibles

| Script | Función |
|--------|---------|
| `preparar_entorno.bat` | Instala Python y dependencias |
| `crear_accesos_directos.bat` | Crea iconos en escritorio |
| `iniciar_servidor.bat` | Inicia el servidor |
| `apagar_servidor.ps1` | Detiene el servidor |

### Acceso desde otros equipos

1. Encuentre la IP del servidor:
   ```cmd
   ipconfig
   ```
2. Acceda desde cualquier navegador:
   ```
   http://[IP_DEL_SERVIDOR]:5050
   ```

---

## 🔒 Seguridad

- 🔐 Autenticación con contraseña hasheada (bcrypt)
- 👥 Sistema de roles y permisos
- 📝 Log de auditoría de acciones
- 🚫 Protección anti-fraude (Maestro Carga)
- 🔑 Preguntas de seguridad para recuperación

---

## 🛠️ Requisitos

- **Windows** 7, 8, 10 o 11
- **Python** 3.11 o superior (se instala automáticamente)
- **Conexión a internet** (solo para instalación)

---

## 📁 Estructura del Proyecto

```
ToolKinventario/
├── app/
│   ├── __init__.py      # Configuración de la app
│   ├── auth.py          # Autenticación y usuarios
│   ├── models.py        # Modelos de datos
│   ├── views.py         # Controladores
│   └── utils.py         # Utilidades
├── templates/           # Vistas HTML
├── static/              # CSS, JS, imágenes
├── database/            # Base de datos SQLite
├── backups/            # Respaldos
├── logs/               # Logs del sistema
├── run.py              # Punto de entrada
└── requirements.txt    # Dependencias Python
```

---

## 📖 Documentación

- **Manual de Usuario**: [MANUAL_USUARIO.md](MANUAL_USUARIO.md)
- **Soporte**: [GitHub Issues](https://github.com/Don-Nadie-Lab/ToolKinventario/issues)

---

## 🆘 Solución de Problemas

### Error de NumPy
```cmd
pip uninstall numpy opencv-python -y
pip install numpy==1.26.4 opencv-python==4.8.1.78
```

### Puerto en uso
Espere unos segundos y reintente, o detenga el servidor con `apagar_servidor.ps1`.

### No puedo eliminar un producto
Verifique que no tenga movimientos asociados.

---

## 🤝 Contribuir

1. Fork el proyecto
2. Cree una rama para su feature
3. Commit sus cambios
4. Push a la rama
5. Abra un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

**Desarrollado con ❤️ por Don Nadie Lab**

⭐ ¿Te gusta ToolKinventario? ¡Dale una estrella al repositorio!
