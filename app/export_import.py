# -*- coding: utf-8 -*-
"""
==========================================================
CAPA DE APLICACIÓN - Exportación e Importación de Datos
==========================================================
Sistema para respaldar y restaurar la base de datos completa.
Permite迁移 de datos entre versiones de la aplicación.

Funcionalidades:
- Exportar toda la base de datos a JSON
- Importar datos desde archivo JSON
- Validar compatibilidad de versiones
- Respaldar antes de importar

Uso:
    from app.export_import import exportar_db, importar_db
    
    # Exportar
    archivo = exportar_db()
    
    # Importar
    resultado = importar_db(archivo)
"""

import os
import json
import shutil
import sqlite3
from datetime import datetime
from io import BytesIO
from flask import current_app

from .models import db, Usuario, Producto, Categoria, Proveedor, Movimiento, Repuesto, LogAuditoria, Configuracion

VERSION_SCHEMA = "1.0.0"
NOMBRE_APP = "ToolKinventario"


class ExportacionError(Exception):
    """Error durante la exportación."""
    pass


class ImportacionError(Exception):
    """Error durante la importación."""
    pass


def obtener_info_esquema():
    """
    Obtiene información del esquema actual de la BD.
    
    Returns:
        dict: Información del esquema
    """
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        tablas = {}
        for tabla in ['usuarios', 'categorias', 'proveedores', 'productos', 'movimientos', 'repuestos', 'configuraciones', 'logs_auditoria']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cursor.fetchone()[0]
                tablas[tabla] = count
            except sqlite3.OperationalError:
                tablas[tabla] = 0
        
        conn.close()
        
        return {
            'version_schema': VERSION_SCHEMA,
            'nombre_app': NOMBRE_APP,
            'tablas': tablas,
            'fecha': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'version_schema': VERSION_SCHEMA,
            'nombre_app': NOMBRE_APP
        }


def exportar_db():
    """
    Exporta toda la base de datos a un diccionario JSON.
    
    Returns:
        dict: Diccionario con todos los datos de la BD
    """
    datos = {
        'metadatos': {
            'version_schema': VERSION_SCHEMA,
            'nombre_app': NOMBRE_APP,
            'version_app': current_app.config.get('VERSION', '1.0.0'),
            'fecha_export': datetime.now().isoformat(),
            'info_esquema': obtener_info_esquema()
        },
        'datos': {}
    }
    
    # Exportar usuarios (sin password_hash sensible)
    usuarios = []
    for u in Usuario.query.all():
        usuarios.append({
            'id': u.id,
            'username': u.username,
            'nombre': u.nombre,
            'email': u.email,
            'rol': u.rol,
            'activo': u.activo,
            'fecha_creacion': u.fecha_creacion.isoformat() if u.fecha_creacion else None,
            'ultimo_acceso': u.ultimo_acceso.isoformat() if u.ultimo_acceso else None
        })
    datos['datos']['usuarios'] = usuarios
    
    # Exportar categorías
    categorias = []
    for c in Categoria.query.all():
        categorias.append({
            'id': c.id,
            'nombre': c.nombre,
            'descripcion': c.descripcion
        })
    datos['datos']['categorias'] = categorias
    
    # Exportar proveedores
    proveedores = []
    for p in Proveedor.query.all():
        proveedores.append({
            'id': p.id,
            'nombre': p.nombre,
            'contacto': p.contacto,
            'telefono': p.telefono,
            'email': p.email,
            'direccion': p.direccion
        })
    datos['datos']['proveedores'] = proveedores
    
    # Exportar productos
    productos = []
    for p in Producto.query.all():
        productos.append({
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'categoria_id': p.categoria_id,
            'ubicacion': p.ubicacion,
            'cantidad': p.cantidad,
            'precio': p.precio,
            'proveedor_id': p.proveedor_id,
            'fecha_vencimiento': p.fecha_vencimiento.isoformat() if p.fecha_vencimiento else None,
            'stock_minimo': p.stock_minimo,
            'fecha_creacion': p.fecha_creacion.isoformat() if p.fecha_creacion else None,
            'fecha_actualizacion': p.fecha_actualizacion.isoformat() if p.fecha_actualizacion else None
        })
    datos['datos']['productos'] = productos
    
    # Exportar movimientos
    movimientos = []
    for m in Movimiento.query.all():
        movimientos.append({
            'id': m.id,
            'producto_id': m.producto_id,
            'usuario_id': m.usuario_id,
            'tipo': m.tipo,
            'cantidad': m.cantidad,
            'cantidad_anterior': m.cantidad_anterior,
            'cantidad_nueva': m.cantidad_nueva,
            'fecha': m.fecha.isoformat() if m.fecha else None,
            'comentario': m.comentario,
            'referencia': m.referencia
        })
    datos['datos']['movimientos'] = movimientos
    
    # Exportar repuestos
    repuestos = []
    for r in Repuesto.query.all():
        repuestos.append({
            'id': r.id,
            'descripcion': r.descripcion,
            'marca': r.marca,
            'tipo': r.tipo,
            'cantidad': r.cantidad,
            'precio_compra': r.precio_compra,
            'ganancia_porcentaje': r.ganancia_porcentaje,
            'proveedor_id': r.proveedor_id,
            'fecha_creacion': r.fecha_creacion.isoformat() if r.fecha_creacion else None
        })
    datos['datos']['repuestos'] = repuestos
    
    # Exportar configuraciones
    configs = []
    for c in Configuracion.query.all():
        configs.append({
            'id': c.id,
            'clave': c.clave,
            'valor': c.valor,
            'descripcion': c.descripcion
        })
    datos['datos']['configuraciones'] = configs
    
    return datos


