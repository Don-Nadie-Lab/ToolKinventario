# -*- coding: utf-8 -*-
"""
==========================================================
CAPA DE APLICACION - Controladores / Vistas
==========================================================
Orquesta el flujo de informacion entre UI y Dominio.
Maneja las peticiones HTTP y coordina las operaciones.

Modulos:
- Dashboard: Estadisticas globales
- Productos: CRUD y busqueda
- Movimientos: Registro de entradas/salidas
- Categorias: Gestion de categorias
- Proveedores: Gestion de proveedores
- Importacion/Exportacion: Carga masiva de datos
"""

import csv
import io
import json
import os
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from markupsafe import escape
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename

from .models import db, Producto, Categoria, Proveedor, Movimiento, TipoMovimiento, Usuario, Repuesto
from .auth import admin_required, no_maestro_carga, registrar_log_auditoria
from .barcode import procesar_codigo_barras
from .utils import generar_respaldo, allowed_file, paginar_resultados
from .network import obtener_informacion_red, monitor_conexion

# Blueprint para vistas principales
views_bp = Blueprint('views', __name__)

# ========================================================
# RUTA PRINCIPAL
# ========================================================
@views_bp.route('/')
def index():
    """Redirige al dashboard o login segun autenticacion"""
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return redirect(url_for('auth.login'))

