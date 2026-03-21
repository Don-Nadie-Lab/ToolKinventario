# MANUAL DE USUARIO
## ToolKinventario - Sistema de Gestión de Inventario

---

## TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Niveles de Usuario](#niveles-de-usuario)
3. [Instalación](#instalación)
4. [Iniciar el Sistema](#iniciar-el-sistema)
5. [Iniciar/Cerrar Sesión](#inicarsesion)
6. [Dashboard](#dashboard)
7. [Gestión de Productos](#productos)
8. [Gestión de Repuestos](#repuestos)
9. [Movimientos de Inventario](#movimientos)
10. [Categorías](#categorías)
11. [Proveedores](#proveedores)
12. [Importar/Exportar Datos](#importar-exportar)
13. [Respaldos](#respaldos)
14. [Cerrar el Sistema](#cerrar-sistema)

---

## 1. INTRODUCCIÓN

**ToolKinventario** es un sistema de gestión de inventario diseñado para empresas que necesitan controlar sus productos, repuestos y movimientos de stock.

### Características principales:
- 📦 Control de productos y repuestos
- 📊 Dashboard con estadísticas en tiempo real
- 📈 Registro de movimientos (entradas/salidas)
- 🏷️ Categorización de productos
- 👥 Gestión de múltiples usuarios
- 💾 Respaldos automáticos
- 📁 Importación/Exportación CSV
- 📱 Acceso desde cualquier dispositivo en la red

---

## 2. NIVELES DE USUARIO

El sistema cuenta con **3 niveles de acceso**:

| Icono | Rol | Descripción | Permisos |
|-------|-----|-------------|----------|
| 👑 | **Administrador** | Control total del sistema | Crear, editar, eliminar todo. Gestionar usuarios, respaldos, mantenimiento |
| 👤 | **Usuario** | Operador estándar | Crear/editar productos, registrar movimientos. No puede eliminar ni acceder a respaldos |
| 📦 | **Maestro Carga** | Solo cargas masivas | Importar productos desde CSV. No puede crear/editar registros manualmente |

### Usuario por defecto:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

> ⚠️ **IMPORTANTE:** Cambie la contraseña del administrador después del primer inicio de sesión.

### Agregar nuevos usuarios (solo Administrador):
1. Vaya a **Configuración** > **Usuarios**
2. Click en **"Nuevo Usuario"**
3. Complete los datos:
   - Nombre de usuario
   - Contraseña
   - Nombre completo
   - Correo electrónico
   - Nivel de acceso (Rol)
4. Click en **Guardar**

---

## 3. INSTALACIÓN

### Requisitos:
- Windows 7/8/10/11
- Python 3.11 o superior
- Conexión a internet (solo para instalación)

### Pasos de instalación:

1. **Descargue el proyecto** desde GitHub:
   ```
   https://github.com/Don-Nadie-Lab/ToolKinventario
   ```

2. **Ejecute el script de preparación** (doble click):
   ```
   preparar_entorno.bat
   ```
   
   Este script:
   - Instala Python si no está presente
   - Instala todas las dependencias
   - Crea las carpetas necesarias

3. **Cree los accesos directos** (opcional):
   ```
   crear_accesos_directos.bat
   ```

---

## 4. INICIAR EL SISTEMA

### Método 1: Acceso directo
- Doble click en el icono **ToolKinventario** del escritorio

### Método 2: Archivo BAT
- Doble click en **iniciar_servidor.bat**

### Método 3: Comando manual
```cmd
cd ruta\del\proyecto
python run.py
```

### Acceso desde otros dispositivos:
Una vez iniciado, el servidor muestra la URL de acceso:
```
http://192.168.1.109:5050
```
Acceda desde cualquier navegador en la misma red.

---

## 5. INICIAR/CERRAR SESIÓN <a name="inicarsesion"></a>

### Iniciar sesión:
1. Ingrese su **Usuario** y **Contraseña**
2. Click en **"Iniciar Sesión"**

### Cerrar sesión:
1. Click en su **nombre de usuario** (esquina superior derecha)
2. Seleccione una opción:
   - **"Cerrar Sesión"** → Solo cierra su sesión
   - **"Apagar Sistema"** → Cierra sesión Y detiene el servidor

---

## 6. DASHBOARD

El Dashboard es la **pantalla principal** que muestra un resumen del sistema.

### Secciones del Dashboard:

| Icono | Sección | Descripción |
|-------|---------|-------------|
| 📊 | **Estadísticas** | Total de productos, categorías, movimientos |
| 💰 | **Valor del Inventario** | Valor total de productos y repuestos |
| ⚠️ | **Alertas de Stock** | Productos con stock bajo el mínimo |
| 📈 | **Productos Más Movidos** | Top 5 productos con más actividad |
| 🕐 | **Últimos Movimientos** | Registro de las últimas transacciones |

### URL de acceso:
Muestra la dirección para acceder desde otros dispositivos en la red.

---

## 7. GESTIÓN DE PRODUCTOS <a name="productos"></a>

### Acceder:
Click en **"Productos"** en el menú lateral

### Operaciones disponibles:

| Icono | Operación | Administrador | Usuario | Maestro Carga |
|-------|-----------|:-------------:|:------:|:-------------:|
| 📋 | Ver lista | ✅ | ✅ | ❌ |
| 🔍 | Buscar | ✅ | ✅ | ❌ |
| ➕ | Nuevo producto | ✅ | ✅ | ❌ |
| ✏️ | Editar producto | ✅ | ✅ | ❌ |
| 🗑️ | Eliminar producto | ✅ | ❌ | ❌ |

### Crear un nuevo producto:
1. Click en **"+ Nuevo Producto"**
2. Complete los campos:
   - **Código** ⭐ (obligatorio - único)
   - **Nombre** ⭐ (obligatorio)
   - **Descripción** (opcional)
   - **Categoría** ⭐ (obligatorio)
   - **Ubicación** (ej: "Estante A-3")
   - **Cantidad inicial** (stock actual)
   - **Precio** (precio de venta)
   - **Costo** (precio de compra)
   - **Proveedor** (opcional)
   - **Stock mínimo** (para alertas)
   - **Fecha de vencimiento** (opcional)
3. Click en **"Guardar"**

### Buscar y filtrar productos:
- **Búsqueda:** Escriba código, nombre o descripción
- **Por categoría:** Seleccione una categoría
- **Stock bajo:** Active para ver solo productos bajo mínimo

### Ver detalles de producto:
1. Click en el producto
2. Vea:
   - Información completa
   - Historial de movimientos
   - Valor del inventario

---

## 8. GESTIÓN DE REPUESTOS <a name="repuestos"></a>

### Acceder:
Click en **"Repuestos"** en el menú lateral

### Características especiales:
- Cálculo automático de precio de venta
- Dos tipos de posesión:
  - **Propio (Reventa):** Productos para vender
  - **Consignación:** Productos del proveedor en préstamo

### Campos específicos:

| Campo | Descripción |
|-------|-------------|
| Descripción | Nombre del repuesto ⭐ |
| Marca | Marca o fabricante |
| Cantidad | Stock disponible |
| Precio Compra | Costo de adquisición |
| % Ganancia | Margen de ganancia (default 30%) |
| **Precio Venta** | Se calcula automáticamente |
| Tipo | Propio o Consignación |

### Fórmula del precio de venta:
```
Precio Venta = Precio Compra × (1 + % Ganancia / 100)
```

---

## 9. MOVIMIENTOS DE INVENTARIO <a name="movimientos"></a>

### Acceder:
Click en **"Movimientos"** en el menú lateral

### Tipos de movimiento:

| Icono | Tipo | Efecto en Stock |
|-------|------|-----------------|
| ➕ | **Entrada** | Aumenta la cantidad |
| ➖ | **Salida** | Disminuye la cantidad |
| 🔄 | **Ajuste** | Establece cantidad exacta |
| 📥 | **Inicial** | Carga inicial |

### Registrar un movimiento:
1. Click en **"+ Nuevo Movimiento"**
2. Seleccione el **Producto**
3. Elija el **Tipo de movimiento**
4. Ingrese la **Cantidad**
5. Agregue una **Referencia** (factura, orden, etc.)
6. Escriba un **Comentario** (opcional)
7. Click en **"Guardar"**

### Validaciones:
- No puede hacer salida mayor al stock disponible
- Los ajustes sobrescriben la cantidad actual

### Escanear código de barras:
1. Click en **"Escanear"**
2. Permita acceso a la cámara
3. Apunte al código de barras
4. El sistema busca el producto automáticamente
5. Si lo encuentra → va al formulario de movimiento
6. Si no lo encuentra → va al formulario de nuevo producto

---

## 10. CATEGORÍAS <a name="categorías"></a>

### Acceder:
Click en **"Categorías"** en el menú lateral

### Propósito:
Organizar y clasificar los productos (ej: Electrónica, Ferretería, Alimenticios)

### Operaciones:

| Icono | Operación | Administrador | Usuario |
|-------|-----------|:-------------:|:-------:|
| 📂 | Ver lista | ✅ | ✅ |
| ➕ | Nueva categoría | ✅ | ✅ |
| ✏️ | Editar | ✅ | ✅ |
| 🗑️ | Eliminar | ✅ | ❌ |

### Crear categoría:
1. Click en **"+ Nueva Categoría"**
2. Ingrese:
   - **Nombre** ⭐ (ej: "Electrónica")
   - **Descripción** (opcional)
3. Click en **"Guardar"**

> ⚠️ No puede eliminar una categoría con productos asociados.

---

## 11. PROVEEDORES <a name="proveedores"></a>

### Acceder:
Click en **"Proveedores"** en el menú lateral

### Propósito:
Mantener los datos de contacto de los proveedores para compras.

### Campos:

| Campo | Descripción |
|-------|-------------|
| Nombre | Nombre de la empresa ⭐ |
| Contacto | Nombre de la persona |
| Teléfono | Número de contacto |
| Email | Correo electrónico |
| Dirección | Dirección física |

### Operaciones:

| Icono | Operación | Administrador | Usuario |
|-------|-----------|:-------------:|:-------:|
| 👥 | Ver lista | ✅ | ✅ |
| ➕ | Nuevo proveedor | ✅ | ✅ |
| ✏️ | Editar | ✅ | ✅ |
| 🗑️ | Eliminar | ✅ | ❌ |

---

## 12. IMPORTAR/EXPORTAR DATOS <a name="importar-exportar"></a>

### Importar productos (CSV):
1. Click en **"Importar"** en el menú
2. Seleccione el archivo CSV
3. El sistema procesa y muestra un resumen:
   - Total de registros
   - Creados
   - Actualizados
   - Errores

#### Formato del archivo CSV:
```csv
codigo,nombre,descripcion,categoria,ubicacion,cantidad,precio,proveedor,fecha_vencimiento,stock_minimo
PROD001,Producto Ejemplo,Descripción del producto,Electrónica,A-1,100,25.50,Proveedor ABC,2025-12-31,10
```

### Exportar productos (CSV):
1. Click en **"Exportar"**
2. Click en **"Descargar CSV"**
3. Se descarga un archivo con todos los productos

---

## 13. RESPALDOS <a name="respaldos"></a>

### Acceder:
Click en **"Respaldos"** en el menú lateral

> ⚠️ Solo disponible para **Administradores**

### Operaciones:

| Icono | Operación | Descripción |
|-------|-----------|-------------|
| 💾 | **Crear respaldo** | Genera una copia de seguridad |
| ⬇️ | **Descargar** | Guarda el respaldo en su PC |
| 🗑️ | **Eliminar** | Borra un respaldo |

### Tipos de respaldo:
- **Completo:** Toda la base de datos
- **Solo productos:** Solo datos de productos

### Ubicación de respaldos:
Los archivos se guardan en la carpeta `backups/` del proyecto.

---

## 14. CERRAR EL SISTEMA <a name="cerrar-sistema"></a>

### Método 1: Desde la aplicación
1. Click en su **nombre de usuario** (esquina superior derecha)
2. Seleccione **"Apagar Sistema"**
3. La pestaña mostrará "Sistema Apagado"
4. El servidor se detiene automáticamente

### Método 2: Desde el servidor (CMD)
Si el servidor está corriendo en una ventana de CMD:
- Presione **Ctrl + C**
- Confirme con **S** o **Y**

### Método 3: Forzar cierre
1. Abra el **Administrador de Tareas** (Ctrl + Shift + Esc)
2. Busque el proceso **python**
3. Click en **"Finalizar tarea"**

---

## ÍCONOS DEL SISTEMA

| Ícono | Significado |
|-------|-------------|
| 📊 | Dashboard / Estadísticas |
| 📦 | Productos |
| 🔧 | Repuestos |
| 📋 | Movimientos |
| 🏷️ | Categorías |
| 👥 | Proveedores |
| 📁 | Importar/Exportar |
| 💾 | Respaldos |
| ⚙️ | Configuración |
| ➕ | Agregar/Nuevo |
| ✏️ | Editar |
| 🗑️ | Eliminar |
| 👁️ | Ver/Detalle |
| 🔍 | Buscar |
| ⬇️ | Descargar |
| ⬆️ | Subir |
| ⚠️ | Alerta |
| ✅ | Éxito |
| ❌ | Error |
| ⚙️ | Configuración |

---

## SOLUCIÓN DE PROBLEMAS

| Problema | Solución |
|----------|----------|
| Error de NumPy | Reinicie el servidor |
| Puerto en uso | Espere unos segundos y reintente |
| No puedo eliminar | Verifique que no tenga movimientos asociados |
| No aparece la interfaz | Acceda desde otro navegador |
| Contraseña olvidada | Contacte al administrador |

---

## INFORMACIÓN DE CONTACTO

Para soporte técnico:
- **GitHub:** https://github.com/Don-Nadie-Lab/ToolKinventario
- **Email:** Soporte@ejemplo.com

---

**Versión:** 1.0.0  
**Última actualización:** Marzo 2026
