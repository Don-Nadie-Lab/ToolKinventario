# -*- coding: utf-8 -*-
"""
Funciones auxiliares para ToolKinventario
Utilidades generales, respaldos, validaciones y configuración
"""

import os
import csv
import logging
import shutil
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from flask import current_app, request
from werkzeug.utils import secure_filename
from .models import db, Usuario, Producto, Movimiento, Categoria, Proveedor, Rol

def crear_directorios_necesarios(app):
    """
    Crea los directorios necesarios para la aplicación
    """
    directorios = [
        'database',
        'backups',
        'logs',
        'uploads',
        'static/uploads'
    ]
    
    for directorio in directorios:
        if not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)
            print(f"Directorio creado: {directorio}")

def configurar_logger(app):
    """
    Configura el sistema de logging con rotacion automatica
    Usa ubicacion con permisos de escritura (APPDATA)
    """
    if not app.debug:
        # Usar APPDATA para logs (tiene permisos de escritura)
        app_name = 'ToolKinventario'
        log_dir = os.path.join(os.environ.get('APPDATA', '.'), app_name, 'logs')
        
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'toolkinventario.log')
            
            file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
        except Exception:
            # Si falla, continuar sin logging a archivo
            pass
    
    return app.logger

def crear_usuario_admin_inicial():
    """
    Crea un usuario administrador inicial si no existe ninguno
    """
    # Verificar si ya existe un administrador
    admin_existente = Usuario.query.filter_by(rol=Rol.ADMIN).first()
    
    if not admin_existente:
        # Crear usuario administrador por defecto
        admin = Usuario(
            username='admin',
            nombre='Administrador',
            email='admin@toolkinventario.local',
            rol=Rol.ADMIN
        )
        admin.set_password('admin123')  # Contraseña temporal - DEBE ser cambiada
        
        db.session.add(admin)
        db.session.commit()
        
        print("Usuario administrador creado:")
        print("Usuario: admin")
        print("Contraseña: admin123")
        print("¡IMPORTANTE: Cambie la contraseña por defecto!")

def verificar_credenciales_por_defecto():
    """
    Verifica si existe un usuario con credenciales por defecto.
    Útil para forzar cambio de contraseña en primer acceso.
    
    Returns:
        bool: True si el usuario admin tiene la contraseña por defecto
    """
    admin = Usuario.query.filter_by(username='admin').first()
    if admin and admin.check_password('admin123'):
        return True
    return False

