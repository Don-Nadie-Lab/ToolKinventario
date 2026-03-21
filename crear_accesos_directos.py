#!/usr/bin/env python3
"""
ToolKinventario - Crear Accesos Directos
Crea iconos en Escritorio y Menu Inicio
"""

import os
import sys
import shutil
from pathlib import Path

def get_desktop_path():
    """Obtener ruta del escritorio"""
    if sys.platform == 'win32':
        return os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
    elif sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Desktop')
    else:
        return os.path.join(os.path.expanduser('~'), 'desktop')

def get_start_menu_path():
    """Obtener ruta del Menu Inicio"""
    if sys.platform == 'win32':
        return os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
    elif sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Applications')
    else:
        return os.path.join(os.path.expanduser('~'), '.local', 'share', 'applications')

def create_shortcut_python(target_path, shortcut_name, icon_path=None, description=""):
    """Crear acceso directo usando comando powershell"""
    import subprocess
    
    desktop = get_desktop_path()
    start_menu = get_start_menu_path()
    
    if not os.path.exists(desktop):
        print(f"[X] Escritorio no encontrado: {desktop}")
        return False
    
    shortcut_path_desktop = os.path.join(desktop, f"{shortcut_name}.lnk")
    shortcut_path_start = os.path.join(start_menu, f"{shortcut_name}.lnk")
    
    # Crear acceso directo usando PowerShell
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path_desktop}")
$Shortcut.TargetPath = "python.exe"
$Shortcut.Arguments = '"{target_path}"'
$Shortcut.WorkingDirectory = '"{os.path.dirname(target_path)}"'
$Shortcut.Description = "{description}"
'''
    if icon_path and os.path.exists(icon_path):
        ps_script += f'''
$Shortcut.IconLocation = "{icon_path}"
'''
    ps_script += '''
$Shortcut.Save()
'''
    
    try:
        result = subprocess.run(['powershell', '-Command', ps_script], 
                             capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Acceso directo creado en Escritorio: {shortcut_name}")
            created_desktop = True
        else:
            print(f"[X] Error creando acceso directo: {result.stderr}")
            created_desktop = False
    except Exception as e:
        print(f"[X] Error: {e}")
        created_desktop = False
    
    # Crear en Menu Inicio
    ps_script_start = ps_script.replace(shortcut_path_desktop, shortcut_path_start)
    
    try:
        result = subprocess.run(['powershell', '-Command', ps_script_start],
                             capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Acceso directo creado en Menu Inicio: {shortcut_name}")
            created_start = True
        else:
            created_start = False
    except:
        created_start = False
    
    return created_desktop or created_start

def create_exe_shortcut(target_exe, shortcut_name, icon_path=None, description=""):
    """Crear acceso directo a un ejecutable .exe"""
    import subprocess
    
    desktop = get_desktop_path()
    start_menu = get_start_menu_path()
    
    if not os.path.exists(desktop):
        print(f"[X] Escritorio no encontrado")
        return False
    
    # PowerShell script para crear acceso directo
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{os.path.join(desktop, shortcut_name + '.lnk')}")
$Shortcut.TargetPath = "{target_exe}"
$Shortcut.WorkingDirectory = '"{os.path.dirname(target_exe)}"'
$Shortcut.Description = "{description}"
$Shortcut.Save()
'''
    
    if icon_path:
        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{os.path.join(desktop, shortcut_name + '.lnk')}")