def validar_importacion(datos):
    """
    Valida que los datos a importar sean compatibles.
    
    Args:
        datos: Diccionario con los datos a importar
        
    Returns:
        tuple: (es_valido, mensaje, advertencias)
    """
    advertencias = []
    errores = []
    
    # Verificar estructura básica
    if 'metadatos' not in datos:
        errores.append("Archivo corrupto: faltan metadatos")
        return False, errores, advertencias
    
    if 'datos' not in datos:
        errores.append("Archivo corrupto: faltan datos")
        return False, errores, advertencias
    
    metadatos = datos['metadatos']
    
    # Verificar versión de schema
    version_schema = metadatos.get('version_schema', 'desconocida')
    if version_schema != VERSION_SCHEMA:
        advertencias.append(
            f"Versión del archivo: {version_schema} - "
            f"Versión actual: {VERSION_SCHEMA}. "
            f"La importación podría tener problemas de compatibilidad."
        )
    
    # Verificar nombre de app
    if metadatos.get('nombre_app') != NOMBRE_APP:
        errores.append(f"Este archivo no es de {NOMBRE_APP}")
        return False, errores, advertencias
    
    # Verificar que hay datos
    datos_contenido = datos.get('datos', {})
    if not any(datos_contenido.values()):
        advertencias.append("El archivo contiene tablas vacías")
    
    return len(errores) == 0, errores, advertencias