def es_password_seguro(password):
    """
    Verifica si una contraseña cumple con requisitos mínimos de seguridad.
    
    Args:
        password: Contraseña a verificar
        
    Returns:
        tuple: (es_segura, mensaje_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe tener al menos una mayúscula"
    
    if not any(c.islower() for c in password):
        return False, "La contraseña debe tener al menos una minúscula"
    
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe tener al menos un número"
    
    return True, ""

def generar_respaldo(tipo='completo'):
    """
    Genera un respaldo de la base de datos en formato CSV
    
    Args:
        tipo: Tipo de respaldo ('completo', 'productos', 'movimientos')
        
    Returns:
        str: Ruta del archivo de respaldo generado
    """
    try:
        # Crear directorio de respaldos si no existe
        backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if tipo == 'completo':
            # Respaldo completo de todas las tablas
            archivo_respaldo = os.path.join(backup_dir, f'respaldo_completo_{timestamp}.zip')
            
            # Crear archivos CSV individuales
            archivos_csv = []
            
            # Respaldar productos
            archivo_productos = os.path.join(backup_dir, f'productos_{timestamp}.csv')
            exportar_productos_csv(archivo_productos)
            archivos_csv.append(archivo_productos)
            
            # Respaldar movimientos
            archivo_movimientos = os.path.join(backup_dir, f'movimientos_{timestamp}.csv')
            exportar_movimientos_csv(archivo_movimientos)
            archivos_csv.append(archivo_movimientos)
            
            # Respaldar categorías
            archivo_categorias = os.path.join(backup_dir, f'categorias_{timestamp}.csv')
            exportar_categorias_csv(archivo_categorias)
            archivos_csv.append(archivo_categorias)
            
            # Respaldar proveedores
            archivo_proveedores = os.path.join(backup_dir, f'proveedores_{timestamp}.csv')
            exportar_proveedores_csv(archivo_proveedores)
            archivos_csv.append(archivo_proveedores)
            
            # Crear archivo ZIP con todos los CSV
            import zipfile
            with zipfile.ZipFile(archivo_respaldo, 'w') as zipf:
                for archivo in archivos_csv:
                    zipf.write(archivo, os.path.basename(archivo))
                    os.remove(archivo)  # Eliminar CSV individual
            
            return archivo_respaldo
            
        elif tipo == 'productos':
            archivo_respaldo = os.path.join(backup_dir, f'productos_{timestamp}.csv')
            exportar_productos_csv(archivo_respaldo)
            return archivo_respaldo
            
        elif tipo == 'movimientos':
            archivo_respaldo = os.path.join(backup_dir, f'movimientos_{timestamp}.csv')
            exportar_movimientos_csv(archivo_respaldo)
            return archivo_respaldo
            
    except Exception as e:
        current_app.logger.error(f"Error al generar respaldo: {str(e)}")
        raise

def exportar_productos_csv(archivo_destino):
    """
    Exporta productos a un archivo CSV
    
    Args:
        archivo_destino: Ruta del archivo CSV de destino
    """
    with open(archivo_destino, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Encabezados
        writer.writerow([
            'id', 'codigo', 'nombre', 'descripcion', 'categoria', 'ubicacion',
            'cantidad', 'precio', 'proveedor', 'fecha_vencimiento', 'stock_minimo',
            'fecha_creacion', 'fecha_actualizacion'
        ])
        
        # Datos
        productos = Producto.query.all()
        for producto in productos:
            writer.writerow([
                producto.id,
                producto.codigo,
                producto.nombre,
                producto.descripcion or '',
                producto.categoria.nombre if producto.categoria else '',
                producto.ubicacion or '',
                producto.cantidad,
                producto.precio,
                producto.proveedor.nombre if producto.proveedor else '',
                producto.fecha_vencimiento.strftime('%Y-%m-%d') if producto.fecha_vencimiento else '',
                producto.stock_minimo,
                producto.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
                producto.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S')
            ])

def exportar_movimientos_csv(archivo_destino):
    """
    Exporta movimientos a un archivo CSV
    
    Args:
        archivo_destino: Ruta del archivo CSV de destino
    """
    with open(archivo_destino, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Encabezados
        writer.writerow([
            'id', 'producto_codigo', 'producto_nombre', 'usuario', 'tipo',
            'cantidad', 'cantidad_anterior', 'cantidad_nueva', 'fecha',
            'comentario', 'referencia'
        ])
        
        # Datos
        movimientos = Movimiento.query.all()
        for movimiento in movimientos:
            writer.writerow([
                movimiento.id,
                movimiento.producto.codigo,
                movimiento.producto.nombre,
                movimiento.usuario.username,
                movimiento.tipo,
                movimiento.cantidad,
                movimiento.cantidad_anterior,
                movimiento.cantidad_nueva,
                movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                movimiento.comentario or '',
                movimiento.referencia or ''
            ])

def exportar_categorias_csv(archivo_destino):
    """
    Exporta categorías a un archivo CSV
    
    Args:
        archivo_destino: Ruta del archivo CSV de destino
    """
    with open(archivo_destino, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Encabezados
        writer.writerow(['id', 'nombre', 'descripcion'])
        
        # Datos
        categorias = Categoria.query.all()
        for categoria in categorias:
            writer.writerow([
                categoria.id,
                categoria.nombre,
                categoria.descripcion or ''
            ])

def exportar_proveedores_csv(archivo_destino):
    """
    Exporta proveedores a un archivo CSV
    
    Args:
        archivo_destino: Ruta del archivo CSV de destino
    """
    with open(archivo_destino, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Encabezados
        writer.writerow(['id', 'nombre', 'contacto', 'telefono', 'email', 'direccion'])
        
        # Datos
        proveedores = Proveedor.query.all()
        for proveedor in proveedores:
            writer.writerow([
                proveedor.id,
                proveedor.nombre,
                proveedor.contacto or '',
                proveedor.telefono or '',
                proveedor.email or '',
                proveedor.direccion or ''
            ])

# ========================================================
# BACKUP Y RESPALDO
# ========================================================
def programar_respaldo_automatico(app):
    """
    Configura respaldos automaticos usando programador.
    Se ejecuta cada dia a la medianoche.
    
    Args:
        app: Instancia de la aplicacion Flask
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        
        # Programar respaldo diario a medianoche
        scheduler.add_job(
            lambda: generar_respaldo_automatico(app),
            'cron',
            hour=0,
            minute=0,
            id='backup_diario'
        )
        
        scheduler.start()
        app.logger.info("Programador de respaldos iniciado")
        
    except ImportError:
        app.logger.warning("APScheduler no instalado. Backups automaticos deshabilitados.")
    except Exception as e:
        app.logger.error(f"Error al configurar respaldos automaticos: {e}")

