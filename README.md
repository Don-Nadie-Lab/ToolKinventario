# 🔧 ToolKinventario

**Sistema de Inventario Universal para Raspberry Pi**

[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Compatible-red.svg)](https://www.raspberrypi.org/)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Instalación en Una Línea

\`\`\`bash
curl -sSL https://raw.githubusercontent.com/donnadieapps/toolkinventario/main/install.sh | sudo bash
\`\`\`

## ✨ Características

- 📦 **Gestión Completa de Inventario**
- 🔐 **Sistema de Autenticación Seguro**
- 📱 **Interfaz Web Responsive**
- 🍓 **Optimizado para Raspberry Pi**
- 💾 **Base de Datos SQLite Integrada**
- 🔄 **Respaldos Automáticos**
- 📖 **Manual de Usuario Integrado**
- 🌐 **Acceso desde Red Local**

## 🎯 Acceso Rápido

Después de la instalación:

- **URL**: http://[IP_DE_TU_PI]:5000
- **Usuario**: admin
- **Contraseña**: admin123
- **Manual**: http://[IP_DE_TU_PI]:5000/manual

## 🛠️ Instalación Manual

Si prefieres instalar paso a paso:

\`\`\`bash
# 1. Clonar repositorio
git clone https://github.com/donnadieapps/toolkinventario.git
cd toolkinventario

# 2. Ejecutar instalador
sudo ./install.sh
\`\`\`

## 📋 Requisitos

- Raspberry Pi (cualquier modelo)
- Raspbian/Raspberry Pi OS
- Python 3.7+
- Conexión a internet (solo para instalación)

## 🔧 Gestión del Servicio

\`\`\`bash
# Iniciar servicio
sudo systemctl start toolkinventario

# Detener servicio
sudo systemctl stop toolkinventario

# Reiniciar servicio
sudo systemctl restart toolkinventario

# Ver estado
sudo systemctl status toolkinventario

# Ver logs en tiempo real
sudo journalctl -u toolkinventario -f
\`\`\`

## 💾 Respaldos

### Automático
- Se ejecuta diariamente a las 2:00 AM
- Mantiene los últimos 7 respaldos
- Ubicación: `/opt/toolkinventario/backups/`

### Manual
\`\`\`bash
sudo /opt/toolkinventario/backup.sh
\`\`\`

## 🌐 Acceso Remoto

Para acceder desde otros dispositivos en tu red:

1. Encuentra la IP de tu Raspberry Pi:
   \`\`\`bash
   hostname -I
   \`\`\`

2. Accede desde cualquier dispositivo:
   \`\`\`
   http://[IP_DE_TU_PI]:5000
   \`\`\`

## 📖 Funcionalidades

### Dashboard
- Resumen del inventario
- Estadísticas en tiempo real
- Productos con stock bajo
- Actividad reciente

### Productos
- Agregar/editar/eliminar productos
- Códigos de barras
- Categorías y proveedores
- Control de stock mínimo

### Movimientos
- Entradas y salidas
- Ajustes de inventario
- Historial completo
- Trazabilidad

### Categorías
- Organización de productos
- Gestión simplificada
- Filtros por categoría

## 🔒 Seguridad

- Autenticación requerida
- Sesiones seguras
- Firewall configurado automáticamente
- Acceso solo desde red local

## ⚠️ Nota sobre Producción

El mensaje "No usar en producción" se refiere al servidor de desarrollo de Flask. Para uso doméstico o pequeñas empresas en red local, es completamente seguro y funcional.

## 🆘 Solución de Problemas

### El servicio no inicia
\`\`\`bash
# Ver logs detallados
sudo journalctl -u toolkinventario -n 50

# Verificar permisos
sudo chown -R $USER:$USER /opt/toolkinventario
sudo chmod 600 /opt/toolkinventario/database
\`\`\`

### No puedo acceder desde otros dispositivos
\`\`\`bash
# Verificar firewall
sudo ufw status

# Permitir puerto 5000
sudo ufw allow 5000/tcp
\`\`\`

### Problemas de base de datos
\`\`\`bash
# Verificar base de datos
ls -la /opt/toolkinventario/database/

# Recrear base de datos
sudo systemctl stop toolkinventario
sudo rm /opt/toolkinventario/database/toolkinventario.db
sudo systemctl start toolkinventario
\`\`\`

## 📞 Soporte

- **Email**: soporte@donnadieapps.com
- **Issues**: [GitHub Issues](https://github.com/donnadieapps/toolkinventario/issues)
- **Manual**: Disponible en `/manual` dentro de la aplicación

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- Comunidad Raspberry Pi
- Desarrolladores de Flask
- Usuarios beta testers

---

**Desarrollado con ❤️ por Don Nadie Apps**

*¿Te gusta ToolKinventario? ¡Dale una ⭐ al repositorio!*
