# -*- coding: utf-8 -*-
"""
==========================================================
CAPA DE APLICACION - Autenticacion y Autorizacion
==========================================================
Maneja login, logout, roles y permisos.

Decoradores:
- admin_required: Restringe a administradores
- no_maestro_carga: Evita que restricted users eliminen
- registrar_log_auditoria: Registra acciones para trazabilidad
"""

from datetime import datetime
from functools import wraps
import os
import secrets
import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from markupsafe import escape
from urllib.parse import urlparse

from .models import db, Usuario, Rol, LogAuditoria

# Blueprint para rutas de autenticacion
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ========================================================
# DECORADORES DE AUTORIZACION
# ========================================================
def admin_required(f):
    """
    Decorador: Restringe acceso solo a administradores.
    Uso: @admin_required en rutas sensibles.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def no_maestro_carga(f):
    """
    Decorador: Evita que maestros de carga eliminen registros.
    Implementa control interno anti-fraude.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_maestro_carga():
            flash('No tiene permisos para realizar esta accion.', 'danger')
            return redirect(url_for('views.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def registrar_log_auditoria(accion, tabla=None, registro_id=None, detalles=None):
    """
    Registra accion en el log de auditoria.
    Args:
        accion: Descripcion de la accion
        tabla: Tabla afectada (productos, usuarios, etc.)
        registro_id: ID del registro
        detalles: Informacion adicional
    """
    if current_user.is_authenticated:
        log = LogAuditoria(
            usuario_id=current_user.id,
            accion=accion,
            tabla=tabla,
            registro_id=registro_id,
            detalles=detalles,
            ip=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

# ========================================================
# RUTAS DE AUTENTICACION
# ========================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pantalla de inicio de sesion con clave de seguridad"""
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    
    # Obtener clave de seguridad desde config o variable de entorno
    clave_seguridad = current_app.config.get('CLAVE_SEGURIDAD', 
                                              os.environ.get('CLAVE_SEGURIDAD', ''))
    requiere_clave = bool(clave_seguridad)
    
    if request.method == 'POST':
        username = escape(request.form.get('username', ''))
        password = request.form.get('password', '')
        clave_ingresada = request.form.get('clave_seguridad', '')
        
        # SEGURIDAD: Validar formato de username
        if not username or not password:
            flash('Complete usuario y contrasena.', 'warning')
            return render_template('auth/login.html', requiere_clave=requiere_clave)
        
        # Validar que username solo contenga caracteres seguros
        # Permite: letras, numeros, guiones bajos y guiones (3-50 caracteres)
        if not username.replace('_', '').replace('-', '').isalnum():
            flash('Nombre de usuario invalido.', 'danger')
            return render_template('auth/login.html', requiere_clave=requiere_clave)
        
        if len(username) < 3 or len(username) > 50:
            flash('El usuario debe tener entre 3 y 50 caracteres.', 'danger')
            return render_template('auth/login.html', requiere_clave=requiere_clave)
        
        # Verificar clave de seguridad si está configurada
        if requiere_clave and clave_ingresada != clave_seguridad:
            flash('Clave de seguridad incorrecta.', 'danger')
            return render_template('auth/login.html', requiere_clave=requiere_clave)
        
        user = Usuario.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.activo:
                flash('Cuenta desactivada.', 'danger')
                return render_template('auth/login.html', requiere_clave=requiere_clave)
            
            login_user(user)
            session.permanent = True
            flash(f'Bienvenido, {user.nombre}!', 'success')
            
            # SEGURIDAD: Forzar cambio de contrasena por defecto
            if user.username == 'admin' and user.check_password('admin123'):
                flash('Por seguridad, cambie la contrasena por defecto', 'warning')
                return redirect(url_for('auth.perfil'))
            
            # Redirigir a la pagina intentada o al dashboard
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('views.dashboard')
            return redirect(next_page)
        else:
            flash('Usuario o contrasena incorrectos.', 'danger')
    
    return render_template('auth/login.html', requiere_clave=requiere_clave)

@auth_bp.route('/logout')
@login_required
def logout():
    """Cierra la sesion del usuario"""
    logout_user()
    flash('Sesion cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout-shutdown')
@login_required
def logout_shutdown():
    """Cierra sesion y apaga el servidor"""
    import subprocess
    import os
    
    logout_user()
    
    # Ejecutar script para apagar servidor (OCULTO)
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'apagar_servidor.ps1')
    
    if os.path.exists(script_path):
        try:
            # Usar subprocess con CREATE_NO_WINDOW para ejecutar oculto
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.Popen(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', script_path],
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
        except Exception:
            pass
    
    return render_template('auth/servidor_apagado.html')

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Edicion de perfil de usuario"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not nombre or not email:
            flash('Complete los campos obligatorios.', 'warning')
            return render_template('auth/perfil.html')
        
        # Verificar email duplicado
        if email != current_user.email:
            existente = Usuario.query.filter_by(email=email).first()
            if existente and existente.id != current_user.id:
                flash('Email ya en uso.', 'danger')
                return render_template('auth/perfil.html')
        
        current_user.nombre = nombre
        current_user.email = email
        
        # Cambio de contrasena
        if password:
            if password != password_confirm:
                flash('Contrasenas no coinciden.', 'danger')
                return render_template('auth/perfil.html')
            current_user.set_password(password)
            flash('Contrasena actualizada.', 'success')
        
        # Guardar preguntas de seguridad
        pregunta1 = request.form.get('pregunta_seguridad_1')
        respuesta1 = request.form.get('respuesta_seguridad_1')
        pregunta2 = request.form.get('pregunta_seguridad_2')
        respuesta2 = request.form.get('respuesta_seguridad_2')
        
        if pregunta1 and respuesta1:
            current_user.pregunta_seguridad_1 = pregunta1
            current_user.respuesta_seguridad_1 = respuesta1
        if pregunta2 and respuesta2:
            current_user.pregunta_seguridad_2 = pregunta2
            current_user.respuesta_seguridad_2 = respuesta2
        
        db.session.commit()
        registrar_log_auditoria('Actualizacion de perfil')
        flash('Perfil actualizado.', 'success')
        
    return render_template('auth/perfil.html')

# ========================================================
# GESTION DE USUARIOS (Solo Admin)
# ========================================================
@auth_bp.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    """Lista todos los usuarios del sistema"""
    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)

@auth_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_usuario():
    """Crea un nuevo usuario del sistema"""
    if request.method == 'POST':
        username = request.form.get('username')
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol')
        
        if not username or not nombre or not email or not password or not rol:
            flash('Complete todos los campos.', 'warning')
            return render_template('auth/nuevo_usuario.html')
        
        if Usuario.query.filter_by(username=username).first():
            flash('Usuario ya existe.', 'danger')
            return render_template('auth/nuevo_usuario.html')
        
        if Usuario.query.filter_by(email=email).first():
            flash('Email ya en uso.', 'danger')
            return render_template('auth/nuevo_usuario.html')
        
        if rol not in [Rol.ADMIN, Rol.USUARIO, Rol.MAESTRO_CARGA]:
            flash('Rol invalido.', 'danger')
            return render_template('auth/nuevo_usuario.html')
        
        nuevo_usuario = Usuario(
            username=username,
            nombre=nombre,
            email=email,
            rol=rol
        )
        nuevo_usuario.set_password(password)
        
        # Guardar preguntas de seguridad
        pregunta1 = request.form.get('pregunta_seguridad_1')
        respuesta1 = request.form.get('respuesta_seguridad_1')
        pregunta2 = request.form.get('pregunta_seguridad_2')
        respuesta2 = request.form.get('respuesta_seguridad_2')
        
        if pregunta1 and respuesta1:
            nuevo_usuario.pregunta_seguridad_1 = pregunta1
            nuevo_usuario.respuesta_seguridad_1 = respuesta1
        if pregunta2 and respuesta2:
            nuevo_usuario.pregunta_seguridad_2 = pregunta2
            nuevo_usuario.respuesta_seguridad_2 = respuesta2
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        registrar_log_auditoria('Creacion de usuario', 'usuarios', nuevo_usuario.id)
        flash(f'Usuario {username} creado.', 'success')
        return redirect(url_for('auth.lista_usuarios'))
    
    return render_template('auth/nuevo_usuario.html')

@auth_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    """Edita un usuario existente"""
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        rol = request.form.get('rol')
        activo = 'activo' in request.form
        password = request.form.get('password')
        
        if not nombre or not email or not rol:
            flash('Complete los campos obligatorios.', 'warning')
            return render_template('auth/editar_usuario.html', usuario=usuario)
        
        if email != usuario.email:
            existente = Usuario.query.filter_by(email=email).first()
            if existente and existente.id != usuario.id:
                flash('Email ya en uso.', 'danger')
                return render_template('auth/editar_usuario.html', usuario=usuario)
        
        if rol not in [Rol.ADMIN, Rol.USUARIO, Rol.MAESTRO_CARGA]:
            flash('Rol invalido.', 'danger')
            return render_template('auth/editar_usuario.html', usuario=usuario)
        
        usuario.nombre = nombre
        usuario.email = email
        usuario.rol = rol
        usuario.activo = activo
        
        if password:
            usuario.set_password(password)
        
        # Guardar preguntas de seguridad
        pregunta1 = request.form.get('pregunta_seguridad_1')
        respuesta1 = request.form.get('respuesta_seguridad_1')
        pregunta2 = request.form.get('pregunta_seguridad_2')
        respuesta2 = request.form.get('respuesta_seguridad_2')
        
        if pregunta1 and respuesta1:
            usuario.pregunta_seguridad_1 = pregunta1
            usuario.respuesta_seguridad_1 = respuesta1
        if pregunta2 and respuesta2:
            usuario.pregunta_seguridad_2 = pregunta2
            usuario.respuesta_seguridad_2 = respuesta2
        
        db.session.commit()
        registrar_log_auditoria('Actualizacion de usuario', 'usuarios', usuario.id)
        flash(f'Usuario {usuario.username} actualizado.', 'success')
        return redirect(url_for('auth.lista_usuarios'))
    
    return render_template('auth/editar_usuario.html', usuario=usuario)

@auth_bp.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(id):
    """Elimina un usuario (no permite auto-eliminacion)"""
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('No puede eliminar su propio usuario.', 'danger')
        return redirect(url_for('auth.lista_usuarios'))
    
    username = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    
    registrar_log_auditoria('Eliminacion de usuario', 'usuarios', id, f'Usuario: {username}')
    flash(f'Usuario {username} eliminado.', 'success')
    return redirect(url_for('auth.lista_usuarios'))

@auth_bp.route('/auditoria')
@login_required
@admin_required
def log_auditoria():
    """Visualiza el registro de auditoria"""
    page = request.args.get('page', 1, type=int)
    logs = LogAuditoria.query.order_by(LogAuditoria.fecha.desc()).paginate(
        page=page, per_page=50, error_out=False)
    
    return render_template('auth/auditoria.html', logs=logs)

@auth_bp.route('/recuperar-clave', methods=['GET', 'POST'])
def recuperar_clave():
    """Sistema de recuperacion por preguntas de seguridad - SIN EMAIL"""
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            flash('Ingrese su nombre de usuario', 'warning')
            return render_template('auth/recuperar_clave.html')
        
        user = Usuario.query.filter_by(username=username).first()
        if not user:
            flash('Usuario no encontrado', 'danger')
            return render_template('auth/recuperar_clave.html')
        
        if not user.pregunta_seguridad_1 or not user.respuesta_seguridad_1:
            flash('Este usuario no tiene preguntas de seguridad configuradas. Contacte al administrador.', 'danger')
            return render_template('auth/recuperar_clave.html')
        
        session['recover_user_id'] = user.id
        return redirect(url_for('auth.responder_preguntas'))
    
    return render_template('auth/recuperar_clave.html')

@auth_bp.route('/responder-preguntas', methods=['GET', 'POST'])
def responder_preguntas():
    """Responder preguntas de seguridad"""
    if 'recover_user_id' not in session:
        flash('Sesion invalida. Inicie nuevamente.', 'danger')
        return redirect(url_for('auth.recuperar_clave'))
    
    user_id = session['recover_user_id']
    user = Usuario.query.get_or_404(user_id)
    
    if request.method == 'POST':
        respuesta1 = request.form.get('respuesta1', '').strip()
        respuesta2 = request.form.get('respuesta2', '').strip()
        
        if (respuesta1.lower() == user.respuesta_seguridad_1.lower() and 
            respuesta2.lower() == user.respuesta_seguridad_2.lower()):
            session['authorized_reset'] = True
            flash('Respuestas correctas. Ahora puede cambiar su contrasena.', 'success')
            return redirect(url_for('auth.cambiar_clave_recuperacion'))
        else:
            flash('Respuestas incorrectas. Intente nuevamente.', 'danger')
    
    return render_template('auth/preguntas_seguridad.html', user=user)

@auth_bp.route('/cambiar-clave-recuperacion', methods=['GET', 'POST'])
def cambiar_clave_recuperacion():
    """Cambiar contrasena despues de preguntas correctas"""
    if 'recover_user_id' not in session or not session.get('authorized_reset'):
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('auth.recuperar_clave'))
    
    user_id = session['recover_user_id']
    user = Usuario.query.get_or_404(user_id)
    
    if request.method == 'POST':
        nueva_clave = request.form.get('nueva_clave')
        confirmar_clave = request.form.get('confirmar_clave')
        
        if not nueva_clave or not confirmar_clave:
            flash('Complete ambos campos de contrasena', 'warning')
            return render_template('auth/cambiar_clave_recuperacion.html')
        
        if nueva_clave != confirmar_clave:
            flash('Las contrasenas no coinciden', 'danger')
            return render_template('auth/cambiar_clave_recuperacion.html')
        
        if len(nueva_clave) < 6:
            flash('La contrasena debe tener al menos 6 caracteres', 'danger')
            return render_template('auth/cambiar_clave_recuperacion.html')
        
        user.set_password(nueva_clave)
        db.session.commit()
        
        session.pop('recover_user_id', None)
        session.pop('authorized_reset', None)
        
        flash('Contrasena cambiada exitosamente. Ahora puede iniciar sesion.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/cambiar_clave_recuperacion.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Formulario para recuperacion con preguntas de seguridad"""
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            flash('Ingrese su nombre de usuario', 'warning')
            return render_template('auth/forgot_password.html')
        
        user = Usuario.query.filter_by(username=username).first()
        if user and user.pregunta_seguridad_1 and user.respuesta_seguridad_1:
            session['reset_user_id'] = user.id
            session['reset_step'] = 'questions'
            return redirect(url_for('auth.reset_questions'))
        else:
            flash('Usuario no encontrado o no tiene preguntas de seguridad configuradas', 'danger')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-questions', methods=['GET', 'POST'])
def reset_questions():
    """Formulario para responder preguntas de seguridad"""
    if 'reset_user_id' not in session or session.get('reset_step') != 'questions':
        flash('Sesion invalida. Inicie el proceso nuevamente.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    user_id = session['reset_user_id']
    user = Usuario.query.get_or_404(user_id)
    
    if request.method == 'POST':
        respuesta1 = request.form.get('respuesta1', '').strip().lower()
        respuesta2 = request.form.get('respuesta2', '').strip().lower()
        
        if (respuesta1 == user.respuesta_seguridad_1.lower() and 
            respuesta2 == user.respuesta_seguridad_2.lower()):
            session['reset_step'] = 'new_password'
            flash('Respuestas correctas. Ahora puede cambiar su contrasena.', 'success')
            return redirect(url_for('auth.reset_password_questions'))
        else:
            flash('Respuestas incorrectas. Intente nuevamente.', 'danger')
    
    return render_template('auth/reset_questions.html', user=user)

@auth_bp.route('/reset-password-questions', methods=['GET', 'POST'])
def reset_password_questions():
    """Formulario para cambiar contrasena despues de preguntas correctas"""
    if ('reset_user_id' not in session or 
        session.get('reset_step') != 'new_password'):
        flash('Sesion invalida. Inicie el proceso nuevamente.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    user_id = session['reset_user_id']
    user = Usuario.query.get_or_404(user_id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not password or not password_confirm:
            flash('Complete ambos campos de contrasena', 'warning')
            return render_template('auth/reset_password_questions.html')
        
        if password != password_confirm:
            flash('Las contrasenas no coinciden', 'danger')
            return render_template('auth/reset_password_questions.html')
        
        user.set_password(password)
        db.session.commit()
        
        session.pop('reset_user_id', None)
        session.pop('reset_step', None)
        
        flash('Contrasena actualizada correctamente. Ahora puede iniciar sesion.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_questions.html')