def generar_respaldo_automatico(app):
    """
    Genera un respaldo automatico de la base de datos.
    Se llama automaticamente via scheduler.
    """
    with app.app_context():
        try:
            # Generar respaldo
            archivo = generar_respaldo(tipo='completo')
            app.logger.info(f"Respaldo automatico generado: {archivo}")
            
            # Limpiar respaldos antiguos (mantener ultimos 7 dias)
            limpiar_respaldos_antiguos(7)
            
            return archivo
        except Exception as e:
            app.logger.error(f"Error en respaldo automatico: {e}")
            return None

def limpiar_respaldos_antiguos(dias_mantener=7):
    """
    Elimina respaldos antiguos para ahorrar espacio
    
    Args:
        dias_mantener: Número de días de respaldos a mantener
    """
    try:
        backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
        if not os.path.exists(backup_dir):
            return
        
        fecha_limite = datetime.now() - timedelta(days=dias_mantener)
        
        for archivo in os.listdir(backup_dir):
            ruta_archivo = os.path.join(backup_dir, archivo)
            
            if os.path.isfile(ruta_archivo):
                fecha_archivo = datetime.fromtimestamp(os.path.getctime(ruta_archivo))
                
                if fecha_archivo < fecha_limite:
                    os.remove(ruta_archivo)
                    current_app.logger.info(f"Respaldo antiguo eliminado: {archivo}")
                    
    except Exception as e:
        current_app.logger.error(f"Error al limpiar respaldos antiguos: {str(e)}")

def allowed_file(filename, extensiones_permitidas):
    """
    Verifica si un archivo tiene una extensión permitida
    
    Args:
        filename: Nombre del archivo
        extensiones_permitidas: Lista de extensiones permitidas
        
    Returns:
        bool: True si la extensión es permitida
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensiones_permitidas

def paginar_resultados(query, page=1, per_page=20):
    """
    Pagina los resultados de una consulta
    
    Args:
        query: Consulta SQLAlchemy
        page: Número de página
        per_page: Elementos por página
        
    Returns:
        Objeto de paginación
    """
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def validar_codigo_producto(codigo):
    """
    Valida que un código de producto sea único y tenga formato válido
    
    Args:
        codigo: Código a validar
        
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if not codigo:
        return False, "El código es obligatorio"
    
    # Eliminar espacios
    codigo = codigo.strip()
    
    if len(codigo) < 3:
        return False, "El código debe tener al menos 3 caracteres"
    
    if len(codigo) > 50:
        return False, "El código no puede tener más de 50 caracteres"
    
    # Verificar caracteres permitidos
    import re
    if not re.match(r'^[A-Za-z0-9\-_\.]+$', codigo):
        return False, "El código solo puede contener letras, números, guiones, guiones bajos y puntos"
    
    return True, ""

def formatear_precio(precio):
    """
    Formatea un precio para mostrar
    
    Args:
        precio: Precio a formatear
        
    Returns:
        str: Precio formateado
    """
    if precio is None:
        return "$0.00"
    
    return f"${precio:,.2f}"

def formatear_fecha(fecha):
    """
    Formatea una fecha para mostrar
    
    Args:
        fecha: Fecha a formatear
        
    Returns:
        str: Fecha formateada
    """
    if fecha is None:
        return ""
    
    if isinstance(fecha, datetime):
        return fecha.strftime('%d/%m/%Y %H:%M')
    else:
        return fecha.strftime('%d/%m/%Y')

def calcular_estadisticas_inventario():
    """
    Calcula estadísticas generales del inventario
    
    Returns:
        dict: Diccionario con estadísticas
    """
    try:
        # Valor total del inventario
        valor_total = db.session.query(
            db.func.sum(Producto.cantidad * Producto.precio)
        ).scalar() or 0
        
        # Productos con stock bajo
        productos_stock_bajo = Producto.query.filter(
            Producto.cantidad <= Producto.stock_minimo
        ).count()
        
        # Productos sin stock
        productos_sin_stock = Producto.query.filter(
            Producto.cantidad == 0
        ).count()
        
        # Movimientos del mes actual
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        movimientos_mes = Movimiento.query.filter(
            Movimiento.fecha >= inicio_mes
        ).count()
        
        # Categoría con más productos
        categoria_top = db.session.query(
            Categoria.nombre,
            db.func.count(Producto.id).label('total')
        ).join(Producto).group_by(Categoria.id).order_by(
            db.desc('total')
        ).first()
        
        return {
            'valor_total': valor_total,
            'productos_stock_bajo': productos_stock_bajo,
            'productos_sin_stock': productos_sin_stock,
            'movimientos_mes': movimientos_mes,
            'categoria_top': categoria_top.nombre if categoria_top else 'N/A'
        }
        
    except Exception as e:
        current_app.logger.error(f"Error al calcular estadísticas: {str(e)}")
        return {
            'valor_total': 0,
            'productos_stock_bajo': 0,
            'productos_sin_stock': 0,
            'movimientos_mes': 0,
            'categoria_top': 'N/A'
        }