# ========================================================
# DASHBOARD
# ========================================================
@views_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Panel principal con resumen del inventario.
    Muestra metricas clave, alertas y URL de acceso.
    """
    # Estadisticas basicas
    total_productos = Producto.query.count()
    total_categorias = Categoria.query.count()
    total_movimientos = Movimiento.query.count()
    total_repuestos = Repuesto.query.count()
    
    # Valor total del inventario (productos)
    valor_inventario = db.session.query(
        db.func.sum(Producto.cantidad * Producto.precio)
    ).scalar() or 0
    
    # Valor total de repuestos
    valor_repuestos = db.session.query(
        db.func.sum(Repuesto.cantidad * Repuesto.precio_venta)
    ).scalar() or 0
    
    # Valor de compra de repuestos
    valor_compra_repuestos = db.session.query(
        db.func.sum(Repuesto.cantidad * Repuesto.precio_compra)
    ).scalar() or 0
    
    # Stock total
    stock_total_productos = db.session.query(
        db.func.sum(Producto.cantidad)
    ).scalar() or 0
    
    stock_total_repuestos = db.session.query(
        db.func.sum(Repuesto.cantidad)
    ).scalar() or 0
    
    # Productos con stock bajo (alerta)
    productos_stock_bajo = Producto.query.filter(
        Producto.cantidad <= Producto.stock_minimo
    ).limit(5).all()
    
    # Repuestos con stock bajo
    repuestos_stock_bajo = Repuesto.query.filter(
        Repuesto.cantidad <= 5
    ).limit(5).all()
    
    # Ultimos movimientos
    ultimos_movimientos = Movimiento.query.order_by(
        Movimiento.fecha.desc()
    ).limit(10).all()
    
    # Productos más movidos (Top 5)
    productos_mas_movidos = db.session.query(
        Producto, func.count(Movimiento.id).label('total')
    ).join(Movimiento).group_by(Producto.id).order_by(desc('total')).limit(5).all()
    
    # Obtener IP y puerto del servidor
    from flask import current_app
    ip_servidor = current_app.config.get('IP_LOCAL', '127.0.0.1')
    puerto_servidor = current_app.config.get('PUERTO_EJECUCION', 5050)
    url_acceso = f"http://{ip_servidor}:{puerto_servidor}"
    
    return render_template('dashboard.html',
                          total_productos=total_productos,
                          total_categorias=total_categorias,
                          total_movimientos=total_movimientos,
                          total_repuestos=total_repuestos,
                          valor_inventario=valor_inventario,
                          valor_repuestos=valor_repuestos,
                          valor_compra_repuestos=valor_compra_repuestos,
                          stock_total_productos=stock_total_productos,
                          stock_total_repuestos=stock_total_repuestos,
                          productos_stock_bajo=productos_stock_bajo,
                          repuestos_stock_bajo=repuestos_stock_bajo,
                          ultimos_movimientos=ultimos_movimientos,
                          productos_mas_movidos=productos_mas_movidos,
                          ip_servidor=ip_servidor,
                          puerto_servidor=puerto_servidor,
                          url_acceso=url_acceso)

# ---- GESTION DE PRODUCTOS ----
# CRUD completo de productos con filtros y paginacion

@views_bp.route('/productos')
@login_required
def lista_productos():
    """
    Lista de productos con filtros y paginación
    """
    # Parámetros de búsqueda y filtrado
    busqueda = request.args.get('busqueda', '')
    categoria_id = request.args.get('categoria_id', type=int)
    stock_bajo = request.args.get('stock_bajo', type=int)
    
    # Construir consulta base
    query = Producto.query
    
    # Aplicar filtros
    if busqueda:
        query = query.filter(
            (Producto.codigo.ilike(f'%{busqueda}%')) |
            (Producto.nombre.ilike(f'%{busqueda}%')) |
            (Producto.descripcion.ilike(f'%{busqueda}%'))
        )
    
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    
    if stock_bajo:
        query = query.filter(Producto.cantidad <= Producto.stock_minimo)
    
    # Ordenar y paginar resultados
    productos = paginar_resultados(
        query.order_by(Producto.nombre),
        page=request.args.get('page', 1, type=int),
        per_page=20
    )
    
    # Obtener categorías para el filtro
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    
    return render_template('productos/lista.html',
                          productos=productos,
                          categorias=categorias,
                          busqueda=busqueda,
                          categoria_id=categoria_id,
                          stock_bajo=stock_bajo)

@views_bp.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def nuevo_producto():
    """
    Crea un nuevo producto
    """
    if request.method == 'POST':
        # Obtener datos del formulario
        codigo = request.form.get('codigo')
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        categoria_id = request.form.get('categoria_id', type=int)
        ubicacion = request.form.get('ubicacion')
        cantidad = request.form.get('cantidad', type=int, default=0)
        precio = request.form.get('precio', type=float, default=0.0)
        proveedor_id = request.form.get('proveedor_id', type=int)
        stock_minimo = request.form.get('stock_minimo', type=int, default=5)
        
        # Fecha de vencimiento (opcional)
        fecha_vencimiento_str = request.form.get('fecha_vencimiento')
        fecha_vencimiento = None
        if fecha_vencimiento_str:
            try:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido.', 'danger')
                return redirect(url_for('views.nuevo_producto'))
        
        # Validar datos obligatorios
        if not codigo or not nombre or not categoria_id:
            flash('Por favor complete los campos obligatorios.', 'warning')
            categorias = Categoria.query.all()
            proveedores = Proveedor.query.all()
            return render_template('productos/nuevo.html', 
                                  categorias=categorias, 
                                  proveedores=proveedores)
        
        # Verificar si el código ya existe
        if Producto.query.filter_by(codigo=codigo).first():
            flash('Ya existe un producto con este codigo.', 'danger')
            categorias = Categoria.query.all()
            proveedores = Proveedor.query.all()
            return render_template('productos/nuevo.html', 
                                  categorias=categorias, 
                                  proveedores=proveedores)
        
        # Crear nuevo producto con datos sanitizados
        nuevo_producto = Producto(
            codigo=escape(codigo).strip() if codigo else codigo,
            nombre=escape(nombre).strip() if nombre else nombre,
            descripcion=escape(descripcion).strip() if descripcion else descripcion,
            categoria_id=categoria_id,
            ubicacion=escape(ubicacion).strip() if ubicacion else ubicacion,
            cantidad=cantidad,
            precio=precio,
            proveedor_id=proveedor_id,
            fecha_vencimiento=fecha_vencimiento,
            stock_minimo=stock_minimo
        )
        
        db.session.add(nuevo_producto)
        db.session.commit()
        
        # Si hay cantidad inicial, registrar movimiento
        if cantidad > 0:
            movimiento = Movimiento(
                producto_id=nuevo_producto.id,
                usuario_id=current_user.id,
                tipo=TipoMovimiento.INICIAL,
                cantidad=cantidad,
                cantidad_anterior=0,
                cantidad_nueva=cantidad,
                comentario='Carga inicial de producto'
            )
            db.session.add(movimiento)
            db.session.commit()
        
        registrar_log_auditoria('Creación de producto', 'productos', nuevo_producto.id)
        flash(f'Producto {nombre} creado correctamente.', 'success')
        return redirect(url_for('views.lista_productos'))
    
    # GET: Mostrar formulario
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    proveedores = Proveedor.query.all()
    
    return render_template('productos/nuevo.html', 
                          categorias=categorias, 
                          proveedores=proveedores)

@views_bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def editar_producto(id):
    """
    Edita un producto existente
    """
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        categoria_id = request.form.get('categoria_id', type=int)
        ubicacion = request.form.get('ubicacion')
        precio = request.form.get('precio', type=float, default=0.0)
        proveedor_id = request.form.get('proveedor_id', type=int)
        stock_minimo = request.form.get('stock_minimo', type=int, default=5)
        
        # Fecha de vencimiento (opcional)
        fecha_vencimiento_str = request.form.get('fecha_vencimiento')
        fecha_vencimiento = None
        if fecha_vencimiento_str:
            try:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido.', 'danger')
                return redirect(url_for('views.editar_producto', id=id))
        
        # Validar datos obligatorios
        if not nombre or not categoria_id:
            flash('Por favor complete los campos obligatorios.', 'warning')
            categorias = Categoria.query.all()
            proveedores = Proveedor.query.all()
            return render_template('productos/editar.html', 
                                  producto=producto,
                                  categorias=categorias, 
                                  proveedores=proveedores)
        
        # Actualizar producto con datos sanitizados
        producto.nombre = escape(nombre).strip() if nombre else nombre
        producto.descripcion = escape(descripcion).strip() if descripcion else descripcion
        producto.categoria_id = categoria_id
        producto.ubicacion = escape(ubicacion).strip() if ubicacion else ubicacion
        producto.precio = precio
        producto.proveedor_id = proveedor_id
        producto.fecha_vencimiento = fecha_vencimiento
        producto.stock_minimo = stock_minimo
        producto.fecha_actualizacion = datetime.now()
        
        db.session.commit()
        
        registrar_log_auditoria('Actualización de producto', 'productos', producto.id)
        flash(f'Producto {nombre} actualizado correctamente.', 'success')
        return redirect(url_for('views.lista_productos'))
    
    # GET: Mostrar formulario
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    proveedores = Proveedor.query.all()
    
    return render_template('productos/editar.html', 
                          producto=producto,
                          categorias=categorias, 
                          proveedores=proveedores)

@views_bp.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required  # Solo administradores pueden eliminar productos
@no_maestro_carga  # Restricción anti-fraude
def eliminar_producto(id):
    """
    Elimina un producto (solo administradores)
    """
    producto = Producto.query.get_or_404(id)
    
    # Verificar si tiene movimientos asociados
    if Movimiento.query.filter_by(producto_id=id).first():
        flash('No se puede eliminar el producto porque tiene movimientos asociados.', 'danger')
        return redirect(url_for('views.lista_productos'))
    
    nombre = producto.nombre
    db.session.delete(producto)
    db.session.commit()
    
    registrar_log_auditoria('Eliminación de producto', 'productos', id, f'Producto: {nombre}')
    flash(f'Producto {nombre} eliminado correctamente.', 'success')
    return redirect(url_for('views.lista_productos'))

@views_bp.route('/productos/ver/<int:id>')
@login_required
def ver_producto(id):
    """
    Muestra detalles de un producto y su historial de movimientos
    """
    producto = Producto.query.get_or_404(id)
    
    # Obtener historial de movimientos
    movimientos = Movimiento.query.filter_by(producto_id=id).order_by(
        Movimiento.fecha.desc()
    ).limit(50).all()
    
    return render_template('productos/ver.html', 
                          producto=producto,
                          movimientos=movimientos)

# ---- GESTION DE MOVIMIENTOS ----
# Registro de entradas, salidas y ajustes de inventario

@views_bp.route('/movimientos')
@login_required
def lista_movimientos():
    """
    Lista de movimientos con filtros y paginación
    """
    # Parámetros de búsqueda y filtrado
    tipo = request.args.get('tipo')
    producto_id = request.args.get('producto_id', type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Construir consulta base
    query = Movimiento.query
    
    # Aplicar filtros
    if tipo:
        query = query.filter(Movimiento.tipo == tipo)
    
    if producto_id:
        query = query.filter(Movimiento.producto_id == producto_id)
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(func.date(Movimiento.fecha) >= fecha_desde_obj)
        except ValueError:
            flash('Formato de fecha desde inválido.', 'warning')
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            query = query.filter(func.date(Movimiento.fecha) <= fecha_hasta_obj)
        except ValueError:
            flash('Formato de fecha hasta inválido.', 'warning')
    
    # Ordenar y paginar resultados
    movimientos = paginar_resultados(
        query.order_by(Movimiento.fecha.desc()),
        page=request.args.get('page', 1, type=int),
        per_page=50
    )
    
    # Obtener productos para el filtro
    productos = Producto.query.order_by(Producto.nombre).all()
    
    return render_template('movimientos/lista.html',
                          movimientos=movimientos,
                          productos=productos,
                          tipo=tipo,
                          producto_id=producto_id,
                          fecha_desde=fecha_desde,
                          fecha_hasta=fecha_hasta,
                          tipos_movimiento=TipoMovimiento)

@views_bp.route('/movimientos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_movimiento():
    """
    Registra un nuevo movimiento de inventario
    """
    if request.method == 'POST':
        # Obtener datos del formulario
        producto_id = request.form.get('producto_id', type=int)
        tipo = request.form.get('tipo')
        cantidad = request.form.get('cantidad', type=int)
        comentario = request.form.get('comentario')
        referencia = request.form.get('referencia')
        
        # Validar datos
        if not producto_id or not tipo or not cantidad:
            flash('Por favor complete los campos obligatorios.', 'warning')
            productos = Producto.query.all()
            return render_template('movimientos/nuevo.html', 
                                  productos=productos,
                                  tipos_movimiento=TipoMovimiento)
        
        if cantidad <= 0:
            flash('La cantidad debe ser mayor que cero.', 'warning')
            productos = Producto.query.all()
            return render_template('movimientos/nuevo.html', 
                                  productos=productos,
                                  tipos_movimiento=TipoMovimiento)
        
        # Verificar tipo de movimiento válido
        if tipo not in [TipoMovimiento.ENTRADA, TipoMovimiento.SALIDA, TipoMovimiento.AJUSTE]:
            flash('Tipo de movimiento no válido.', 'danger')
            productos = Producto.query.all()
            return render_template('movimientos/nuevo.html', 
                                  productos=productos,
                                  tipos_movimiento=TipoMovimiento)
        
        # Obtener producto
        producto = Producto.query.get_or_404(producto_id)
        cantidad_anterior = producto.cantidad
        
        # Calcular nueva cantidad según el tipo de movimiento
        if tipo == TipoMovimiento.ENTRADA:
            cantidad_nueva = cantidad_anterior + cantidad
        elif tipo == TipoMovimiento.SALIDA:
            if cantidad > cantidad_anterior:
                flash('No hay suficiente stock para realizar esta salida.', 'danger')
                productos = Producto.query.all()
                return render_template('movimientos/nuevo.html', 
                                      productos=productos,
                                      tipos_movimiento=TipoMovimiento)
            cantidad_nueva = cantidad_anterior - cantidad
        else:  # AJUSTE
            cantidad_nueva = cantidad
        
        # Crear movimiento con datos sanitizados
        movimiento = Movimiento(
            producto_id=producto_id,
            usuario_id=current_user.id,
            tipo=tipo,
            cantidad=cantidad,
            cantidad_anterior=cantidad_anterior,
            cantidad_nueva=cantidad_nueva,
            comentario=escape(comentario).strip() if comentario else comentario,
            referencia=escape(referencia).strip() if referencia else referencia
        )
        
        # Actualizar stock del producto
        producto.cantidad = cantidad_nueva
        
        db.session.add(movimiento)
        db.session.commit()
        
        registrar_log_auditoria('Registro de movimiento', 'movimientos', movimiento.id)
        flash(f'Movimiento registrado correctamente.', 'success')
        return redirect(url_for('views.lista_movimientos'))
    
    # GET: Mostrar formulario
    productos = Producto.query.order_by(Producto.nombre).all()
    
    # Si se proporciona un código de barras, buscar el producto
    codigo_barras = request.args.get('codigo')
    producto_seleccionado = None
    if codigo_barras:
        producto_seleccionado = Producto.query.filter_by(codigo=codigo_barras).first()
        if not producto_seleccionado:
            flash(f'No se encontró ningún producto con el código {codigo_barras}.', 'warning')
    
    return render_template('movimientos/nuevo.html', 
                          productos=productos,
                          tipos_movimiento=TipoMovimiento,
                          producto_seleccionado=producto_seleccionado)

@views_bp.route('/movimientos/escanear', methods=['GET', 'POST'])
@login_required
def escanear_codigo():
    """
    Escanea un código de barras usando la cámara
    """
    if request.method == 'POST':
        # Procesar imagen de la cámara
        if 'imagen' not in request.files:
            flash('No se recibió ninguna imagen.', 'danger')
            return redirect(url_for('views.escanear_codigo'))
        
        imagen = request.files['imagen']
        if not imagen.filename:
            flash('No se seleccionó ninguna imagen.', 'danger')
            return redirect(url_for('views.escanear_codigo'))
        
        # Procesar código de barras
        codigo = procesar_codigo_barras(imagen)
        
        if codigo:
            # Buscar producto por código
            producto = Producto.query.filter_by(codigo=codigo).first()
            
            if producto:
                # Redirigir al formulario de movimiento con el producto seleccionado
                return redirect(url_for('views.nuevo_movimiento', codigo=codigo))
            else:
                # Redirigir al formulario de nuevo producto con el código prellenado
                return redirect(url_for('views.nuevo_producto', codigo=codigo))
        else:
            flash('No se pudo detectar ningún código de barras.', 'warning')
    
    return render_template('movimientos/escanear.html')

# ---- GESTION DE CATEGORIAS ----
# Clasificacion de productos

@views_bp.route('/categorias')
@login_required
def lista_categorias():
    """
    Lista de categorías
    """
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('categorias/lista.html', categorias=categorias)

@views_bp.route('/categorias/nueva', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def nueva_categoria():
    """
    Crea una nueva categoría
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        if not nombre:
            flash('Por favor ingrese un nombre para la categoría.', 'warning')
            return render_template('categorias/nueva.html')
        
        # Verificar si ya existe
        if Categoria.query.filter_by(nombre=nombre).first():
            flash('Ya existe una categoría con este nombre.', 'danger')
            return render_template('categorias/nueva.html')
        
        # Crear categoria con datos sanitizados
        categoria = Categoria(
            nombre=escape(nombre).strip() if nombre else nombre,
            descripcion=escape(descripcion).strip() if descripcion else descripcion
        )
        db.session.add(categoria)
        db.session.commit()
        
        registrar_log_auditoria('Creación de categoría', 'categorias', categoria.id)
        flash(f'Categoría {nombre} creada correctamente.', 'success')
        return redirect(url_for('views.lista_categorias'))
    
    return render_template('categorias/nueva.html')