$Shortcut.TargetPath = "{target_exe}"
$Shortcut.WorkingDirectory = '"{os.path.dirname(target_exe)}"'
$Shortcut.Description = "{description}"
$Shortcut.IconLocation = "{icon_path}"
$Shortcut.Save()
'''
    
    ps_script_start = ps_script.replace(
        os.path.join(desktop, shortcut_name + '.lnk'),
        os.path.join(start_menu, shortcut_name + '.lnk')
    )
    
    try:
        subprocess.run(['powershell', '-Command', ps_script], 
                      capture_output=True, check=True)
        print(f"[OK] Acceso directo en Escritorio: {shortcut_name}")
        created_desktop = True
    except Exception as e:
        print(f"[X] Error creando acceso directo: {e}")
        created_desktop = False
    
    try:
        subprocess.run(['powershell', '-Command', ps_script_start],
                      capture_output=True, check=True)
        print(f"[OK] Acceso directo en Menu Inicio: {shortcut_name}")
        created_start = True
    except:
        created_start = False
    
    return created_desktop or created_start

def add_to_startup(exe_path, app_name):
    """Agregar aplicacion al inicio automatico de Windows"""
    import subprocess
    
    if sys.platform != 'win32':
        print("[X] Esta funcion solo funciona en Windows")
        return False
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    ps_script = f'''
$regPath = 'HKCU:\\{key_path}'
Set-ItemProperty -Path $regPath -Name "{app_name}" -Value '"{exe_path}"'
'''
    
    try:
        subprocess.run(['powershell', '-Command', ps_script],
                     capture_output=True, check=True)
        print(f"[OK] Agregado al inicio automatico: {app_name}")
        return True
    except Exception as e:
        print(f"[X] Error agregando al inicio: {e}")
        return False

def remove_from_startup(app_name):
    """Quitar aplicacion del inicio automatico"""
    import subprocess
    
    if sys.platform != 'win32':
        return False
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    ps_script = f'''
$regPath = 'HKCU:\\{key_path}'
Remove-ItemProperty -Path $regPath -Name "{app_name}" -ErrorAction SilentlyContinue
'''
    
    try:
        subprocess.run(['powershell', '-Command', ps_script],
                     capture_output=True, check=True)
        print(f"[OK] Removido del inicio automatico")
        return True
    except:
        return False

def main():
    print("")
    print("=" * 50)
    print("  ToolKinventario - Crear Accesos Directos")
    print("=" * 50)
    print("")
    
    # Detectar ubicacion
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Buscar ejecutables
    exe_path = os.path.join(app_dir, 'ToolKinventario.exe')
    launcher_path = os.path.join(app_dir, 'ToolKinventarioLauncher.exe')
    
    if not os.path.exists(exe_path) and not os.path.exists(launcher_path):
        # Buscar en dist
        dist_exe = os.path.join(os.path.dirname(app_dir), 'dist', 'ToolKinventario', 'ToolKinventarioLauncher.exe')
        if os.path.exists(dist_exe):
            launcher_path = dist_exe
        else:
            print("[X] No se encontro ToolKinventario.exe o ToolKinventarioLauncher.exe")
            return
    
    # Icono
    icon_path = os.path.join(app_dir, 'static', 'icon.ico')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(app_dir, 'icon.ico')
    if not os.path.exists(icon_path):
        icon_path = None
    
    # Crear accesos directos
    print("Creando accesos directos en Escritorio...")
    print("")
    
    if os.path.exists(launcher_path):
        create_exe_shortcut(
            launcher_path,
            "ToolKinventario",
            icon_path,
            "Sistema de Gestion de Inventario"
        )
    elif os.path.exists(exe_path):
        create_exe_shortcut(
            exe_path,
            "ToolKinventario",
            icon_path,
            "Sistema de Gestion de Inventario"
        )
    
    print("")
    print("=" * 50)
    print("  ACCESOS DIRECTOS CREADOS")
    print("=" * 50)
    print("")
    print("  Escritorio: Icono ToolKinventario")
    print("  Menu Inicio: ToolKinventario")
    print("")
    
    # Preguntar por inicio automatico
    if sys.platform == 'win32':
        print("[?] Agregar al inicio automatico de Windows? (S/N): ", end="")
        respuesta = input().strip().upper()
        
        if respuesta == 'S':
            if os.path.exists(launcher_path):
                add_to_startup(launcher_path, "ToolKinventario")
            elif os.path.exists(exe_path):
                add_to_startup(exe_path, "ToolKinventario")
    
    print("")
    print("Listo!")

if __name__ == "__main__":
    main()
