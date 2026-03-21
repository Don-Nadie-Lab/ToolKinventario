#!/usr/bin/env python3
"""
ToolKinventario - Preparar Version Portable
Copia la carpeta completa del proyecto para uso sin instalador
"""

import os
import sys
import shutil
from pathlib import Path

def print_status(message, status="info"):
    symbols = {"info": "[INFO]", "success": "[OK]", "error": "[X]", "warning": "[!]"}
    print(f"{symbols.get(status, '[INFO]')} {message}")

def preparar_portable():
    print("")
    print("=" * 60)
    print("  ToolKinventario - Preparar Version Portable")
    print("=" * 60)
    print("")
    
    # Directorios
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(script_dir, 'dist', 'ToolKinventario')
    portable_dir = os.path.join(script_dir, 'ToolKinventario-Portable')
    
    # Verificar que existe la compilacion
    if not os.path.exists(dist_dir):
        print_status("No se encontro la compilacion en dist/ToolKinventario/", "error")
        print_status("Ejecute primero: python installer/compilar_completo.py", "info")
        return False
    
    print_status(f"Origen: {dist_dir}")
    print_status(f"Destino: {portable_dir}")
    print("")
    
    # Limpiar destino anterior si existe
    if os.path.exists(portable_dir):
        print_status("Limpiando version portable anterior...", "info")
        try:
            shutil.rmtree(portable_dir)
        except Exception as e:
            print_status(f"No se pudo limpiar: {e}", "warning")
    
    # Copiar todo
    print_status("Copiando archivos...", "info")
    
    try:
        # Copiar directorio completo
        shutil.copytree(dist_dir, portable_dir)
        print_status("Archivos copiados correctamente", "success")
    except Exception as e:
        print_status(f"Error copiando: {e}", "error")
        return False
    
    # Copiar archivos de configuracion necesarios
    archivos_config = [
        ('requirements.txt', 'requirements.txt'),
    ]
    
    for src, dst in archivos_config:
        src_path = os.path.join(script_dir, src)
        dst_path = os.path.join(portable_dir, dst)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
    
    # Crear archivo README-portable.txt
    readme_content = '''# ToolKinventario - Version Portable

Esta es una version portable de ToolKinventario.

## Uso

1. Haga doble clic en ToolKinventarioLauncher.exe para iniciar
2. Se abrira una ventana, espere a que el servidor este listo
3. El navegador se abrira automaticamente con la aplicacion

## Credenciales

Usuario: admin
Contrasena: admin123

## Puerto

Puerto por defecto: 5000
Puede cambiarlo en Configuracion

## Archivos

- ToolKinventarioLauncher.exe - Lanzador con interface grafica
- ToolKinventario.exe - Servidor (para uso interno)

## Carpetas

- database/ - Base de datos SQLite
- backups/ - Copias de seguridad
- logs/ - Registros de la aplicacion
- uploads/ - Archivos subidos

## Informacion

Version: 1.0.0
Desarrollador: Don Nadie Labs
GitHub: https://github.com/Don-Nadie-Lab/ToolKinventario

'''
    
    readme_path = os.path.join(portable_dir, 'README-portable.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print_status("README-portable.txt creado", "success")
    
    print("")
    print("=" * 60)
    print("  VERSION PORTABLE PREPARADA")
    print("=" * 60)
    print("")
    print(f"  Ubicacion: {portable_dir}")
    print(f"  Tamano: {get_dir_size(portable_dir):.2f} MB")
    print("")
    print("  Para usar:")
    print("  1. Copie la carpeta ToolKinventario-Portable al otro PC")
    print("  2. Ejecute ToolKinventarioLauncher.exe")
    print("")
    
    # Crear script para crear accesos directos
    crear_accesos_path = os.path.join(portable_dir, 'crear_accesos_directos.py')
    script_accesos = os.path.join(script_dir, 'crear_accesos_directos.py')
    if os.path.exists(script_accesos):
        shutil.copy2(script_accesos, crear_accesos_path)
        print_status("Script crear_accesos_directos.py copiado", "success")
    
    return True

def get_dir_size(path):
    """Obtener tamano de un directorio en MB"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)

if __name__ == "__main__":
    preparar_portable()