@views_bp.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def editar_categoria(id):
    """
    Edita una categoría existente
    """
    categoria = Categoria.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        if not nombre:
            flash('Por favor ingrese un nombre para la categoría.', 'warning')
            return render_template('categorias/editar.html', categoria=categoria)
        
        # Verificar si ya existe otro con el mismo nombre
        existente = Categoria.query.filter_by(nombre=nombre).first()
        if existente and existente.id != id:
            flash('Ya existe otra categoría con este nombre.', 'danger')
            return render_template('categorias/editar.html', categoria=categoria)
        
        # Actualizar categoria con datos sanitizados
        categoria.nombre = escape(nombre).strip() if nombre else nombre
        categoria.descripcion = escape(descripcion).strip() if descripcion else descripcion
        db.session.commit()
        
        registrar_log_auditoria('Actualización de categoría', 'categorias', categoria.id)
        flash(f'Categoría {nombre} actualizada correctamente.', 'success')
        return redirect(url_for('views.lista_categorias'))
    
    return render_template('categorias/editar.html', categoria=categoria)

@views_bp.route('/categorias/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
@no_maestro_carga
def eliminar_categoria(id):
    """
    Elimina una categoría (solo administradores)
    """
    categoria = Categoria.query.get_or_404(id)
    
    # Verificar si tiene productos asociados
    if Producto.query.filter_by(categoria_id=id).first():
        flash('No se puede eliminar la categoría porque tiene productos asociados.', 'danger')
        return redirect(url_for('views.lista_categorias'))
    
    nombre = categoria.nombre
    db.session.delete(categoria)
    db.session.commit()
    
    registrar_log_auditoria('Eliminación de categoría', 'categorias', id, f'Categoría: {nombre}')
    flash(f'Categoría {nombre} eliminada correctamente.', 'success')
    return redirect(url_for('views.lista_categorias'))

# ---- GESTION DE PROVEEDORES ----
# Datos de contacto para compras

@views_bp.route('/proveedores')
@login_required
def lista_proveedores():
    """
    Lista de proveedores
    """
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('proveedores/lista.html', proveedores=proveedores)

@views_bp.route('/proveedores/nuevo', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def nuevo_proveedor():
    """
    Crea un nuevo proveedor
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        contacto = request.form.get('contacto')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')
        
        if not nombre:
            flash('Por favor ingrese un nombre para el proveedor.', 'warning')
            return render_template('proveedores/nuevo.html')
        
        # Crear proveedor con datos sanitizados
        proveedor = Proveedor(
            nombre=escape(nombre).strip() if nombre else nombre,
            contacto=escape(contacto).strip() if contacto else contacto,
            telefono=escape(telefono).strip() if telefono else telefono,
            email=escape(email).strip() if email else email,
            direccion=escape(direccion).strip() if direccion else direccion
        )
        db.session.add(proveedor)
        db.session.commit()
        
        registrar_log_auditoria('Creación de proveedor', 'proveedores', proveedor.id)
        flash(f'Proveedor {nombre} creado correctamente.', 'success')
        return redirect(url_for('views.lista_proveedores'))
    
    return render_template('proveedores/nuevo.html')

@views_bp.route('/proveedores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def editar_proveedor(id):
    """
    Edita un proveedor existente
    """
    proveedor = Proveedor.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        contacto = request.form.get('contacto')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')
        
        if not nombre:
            flash('Por favor ingrese un nombre para el proveedor.', 'warning')
            return render_template('proveedores/editar.html', proveedor=proveedor)
        
        # Actualizar proveedor con datos sanitizados
        proveedor.nombre = escape(nombre).strip() if nombre else nombre
        proveedor.contacto = escape(contacto).strip() if contacto else contacto
        proveedor.telefono = escape(telefono).strip() if telefono else telefono
        proveedor.email = escape(email).strip() if email else email
        proveedor.direccion = escape(direccion).strip() if direccion else direccion
        db.session.commit()
        
        registrar_log_auditoria('Actualización de proveedor', 'proveedores', proveedor.id)
        flash(f'Proveedor {nombre} actualizado correctamente.', 'success')
        return redirect(url_for('views.lista_proveedores'))
    
    return render_template('proveedores/editar.html', proveedor=proveedor)

@views_bp.route('/proveedores/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
@no_maestro_carga
def eliminar_proveedor(id):
    """
    Elimina un proveedor (solo administradores)
    """
    proveedor = Proveedor.query.get_or_404(id)
    
    # Verificar si tiene productos asociados
    if Producto.query.filter_by(proveedor_id=id).first():
        flash('No se puede eliminar el proveedor porque tiene productos asociados.', 'danger')
        return redirect(url_for('views.lista_proveedores'))
    
    nombre = proveedor.nombre
    db.session.delete(proveedor)
    db.session.commit()
    
    registrar_log_auditoria('Eliminación de proveedor', 'proveedores', id, f'Proveedor: {nombre}')
    flash(f'Proveedor {nombre} eliminado correctamente.', 'success')
    return redirect(url_for('views.lista_proveedores'))

# ---- IMPORTACION Y EXPORTACION ----
# Carga masiva de productos desde/hacia CSV

@views_bp.route('/importar', methods=['GET', 'POST'])
@login_required
def importar_productos():
    """
    Importa productos desde un archivo CSV
    """
    if request.method == 'POST':
        # Verificar si se subió un archivo
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo.', 'danger')
            return redirect(url_for('views.importar_productos'))
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            flash('No se seleccionó ningún archivo.', 'danger')
            return redirect(url_for('views.importar_productos'))
        
        if not allowed_file(archivo.filename, ['csv']):
            flash('Formato de archivo no permitido. Use CSV.', 'danger')
            return redirect(url_for('views.importar_productos'))
        
        # Procesar archivo CSV
        try:
            # Leer CSV
            stream = io.StringIO(archivo.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            # Contadores para el resumen
            total = 0
            creados = 0
            actualizados = 0
            errores = 0
            
            for row in csv_reader:
                total += 1
                try:
                    # Verificar campos obligatorios
                    if not row.get('codigo') or not row.get('nombre'):
                        errores += 1
                        continue
                    
                    # Buscar si el producto ya existe
                    producto = Producto.query.filter_by(codigo=row['codigo']).first()
                    
                    # Buscar categoría
                    categoria = None
                    if row.get('categoria'):
                        categoria = Categoria.query.filter_by(nombre=row['categoria']).first()
                        if not categoria:
                            # Crear categoría si no existe
                            categoria = Categoria(nombre=row['categoria'])
                            db.session.add(categoria)
                            db.session.flush()  # Para obtener el ID
                    
                    # Buscar proveedor
                    proveedor = None
                    if row.get('proveedor'):
                        proveedor = Proveedor.query.filter_by(nombre=row['proveedor']).first()
                        if not proveedor:
                            # Crear proveedor si no existe
                            proveedor = Proveedor(nombre=row['proveedor'])
                            db.session.add(proveedor)
                            db.session.flush()  # Para obtener el ID
                    
                    # Procesar fecha de vencimiento
                    fecha_vencimiento = None
                    if row.get('fecha_vencimiento'):
                        try:
                            fecha_vencimiento = datetime.strptime(row['fecha_vencimiento'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    if producto:
                        # Actualizar producto existente
                        producto.nombre = row['nombre']
                        if row.get('descripcion'):
                            producto.descripcion = row['descripcion']
                        if categoria:
                            producto.categoria_id = categoria.id
                        if row.get('ubicacion'):
                            producto.ubicacion = row['ubicacion']
                        if row.get('precio'):
                            try:
                                producto.precio = float(row['precio'])
                            except ValueError:
                                pass
                        if proveedor:
                            producto.proveedor_id = proveedor.id
                        if fecha_vencimiento:
                            producto.fecha_vencimiento = fecha_vencimiento
                        if row.get('stock_minimo'):
                            try:
                                producto.stock_minimo = int(row['stock_minimo'])
                            except ValueError:
                                pass
                        
                        actualizados += 1
                    else:
                        # Crear nuevo producto
                        nuevo_producto = Producto(
                            codigo=row['codigo'],
                            nombre=row['nombre'],
                            descripcion=row.get('descripcion', ''),
                            categoria_id=categoria.id if categoria else None,
                            ubicacion=row.get('ubicacion', ''),
                            cantidad=0,
                            precio=float(row.get('precio', 0)) if row.get('precio') else 0,
                            proveedor_id=proveedor.id if proveedor else None,
                            fecha_vencimiento=fecha_vencimiento,
                            stock_minimo=int(row.get('stock_minimo', 5)) if row.get('stock_minimo') else 5
                        )
                        db.session.add(nuevo_producto)
                        creados += 1
                        
                        # Si se especifica cantidad inicial
                        if row.get('cantidad'):
                            try:
                                cantidad = int(row['cantidad'])
                                if cantidad > 0:
                                    db.session.flush()  # Para obtener el ID del nuevo producto
                                    
                                    # Registrar movimiento inicial
                                    movimiento = Movimiento(
                                        producto_id=nuevo_producto.id,
                                        usuario_id=current_user.id,
                                        tipo=TipoMovimiento.INICIAL,
                                        cantidad=cantidad,
                                        cantidad_anterior=0,
                                        cantidad_nueva=cantidad,
                                        comentario='Carga inicial por importación CSV'
                                    )
                                    db.session.add(movimiento)
                                    
                                    # Actualizar cantidad del producto
                                    nuevo_producto.cantidad = cantidad
                            except ValueError:
                                pass
                
                except Exception as e:
                    errores += 1
                    current_app.logger.error(f"Error al procesar fila CSV: {str(e)}")
            
            # Confirmar cambios
            db.session.commit()
            
            registrar_log_auditoria('Importación de productos', 
                                   detalles=f'Total: {total}, Creados: {creados}, Actualizados: {actualizados}, Errores: {errores}')
            
            flash(f'Importación completada. Total: {total}, Creados: {creados}, Actualizados: {actualizados}, Errores: {errores}', 'success')
            return redirect(url_for('views.lista_productos'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error en importación CSV: {str(e)}")
            flash(f'Error al procesar el archivo: {str(e)}', 'danger')
            return redirect(url_for('views.importar_productos'))
    
    return render_template('importar_exportar/importar.html')

@views_bp.route('/exportar', methods=['GET', 'POST'])
@login_required
def exportar_productos():
    """
    Exporta productos a un archivo CSV
    """
    if request.method == 'POST':
        try:
            # Crear archivo CSV en memoria
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Encabezados
            writer.writerow(['codigo', 'nombre', 'descripcion', 'categoria', 'ubicacion', 
                            'cantidad', 'precio', 'proveedor', 'fecha_vencimiento', 
                            'stock_minimo', 'fecha_creacion', 'fecha_actualizacion'])
            
            # Consultar productos
            productos = Producto.query.all()
            
            # Escribir datos
            for producto in productos:
                categoria = producto.categoria.nombre if producto.categoria else ''
                proveedor = producto.proveedor.nombre if producto.proveedor else ''
                fecha_vencimiento = producto.fecha_vencimiento.strftime('%Y-%m-%d') if producto.fecha_vencimiento else ''
                fecha_creacion = producto.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if producto.fecha_creacion else ''
                fecha_actualizacion = producto.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if producto.fecha_actualizacion else ''
                writer.writerow([producto.codigo, producto.nombre, producto.descripcion, categoria, producto.ubicacion, 
                                producto.cantidad, producto.precio, proveedor, fecha_vencimiento, 
                                producto.stock_minimo, fecha_creacion, fecha_actualizacion])
            
            # Preparar archivo para descargar
            output.seek(0)
            return send_file(output, as_attachment=True, download_name='productos.csv', mimetype='text/csv')
        
        except Exception as e:
            current_app.logger.error(f"Error en exportación CSV: {str(e)}")
            flash(f'Error al exportar los productos: {str(e)}', 'danger')
    
    return render_template('importar_exportar/exportar.html')

# ========================================================
# RESPALDOS Y BACKUPS
# ========================================================
@views_bp.route('/respaldos')
@login_required
@admin_required
def lista_respaldos():
    """
    Lista los archivos de respaldo disponibles.
    Solo accesible para administradores.
    """
    import glob
    
    backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
    archivos = []
    
    if os.path.exists(backup_dir):
        for archivo in glob.glob(os.path.join(backup_dir, '*')):
            if os.path.isfile(archivo):
                stat = os.stat(archivo)
                archivos.append({
                    'nombre': os.path.basename(archivo),
                    'ruta': archivo,
                    'tamano': stat.st_size,
                    'fecha': datetime.fromtimestamp(stat.st_mtime)
                })
    
    # Ordenar por fecha descendente
    archivos.sort(key=lambda x: x['fecha'], reverse=True)
    
    return render_template('respaldos/lista.html', archivos=archivos)

@views_bp.route('/respaldos/crear', methods=['POST'])
@login_required
@admin_required
def crear_respaldo():
    """
    Crea un respaldo manual de la base de datos.
    """
    try:
        tipo = request.form.get('tipo', 'completo')
        archivo = generar_respaldo(tipo=tipo)
        
        if archivo:
            registrar_log_auditoria('Creacion de respaldo', detalles=f'Tipo: {tipo}')
            flash(f'Respaldo creado: {os.path.basename(archivo)}', 'success')
        else:
            flash('Error al crear respaldo.', 'danger')
            
    except Exception as e:
        current_app.logger.error(f"Error al crear respaldo: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('views.lista_respaldos'))

@views_bp.route('/respaldos/descargar/<path:filename>')
@login_required
@admin_required
def descargar_respaldo(filename):
    """
    Descarga un archivo de respaldo.
    """
    try:
        # Obtener ruta absoluta
        backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
        filepath = os.path.join(backup_dir, os.path.basename(filename))
        
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )
        else:
            flash('Archivo no encontrado.', 'danger')
            
    except Exception as e:
        flash(f'Error al descargar: {str(e)}', 'danger')
    
    return redirect(url_for('views.lista_respaldos'))

@views_bp.route('/respaldos/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_respaldo():
    """
    Elimina un archivo de respaldo.
    """
    try:
        filename = request.form.get('filename')
        backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
        filepath = os.path.join(backup_dir, os.path.basename(filename))
        
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f'Respaldo eliminado: {filename}', 'success')
        else:
            flash('Archivo no encontrado.', 'danger')
            
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('views.lista_respaldos'))

# ========================================================
# ESTADO DEL SISTEMA Y CONECTIVIDAD
# ========================================================
@views_bp.route('/estado')
@login_required
def estado_sistema():
    """
    API para obtener el estado del sistema y conectividad.
    """
    info = obtener_informacion_red()
    
    # Agregar info de la base de datos
    from .models import db
    from sqlalchemy import text
    
    try:
        db.session.execute(text('SELECT 1'))
        db_status = 'conectada'
    except:
        db_status = 'error'
    
    info['base_datos'] = db_status
    
    return jsonify(info)

@views_bp.route('/info')
@login_required
def info_sistema():
    """
    Pagina de informacion del sistema.
    """
    info = obtener_informacion_red()
    
    # Agregar stats
    info['total_productos'] = Producto.query.count()
    info['total_movimientos'] = Movimiento.query.count()
    info['usuarios_activos'] = Usuario.query.filter_by(activo=True).count()
    
    return render_template('sistema/info.html', info=info)

# ========================================================
# GESTION DE REPUESTOS
# ========================================================

@views_bp.route('/repuestos')
@login_required
def lista_repuestos():
    """
    Lista de artículos con filtros y búsqueda
    """
    busqueda = request.args.get('busqueda', '')
    tipo = request.args.get('tipo', '')
    
    query = Repuesto.query
    
    if busqueda:
        query = query.filter(Repuesto.descripcion.ilike(f'%{busqueda}%') | Repuesto.marca.ilike(f'%{busqueda}%'))
        
    if tipo:
        query = query.filter(Repuesto.tipo == tipo)
        
    repuestos = paginar_resultados(
        query.order_by(Repuesto.descripcion),
        page=request.args.get('page', 1, type=int),
        per_page=20
    )
    
    return render_template('repuestos/lista.html', 
                           repuestos=repuestos,
                           busqueda=busqueda,
                           tipo_actual=tipo)

@views_bp.route('/repuestos/nuevo', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def nuevo_repuesto():
    """
    Crea un nuevo artículo
    """
    if request.method == 'POST':
        descripcion = request.form.get('descripcion')
        marca = request.form.get('marca')
        cantidad = request.form.get('cantidad', type=int, default=0)
        precio_compra = request.form.get('precio_compra', type=float, default=0.0)
        ganancia_porcentaje = request.form.get('ganancia_porcentaje', type=float, default=30.0)
        tipo = request.form.get('tipo', 'Propio (Reventa)')
        proveedor_id = request.form.get('proveedor_id', type=int)
        
        if not descripcion:
            flash('La descripción es obligatoria.', 'warning')
            proveedores = Proveedor.query.all()
            return render_template('repuestos/formulario.html', 
                                   proveedores=proveedores,
                                   repuesto=None)
        
        nuevo = Repuesto(
            descripcion=descripcion,
            marca=marca,
            cantidad=cantidad,
            precio_compra=precio_compra,
            ganancia_porcentaje=ganancia_porcentaje,
            tipo=tipo,
            proveedor_id=proveedor_id
        )
        
        nuevo.calcular_precio_venta()
        db.session.add(nuevo)
        db.session.commit()
        
        registrar_log_auditoria('Creación de artículo', 'repuestos', nuevo.id)
        flash(f'Artículo {descripcion} creado correctamente.', 'success')
        return redirect(url_for('views.lista_repuestos'))
        
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('repuestos/formulario.html', 
                           proveedores=proveedores,
                           repuesto=None)

@views_bp.route('/repuestos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@no_maestro_carga
def editar_repuesto(id):
    """
    Edita un artículo existente
    """
    repuesto = Repuesto.query.get_or_404(id)
    
    if request.method == 'POST':
        repuesto.descripcion = request.form.get('descripcion')
        repuesto.marca = request.form.get('marca')
        repuesto.cantidad = request.form.get('cantidad', type=int, default=0)
        repuesto.precio_compra = request.form.get('precio_compra', type=float, default=0.0)
        repuesto.ganancia_porcentaje = request.form.get('ganancia_porcentaje', type=float, default=30.0)
        repuesto.tipo = request.form.get('tipo')
        repuesto.proveedor_id = request.form.get('proveedor_id', type=int)
        
        repuesto.calcular_precio_venta()
        db.session.commit()
        
        registrar_log_auditoria('Actualización de artículo', 'repuestos', repuesto.id)
        flash(f'Artículo {repuesto.descripcion} actualizado.', 'success')
        return redirect(url_for('views.lista_repuestos'))
        
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('repuestos/formulario.html', 
                           proveedores=proveedores,
                           repuesto=repuesto)

@views_bp.route('/repuestos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
@no_maestro_carga
def eliminar_repuesto(id):
    """
    Elimina un artículo (solo administradores)
    """
    repuesto = Repuesto.query.get_or_404(id)
    descripcion = repuesto.descripcion
    
    db.session.delete(repuesto)
    db.session.commit()
    
    registrar_log_auditoria('Eliminación de artículo', 'repuestos', id, f'Artículo: {descripcion}')
    flash(f'Artículo {descripcion} eliminado.', 'success')
    return redirect(url_for('views.lista_repuestos'))

# ========================================================
# MANTENIMIENTO Y CONFIGURACION
# ========================================================

@views_bp.route('/mantenimiento')
@login_required
@admin_required
def mantenimiento():
    """
    Panel de mantenimiento del sistema (Backups y Reparación)
    """
    from .utils import verificar_integridad_base_datos
    integridad = verificar_integridad_base_datos()
    
    # Obtener últimos backups
    import glob
    backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
    archivos = []
    if os.path.exists(backup_dir):
        for archivo in glob.glob(os.path.join(backup_dir, '*')):
            if os.path.isfile(archivo):
                stat = os.stat(archivo)
                archivos.append({
                    'nombre': os.path.basename(archivo),
                    'fecha': datetime.fromtimestamp(stat.st_mtime)
                })
    archivos.sort(key=lambda x: x['fecha'], reverse=True)
    
    return render_template('sistema/mantenimiento.html', 
                           integridad=integridad,
                           archivos=archivos[:5])

@views_bp.route('/mantenimiento/reparar', methods=['POST'])
@login_required
@admin_required
def reparar_db():
    """
    Ejecuta la verificación de integridad y 'repara' (limpia) si es posible
    """
    from .utils import verificar_integridad_base_datos
    # Por ahora solo reportamos, pero podríamos añadir lógica de limpieza aquí
    resultado = verificar_integridad_base_datos()
    
    if resultado['integridad_ok']:
        flash('La base de datos se encuentra saludable. No se requirieron reparaciones.', 'success')
    else:
        errores = ", ".join(resultado['errores'])
        flash(f'Se detectaron problemas: {errores}. Intente realizar un backup y contactar soporte.', 'warning')
        
    registrar_log_auditoria('Reparación de DB', detalles=f'Resultado: {resultado["integridad_ok"]}')
    return redirect(url_for('views.mantenimiento'))

@views_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    """
    Gestión de configuraciones globales del sistema
    """
    from .utils import obtener_configuracion, establecer_configuracion
    
    if request.method == 'POST':
        # Guardar configuraciones
        establecer_configuracion('nombre_almacen', request.form.get('nombre_almacen', 'Almacén Central'))
        establecer_configuracion('stock_alerta_global', request.form.get('stock_alerta', '5'))
        
        flash('Configuración actualizada correctamente.', 'success')
        return redirect(url_for('views.configuracion'))
        
    configs = {
        'nombre_almacen': obtener_configuracion('nombre_almacen', 'Almacén Central'),
        'stock_alerta': obtener_configuracion('stock_alerta_global', '5')
    }
    
    return render_template('sistema/configuracion.html', configs=configs)

# ========================================================
# API DE CONTROL - SHUTDOWN
# ========================================================
@views_bp.route('/api/shutdown', methods=['POST'])
def shutdown_api():
    """
    Endpoint para solicitar el cierre del servidor.
    Usado por el WebView para cerrar la aplicación de forma segura.
    """
    import threading
    
    def delayed_shutdown():
        import time
        time.sleep(1)
        # Forzar el cierre del proceso
        import os
        os._exit(0)
    
    # Ejecutar shutdown en un thread para que la respuesta pueda enviarse
    shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
    shutdown_thread.start()
    
    return jsonify({'status': 'closing', 'message': 'Servidor cerrando...'})

@views_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint de salud para verificar que el servidor está corriendo.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# ========================================================
# EXPORTAR / IMPORTAR BASE DE DATOS
# ========================================================
@views_bp.route('/sistema/exportar-db')
@login_required
@admin_required
def exportar_db():
    """
    Exporta toda la base de datos a un archivo JSON.
    """
    try:
        from .export_import import exportar_db, VERSION_SCHEMA, NOMBRE_APP
        
        datos = exportar_db()
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"toolkinventario_backup_{timestamp}.json"
        
        # Crear respuesta JSON para descarga
        response = current_app.response_class(
            response=json.dumps(datos, indent=2, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
        response.headers['Content-Disposition'] = f'attachment; filename={nombre_archivo}'
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        
        registrar_log_auditoria('Exportación de base de datos')
        flash('Base de datos exportada correctamente.', 'success')
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exportando DB: {e}")
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('views.configuracion'))

@views_bp.route('/sistema/importar-db', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_db():
    """
    Muestra la página de importación o procesa la importación.
    """
    if request.method == 'POST':
        if 'archivo' not in request.files:
            flash('No se encontró archivo.', 'danger')
            return redirect(url_for('views.importar_db'))
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            flash('No se seleccionó archivo.', 'danger')
            return redirect(url_for('views.importar_db'))
        
        if not archivo.filename.endswith('.json'):
            flash('Solo se permiten archivos JSON.', 'danger')
            return redirect(url_for('views.importar_db'))
        
        try:
            from .export_import import importar_db, obtener_preview_importacion, ImportacionError
            
            # Leer y parsear JSON
            contenido = archivo.read()
            datos = json.loads(contenido)
            
            # Obtener preview
            preview = obtener_preview_importacion(datos)
            
            # Si hay errores fatales, mostrar
            if not preview['valido']:
                for error in preview['errores']:
                    flash(error, 'danger')
                return redirect(url_for('views.configuracion'))
            
            # Realizar importación
            resultado = importar_db(datos)
            
            registrar_log_auditoria('Importación de base de datos', 
                                   detalles=f"Registros importados: {resultado.get('resultados', {})}")
            
            flash(f"Importación exitosa: {resultado.get('mensaje', 'OK')}", 'success')
            
            if preview['advertencias']:
                for adv in preview['advertencias']:
                    flash(adv, 'warning')
            
            return redirect(url_for('views.configuracion'))
            
        except ImportacionError as e:
            flash(f'Error de importación: {str(e)}', 'danger')
            return redirect(url_for('views.configuracion'))
        except json.JSONDecodeError:
            flash('El archivo no es un JSON válido.', 'danger')
            return redirect(url_for('views.configuracion'))
        except Exception as e:
            current_app.logger.error(f"Error importando DB: {e}")
            flash(f'Error al importar: {str(e)}', 'danger')
            return redirect(url_for('views.configuracion'))
    
    # GET: Mostrar página de importación
    return render_template('sistema/importar_db.html')

@views_bp.route('/api/preview-import', methods=['POST'])
@login_required
@admin_required
def preview_import():
    """
    Obtiene una vista previa de lo que se importaría.
    """
    try:
        from .export_import import obtener_preview_importacion
        
        if 'archivo' not in request.files:
            return jsonify({'error': 'No se encontró archivo'}), 400
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        contenido = archivo.read()
        datos = json.loads(contenido)
        
        preview = obtener_preview_importacion(datos)
        
        return jsonify(preview)
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Archivo JSON inválido'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@views_bp.route('/api/info-schema', methods=['GET'])
@login_required
def info_schema():
    """
    Obtiene información del esquema actual de la BD.
    """
    try:
        from .export_import import obtener_info_esquema, VERSION_SCHEMA, NOMBRE_APP
        
        info = obtener_info_esquema()
        info['version_schema_actual'] = VERSION_SCHEMA
        info['nombre_app'] = NOMBRE_APP
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
