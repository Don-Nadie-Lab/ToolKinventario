# -*- coding: utf-8 -*-
"""
Inicializacion de la aplicacion Flask para ToolKinventario
Configura la aplicacion, la base de datos y los blueprints
"""

import os
import sys
import secrets
import stat
from datetime import timedelta, datetime
from flask import Flask, session, redirect, url_for
from flask_login import LoginManager, current_user, logout_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix

# Manejar stdout/stderr nulos en modo windowed (PyInstaller)
if getattr(sys, 'frozen', False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

# Detectar si estamos en un ejecutable compilado
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

# Inicializacion de componentes (se configuran en create_app)
csrf = CSRFProtect()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

def create_app(config=None):
    """
    Crea y configura la aplicacion Flask
    
    Args:
        config: Configuracion opcional para la aplicacion
        
    Returns:
        Aplicacion Flask configurada
    """
    # Importar aqui para evitar conflictos
    from app.models import db, Usuario
    from app.utils import crear_directorios_necesarios, configurar_logger
    from app.auth import auth_bp
    from app.views import views_bp
    
    # Crear la aplicacion Flask
    app = Flask(__name__, 
                static_folder=STATIC_FOLDER,
                template_folder=TEMPLATE_FOLDER)
    
    # Ruta base para la base de datos
    db_path = os.path.join(BASE_DIR, 'database', 'toolkinventario.db')
    
    # Configuracion basica - SEGURIDAD: Generar SECRET_KEY segura si no existe
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)
        print("[WARNING] SECRET_KEY not configured. Generated temporary key.")
        print("          For production, set SECRET_KEY environment variable")
    
    app.config.from_mapping(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', f'sqlite:///{db_path}'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        BACKUP_DIR=os.path.join(BASE_DIR, 'backups'),
        UPLOAD_FOLDER=os.path.join(BASE_DIR, 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB maximo para subida
        SESSION_COOKIE_SECURE=False,  # Cambiar a True en produccion con HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',  # Proteccion CSRF
        REMEMBER_COOKIE_DURATION=86400,  # 1 dia
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    
    # Sobreescribir con configuracion personalizada si se proporciona
    if config:
        app.config.from_mapping(config)
    
    # Configurar para trabajar detras de proxy si es necesario
    app.wsgi_app = ProxyFix(app.wsgi_app)
    # Session management: idle timeout
    app.permanent_session_lifetime = timedelta(minutes=15)
    @app.before_request
    def _manage_session():
        session.permanent = True
        if getattr(current_user, 'is_authenticated', False):
            now = datetime.utcnow()
            last = session.get('last_activity')
            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                    if now - last_dt > timedelta(minutes=15):
                        logout_user()
                        session.pop('last_activity', None)
                        return redirect(url_for('auth.login'))
                except Exception:
                    pass
            session['last_activity'] = now.isoformat()
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicio sesion para acceder a esta pagina.'
    login_manager.login_message_category = 'warning'
    if not app.debug:
        csrf.init_app(app)
    
    # Configuracion de correo (usar variables de entorno en produccion)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@toolkinventario.com')
    mail.init_app(app)
    
    # Crear directorios necesarios
    with app.app_context():
        crear_directorios_necesarios(app)
    
    # Configurar logger
    logger = configurar_logger(app)
    
    # Funcion para cargar usuario en Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    
    # Crear la base de datos si no existe
    with app.app_context():
        db.create_all()
        
        # SEGURIDAD: Establecer permisos restrictivos en la base de datos
        if os.path.exists(db_path):
            try:
                # Solo usuario propietario puede leer/escribir (600)
                os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)
            except Exception as e:
                app.logger.warning(f"No se pudieron establecer permisos seguros en DB: {e}")
        
        # Verificar si existe un usuario administrador
        from app.utils import crear_usuario_admin_inicial
        crear_usuario_admin_inicial()
    
    return app
