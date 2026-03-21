#!/usr/bin/env python3
"""
Punto de entrada silencioso para ToolKinventario
Ejecuta la aplicacion sin mostrar ventana de consola
"""

import os
import sys
import logging

def setup_paths():
    """Configurar rutas correctamente para modo frozen y normal"""
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
        # En modo frozen, agregar el directorio base al path
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # En modo desarrollo, agregar el directorio del proyecto
        project_dir = os.path.dirname(BASE_DIR)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
    
    return BASE_DIR

def setup_logging(base_dir):
    """Configurar logging de manera segura"""
    try:
        logs_dir = os.path.join(base_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, 'toolkinventario_service.log')
        
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )
        return logging.getLogger()
    except Exception as e:
        logging.basicConfig(level=logging.CRITICAL)
        return logging.getLogger()

def main():
    """Funcion principal con manejo de errores"""
    base_dir = setup_paths()
    logger = setup_logging(base_dir)
    
    try:
        logger.info(f"BASE_DIR: {base_dir}")
        logger.info(f"sys.frozen: {getattr(sys, 'frozen', False)}")
        
        # Importar la app
        from app import create_app
        logger.info("App importada correctamente")
        
        app = create_app()
        logger.info("App creada correctamente")
        
        host = os.environ.get('HOST', '127.0.0.1')
        port = int(os.environ.get('PORT', 5050))
        
        logger.info(f"Iniciando servidor en {host}:{port}")
        
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
