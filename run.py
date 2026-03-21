#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada principal para ToolKinventario
Sistema de gestión de inventario local (On-Premise)
"""

import os
import sys
import socket

def setup_encoding():
    """Configurar encoding de manera segura para modo windowed"""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8', errors='replace')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8', errors='replace')

setup_encoding()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_PORT = 5050

def encontrar_puerto_disponible(puerto_inicial=5050, max_intentos=10):
    """Encuentra un puerto disponible starting from puerto_inicial."""
    for puerto in range(puerto_inicial, puerto_inicial + max_intentos):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', puerto))
                return puerto
        except OSError:
            continue
    return puerto_inicial

def obtener_ip_local():
    """Obtiene la IP local del equipo"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

from app import create_app

PUERTO_EJECUCION = None

def main():
    """Función principal para ejecutar la aplicación en modo desarrollo."""
    global PUERTO_EJECUCION
    
    def safe_print(msg=''):
        try:
            print(msg)
            if sys.stdout and hasattr(sys.stdout, 'flush'):
                sys.stdout.flush()
        except:
            pass
    
    safe_print()
    safe_print("=" * 60)
    safe_print("  ToolKinventario - Modo Desarrollo")
    safe_print("  Sistema de Gestion de Inventario")
    safe_print("=" * 60)
    safe_print()
    safe_print("  NOTA: Para modo producción, ejecute: python startup.py")
    safe_print()
    
    try:
        os.makedirs('database', exist_ok=True)
        os.makedirs('backups', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('uploads', exist_ok=True)
    except Exception as e:
        safe_print(f"Advertencia: No se pudieron crear directorios: {e}")
    
    puerto_solicitado = int(os.environ.get('PORT', DEFAULT_PORT))
    PUERTO_EJECUCION = encontrar_puerto_disponible(puerto_solicitado)
    
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    ip_local = obtener_ip_local()
    
    safe_print(f"  Servidor: http://{ip_local}:{PUERTO_EJECUCION}")
    safe_print("  Usuario: admin | Contrasena: admin123")
    safe_print("  Presione Ctrl+C para detener")
    safe_print("=" * 60)
    safe_print()
    
    try:
        app = create_app()
    except Exception as e:
        safe_print(f"Error creando aplicación: {e}")
        sys.exit(1)
    
    app.config['IP_LOCAL'] = ip_local
    app.config['PUERTO_EJECUCION'] = PUERTO_EJECUCION
    
    try:
        app.run(host=host, port=PUERTO_EJECUCION, debug=debug)
    except KeyboardInterrupt:
        safe_print()
        safe_print("Servidor detenido.")
    except Exception as e:
        safe_print(f"Error al iniciar: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