def obtener_productos_vencimiento_proximo(dias=30):
    """
    Obtiene productos que vencen en los próximos días
    
    Args:
        dias: Número de días a considerar
        
    Returns:
        Lista de productos próximos a vencer
    """
    fecha_limite = datetime.now().date() + timedelta(days=dias)
    
    return Producto.query.filter(
        Producto.fecha_vencimiento.isnot(None),
        Producto.fecha_vencimiento <= fecha_limite,
        Producto.cantidad > 0
    ).order_by(Producto.fecha_vencimiento).all()

def generar_reporte_stock_bajo():
    """
    Genera un reporte de productos con stock bajo
    
    Returns:
        Lista de productos con stock bajo
    """
    return Producto.query.filter(
        Producto.cantidad <= Producto.stock_minimo
    ).order_by(Producto.cantidad).all()

def obtener_configuracion(clave, valor_defecto=None):
    """
    Obtiene una configuración del sistema
    
    Args:
        clave: Clave de configuración
        valor_defecto: Valor por defecto si no existe
        
    Returns:
        Valor de configuración
    """
    from .models import Configuracion
    
    config = Configuracion.query.filter_by(clave=clave).first()
    if config:
        return config.valor
    else:
        return valor_defecto

def establecer_configuracion(clave, valor, descripcion=None):
    """
    Establece una configuración del sistema
    
    Args:
        clave: Clave de configuración
        valor: Valor a establecer
        descripcion: Descripción opcional
    """
    from .models import Configuracion
    
    config = Configuracion.query.filter_by(clave=clave).first()
    if config:
        config.valor = valor
        if descripcion:
            config.descripcion = descripcion
    else:
        config = Configuracion(
            clave=clave,
            valor=valor,
            descripcion=descripcion
        )
        db.session.add(config)
    
    db.session.commit()

def verificar_integridad_base_datos():
    """
    Verifica la integridad de la base de datos
    
    Returns:
        dict: Resultado de la verificación
    """
    try:
        errores = []
        
        # Verificar productos sin categoría
        productos_sin_categoria = Producto.query.filter(
            Producto.categoria_id.is_(None)
        ).count()
        
        if productos_sin_categoria > 0:
            errores.append(f"{productos_sin_categoria} productos sin categoría")
        
        # Verificar movimientos huérfanos
        movimientos_huerfanos = db.session.query(Movimiento).filter(
            ~Movimiento.producto_id.in_(
                db.session.query(Producto.id)
            )
        ).count()
        
        if movimientos_huerfanos > 0:
            errores.append(f"{movimientos_huerfanos} movimientos sin producto asociado")
        
        # Verificar usuarios inactivos con sesiones
        # (Esta verificación dependería de cómo se manejen las sesiones)
        
        return {
            'integridad_ok': len(errores) == 0,
            'errores': errores
        }
        
    except Exception as e:
        current_app.logger.error(f"Error al verificar integridad: {str(e)}")
        return {
            'integridad_ok': False,
            'errores': [f"Error en verificación: {str(e)}"]
        }

def obtener_info_sistema():
    """
    Obtiene información del sistema para diagnóstico
    
    Returns:
        dict: Información del sistema
    """
    import platform
    import psutil
    
    try:
        return {
            'sistema_operativo': platform.system(),
            'version_so': platform.release(),
            'arquitectura': platform.machine(),
            'python_version': platform.python_version(),
            'memoria_total': f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            'memoria_disponible': f"{psutil.virtual_memory().available / (1024**3):.1f} GB",
            'uso_cpu': f"{psutil.cpu_percent()}%",
            'espacio_disco': f"{psutil.disk_usage('/').free / (1024**3):.1f} GB libres"
        }
    except Exception as e:
        current_app.logger.error(f"Error al obtener info del sistema: {str(e)}")
        return {
            'error': 'No se pudo obtener información del sistema'
        }
