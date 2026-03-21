# -*- coding: utf-8 -*-
"""
==========================================================
CAPA DE DOMINIO - Modelos de Datos
==========================================================
Esta capa contiene las entidades del negocio y sus reglas.
No depende de la base de datos ni del framework web.

Entidades:
- Usuario: Gestion de acceso al sistema
- Categoria: Clasificacion de productos
- Proveedor: Gestion de proveedores
- Producto: Articulos del inventario
- Movimiento: Registro de entradas/salidas
- LogAuditoria: Trazabilidad de acciones
- Configuracion: Parametros del sistema
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ========================================================
# DEFINICION DE ROLES - Control de acceso
# ========================================================
class Rol:
    """Constantes para roles de usuario"""
    ADMIN = 'admin'           # Acceso total al sistema
    USUARIO = 'usuario'        # Operador standard
    MAESTRO_CARGA = 'maestro_carga'  # Solo cargas masivas

# ========================================================
# ENTIDAD: USUARIO
# ========================================================
class Usuario(db.Model, UserMixin):
    """
    Representa un usuario del sistema.
    Maneja autenticacion y permisos.
    """
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=Rol.USUARIO)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    ultimo_acceso = db.Column(db.DateTime)
    
    # Preguntas de seguridad
    pregunta_seguridad_1 = db.Column(db.String(200))
    respuesta_seguridad_1 = db.Column(db.String(200))
    pregunta_seguridad_2 = db.Column(db.String(200))
    respuesta_seguridad_2 = db.Column(db.String(200))
    
    # Relaciones
    movimientos = db.relationship('Movimiento', backref='usuario', lazy=True)
    
    def set_password(self, password):
        """Genera hash seguro de la contraseña"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Verifica la contrasena contra el hash almacenado"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica si tiene rol de administrador"""
        return self.rol == Rol.ADMIN
    
    def is_maestro_carga(self):
        """Verifica si es maestro de carga (restringido)"""
        return self.rol == Rol.MAESTRO_CARGA
    
    def puede_eliminar(self):
        """Determina si puede eliminar registros"""
        return self.rol in [Rol.ADMIN]
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

# ========================================================
# ENTIDAD: CATEGORIA
# ========================================================
class Categoria(db.Model):
    """
    Categorias para clasificar productos.
    Permite filtrado y organizacion del inventario.
    """
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    
    # Relacion con productos
    productos = db.relationship('Producto', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'

# ========================================================
# ENTIDAD: PROVEEDOR
# ========================================================
class Proveedor(db.Model):
    """
    Proveedores de productos.
    Mantiene datos de contacto para compras.
    """
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    
    # Relacion con productos
    productos = db.relationship('Producto', backref='proveedor', lazy=True)
    
    def __repr__(self):
        return f'<Proveedor {self.nombre}>'

# ========================================================
# ENTIDAD: PRODUCTO
# ========================================================
class Producto(db.Model):
    """
    Productos del inventario.
    Entidad central del sistema con reglas de negocio.
    """
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    ubicacion = db.Column(db.String(50))
    cantidad = db.Column(db.Integer, default=0)
    precio = db.Column(db.Float, default=0.0)
    costo = db.Column(db.Float, default=0.0)  # Costo de adquisicion
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    fecha_vencimiento = db.Column(db.Date)
    stock_minimo = db.Column(db.Integer, default=5)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacion con movimientos
    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)
    
    # ========================================================
    # REGLAS DE NEGOCIO - Metodos de dominio
    # ========================================================
    
    def stock_bajo(self):
        """Verifica si esta por debajo del stock minimo"""
        return self.cantidad <= self.stock_minimo
    
    def sin_stock(self):
        """Verifica si no hay unidades disponibles"""
        return self.cantidad <= 0
    
    def valor_inventario(self):
        """Calcula el valor total en inventario"""
        return self.cantidad * self.precio
    
    def margen_utilidad(self):
        """Calcula el porcentaje de ganancia"""
        if self.costo > 0:
            return ((self.precio - self.costo) / self.costo) * 100
        return 0
    
    def puede_vender(self, cantidad):
        """Verifica si hay stock suficiente para venta"""
        return self.cantidad >= cantidad
    
    def esta_vencido(self):
        """Verifica si el producto esta vencido"""
        if self.fecha_vencimiento:
            return self.fecha_vencimiento < datetime.now().date()
        return False
    
    def proximo_vencer(self, dias=30):
        """Verifica si vence en los proximos dias"""
        if self.fecha_vencimiento:
            from datetime import timedelta
            return self.fecha_vencimiento <= (datetime.now().date() + timedelta(days=dias))
        return False
    
    def __repr__(self):
        return f'<Producto {self.codigo}: {self.nombre}>'

# ========================================================
# DEFINICION DE TIPOS DE MOVIMIENTO
# ========================================================
class TipoMovimiento:
    """Constantes para tipos de movimiento"""
    ENTRADA = 'entrada'      # Compra, donacion, produccion
    SALIDA = 'salida'        # Venta, mermas, consumo
    AJUSTE = 'ajuste'        # Correccion de inventario
    INICIAL = 'inicial'       # Carga inicial

# ========================================================
# ENTIDAD: MOVIMIENTO
# ========================================================
class Movimiento(db.Model):
    """
    Registro de movimientos de inventario.
    Mantiene trazabilidad completa de entradas y salidas.
    """
    __tablename__ = 'movimientos'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    cantidad_nueva = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    comentario = db.Column(db.Text)
    referencia = db.Column(db.String(50))  # Factura, orden, etc.
    
    def __repr__(self):
        return f'<Movimiento {self.id}: {self.tipo} {self.cantidad} unidades>'

# ========================================================
# ENTIDAD: LOG DE AUDITORIA
# ========================================================
class LogAuditoria(db.Model):
    """
    Registro de auditoria.
    cumple normativas de trazabilidad y cumplimiento.
    """
    __tablename__ = 'log_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    accion = db.Column(db.String(50), nullable=False)
    tabla = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    detalles = db.Column(db.Text)
    ip = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.now)
    
    usuario = db.relationship('Usuario', backref='logs', lazy=True)
    
    def __repr__(self):
        return f'<LogAuditoria {self.id}: {self.accion}>'

# ========================================================
# ENTIDAD: CONFIGURACION
# ========================================================
class Configuracion(db.Model):
    """
    Configuraciones del sistema.
    Almacena parametros ajustables.
    """
    __tablename__ = 'configuraciones'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Configuracion {self.clave}>'

# ========================================================
# ENTIDAD: REPUESTO
# ========================================================
class Repuesto(db.Model):
    """
    Representa un repuesto o autoparte en el inventario.
    Incluye lógica de cálculo de precios y tipo de posesión.
    """
    __tablename__ = 'repuestos'
    
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    marca = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, default=0)
    precio_compra = db.Column(db.Float, default=0.0)
    ganancia_porcentaje = db.Column(db.Float, default=30.0) # Porcentaje de ganancia por defecto
    precio_venta = db.Column(db.Float, default=0.0)
    tipo = db.Column(db.String(50), default='Propio (Reventa)') # 'Propio (Reventa)' o 'Consignación'
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    proveedor = db.relationship('Proveedor', backref='repuestos', lazy=True)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def calcular_precio_venta(self):
        """Calcula el precio de venta basado en el costo y margen"""
        if self.precio_compra and self.ganancia_porcentaje:
            self.precio_venta = self.precio_compra * (1 + (self.ganancia_porcentaje / 100))
        return self.precio_venta
    
    def save_precio_venta(self):
        """Calcula y guarda el precio de venta en la base de datos"""
        self.calcular_precio_venta()
        if self.id is not None:
            from .models import db
            db.session.commit()

    def __repr__(self):
        return f'<Repuesto {self.descripcion} ({self.marca})>'