def importar_db(datos, crear_respaldo_local=True):
    """
    Importa datos desde un diccionario JSON.
    
    Args:
        datos: Diccionario con los datos a importar
        crear_respaldo_local: Si True, crea backup antes de importar
        
    Returns:
        dict: Resultado de la importación
        
    Raises:
        ImportacionError: Si hay errores durante la importación
    """
    # Validar datos
    es_valido, errores, advertencias = validar_importacion(datos)
    
    if not es_valido:
        raise ImportacionError("; ".join(errores))
    
    # Crear respaldo de la BD actual
    if crear_respaldo_local:
        try:
            respaldo = exportar_db()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if getattr(current_app, '_blueprints', None):
                backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
            else:
                backup_dir = 'backups'
            
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, f'auto_backup_before_import_{timestamp}.json')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(respaldo, f, indent=2, ensure_ascii=False)
            
            current_app.logger.info(f"Respaldo automático creado: {backup_file}")
        except Exception as e:
            current_app.logger.warning(f"No se pudo crear respaldo automático: {e}")
    
    # Importar datos
    datos_contenido = datos.get('datos', {})
    resultados = {
        'usuarios': 0,
        'categorias': 0,
        'proveedores': 0,
        'productos': 0,
        'movimientos': 0,
        'repuestos': 0,
        'configuraciones': 0
    }
    
    try:
        # Importar categorías primero (FK de productos)
        for cat_data in datos_contenido.get('categorias', []):
            existente = Categoria.query.filter_by(nombre=cat_data['nombre']).first()
            if not existente:
                cat = Categoria(
                    nombre=cat_data['nombre'],
                    descripcion=cat_data.get('descripcion')
                )
                db.session.add(cat)
                resultados['categorias'] += 1
        
        # Importar proveedores
        for prov_data in datos_contenido.get('proveedores', []):
            existente = Proveedor.query.filter_by(nombre=prov_data['nombre']).first()
            if not existente:
                prov = Proveedor(
                    nombre=prov_data['nombre'],
                    contacto=prov_data.get('contacto'),
                    telefono=prov_data.get('telefono'),
                    email=prov_data.get('email'),
                    direccion=prov_data.get('direccion')
                )
                db.session.add(prov)
                resultados['proveedores'] += 1
        
        # Importar productos
        for prod_data in datos_contenido.get('productos', []):
            existente = Producto.query.filter_by(codigo=prod_data['codigo']).first()
            if not existente:
                prod = Producto(
                    codigo=prod_data['codigo'],
                    nombre=prod_data['nombre'],
                    descripcion=prod_data.get('descripcion'),
                    categoria_id=prod_data.get('categoria_id'),
                    ubicacion=prod_data.get('ubicacion'),
                    cantidad=prod_data.get('cantidad', 0),
                    precio=prod_data.get('precio', 0),
                    proveedor_id=prod_data.get('proveedor_id'),
                    stock_minimo=prod_data.get('stock_minimo', 5),
                    fecha_creacion=datetime.fromisoformat(prod_data['fecha_creacion']) if prod_data.get('fecha_creacion') else datetime.now()
                )
                if prod_data.get('fecha_vencimiento'):
                    from datetime import date
                    prod.fecha_vencimiento = date.fromisoformat(prod_data['fecha_vencimiento'])
                db.session.add(prod)
                resultados['productos'] += 1
        
        # Importar repuestos
        for rep_data in datos_contenido.get('repuestos', []):
            existente = Repuesto.query.filter_by(descripcion=rep_data['descripcion']).first()
            if not existente:
                rep = Repuesto(
                    descripcion=rep_data['descripcion'],
                    marca=rep_data.get('marca'),
                    tipo=rep_data.get('tipo'),
                    cantidad=rep_data.get('cantidad', 0),
                    precio_compra=rep_data.get('precio_compra', 0),
                    ganancia_porcentaje=rep_data.get('ganancia_porcentaje', 30),
                    proveedor_id=rep_data.get('proveedor_id')
                )
                db.session.add(rep)
                resultados['repuestos'] += 1
        
        # Importar configuraciones
        for config_data in datos_contenido.get('configuraciones', []):
            existente = Configuracion.query.filter_by(clave=config_data['clave']).first()
            if existente:
                existente.valor = config_data.get('valor', existente.valor)
            else:
                config = Configuracion(
                    clave=config_data['clave'],
                    valor=config_data.get('valor'),
                    descripcion=config_data.get('descripcion')
                )
                db.session.add(config)
            resultados['configuraciones'] += 1
        
        # Commit de los cambios
        db.session.commit()
        
        return {
            'success': True,
            'resultados': resultados,
            'advertencias': advertencias,
            'mensaje': f"Se importaron {sum(resultados.values())} registros"
        }
        
    except Exception as e:
        db.session.rollback()
        raise ImportacionError(f"Error durante la importación: {str(e)}")


def obtener_preview_importacion(datos):
    """
    Obtiene una vista previa de lo que se importaría.
    
    Args:
        datos: Diccionario con los datos a importar
        
    Returns:
        dict: Preview de la importación
    """
    es_valido, errores, advertencias = validar_importacion(datos)
    
    datos_contenido = datos.get('datos', {})
    
    preview = {
        'valido': es_valido,
        'errores': errores,
        'advertencias': advertencias,
        'metadatos': datos.get('metadatos', {}),
        'contenido': {
            'usuarios': len(datos_contenido.get('usuarios', [])),
            'categorias': len(datos_contenido.get('categorias', [])),
            'proveedores': len(datos_contenido.get('proveedores', [])),
            'productos': len(datos_contenido.get('productos', [])),
            'movimientos': len(datos_contenido.get('movimientos', [])),
            'repuestos': len(datos_contenido.get('repuestos', [])),
            'configuraciones': len(datos_contenido.get('configuraciones', []))
        },
        'total_registros': sum(len(v) for v in datos_contenido.values())
    }
    
    return preview
