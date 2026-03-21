# -*- coding: utf-8 -*-
"""
==========================================================
MODULO DE CONECTIVIDAD Y MODO OFFLINE
==========================================================
Detecta el estado de conexion y permite funcionamiento
completamente sin internet (on-premise).

La aplicacion usa SQLite (base de datos local), por lo que
funciona offline por defecto. Este modulo proporciona:
- Deteccion de estado de conexion
- Indicador visual en la interfaz
- Utilidades de red
"""

import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)

class MonitorConexion:
    """
    Monitorea el estado de conexion a internet.
    Permite que la app detecte cuando esta offline.
    """
    
    def __init__(self, intervalo=30):
        """
        Args:
            intervalo: Segundos entre verificaciones
        """
        self.intervalo = intervalo
        self.conectado = True
        self._thread = None
        self._ejecutando = False
        self.servidores_prueba = [
            ('8.8.8.8', 53),      # Google DNS
            ('1.1.1.1', 53),      # Cloudflare DNS
        ]
    
    def verificar_conexion(self):
        """
        Verifica si hay conexion a internet.
        Returns:
            bool: True si hay conexion
        """
        for servidor, puerto in self.servidores_prueba:
            if self._probar_host(servidor, puerto):
                return True
        return False
    
    def _probar_host(self, host, puerto, timeout=3):
        """Prueba conexion a un host especifico"""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, puerto))
            return True
        except (socket.timeout, socket.error):
            return False
    
    def iniciar_monitoreo(self):
        """Inicia el hilo de monitoreo en background"""
        if self._ejecutando:
            return
        
        self._ejecutando = True
        self._thread = threading.Thread(target=self._monitoreo_loop, daemon=True)
        self._thread.start()
        logger.info("Monitoreo de conexion iniciado")
    
    def _monitoreo_loop(self):
        """Bucle principal de monitoreo"""
        while self._ejecutando:
            estado_anterior = self.conectado
            self.conectado = self.verificar_conexion()
            
            if estado_anterior != self.conectado:
                if self.conectado:
                    logger.info("Conexion a internet restaurada")
                else:
                    logger.warning("Conexion a internet perdida - Modo Offline")
            
            time.sleep(self.intervalo)
    
    def detener_monitoreo(self):
        """Detiene el hilo de monitoreo"""
        self._ejecutando = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Monitoreo de conexion detenido")
    
    def obtener_estado(self):
        """
        Obtiene el estado actual de conexion.
        Returns:
            dict: Estado de conexion
        """
        return {
            'conectado': self.conectado,
            'timestamp': time.time()
        }

# Instancia global del monitor
monitor_conexion = MonitorConexion()

def obtener_ip_local():
    """
    Obtiene la direccion IP local de la maquina.
    Returns:
        str: Direccion IP o 'No disponible'
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'No disponible'

def obtener_nombre_host():
    """
    Obtiene el nombre del host local.
    Returns:
        str: Nombre del host
    """
    try:
        return socket.gethostname()
    except Exception:
        return 'No disponible'

def es_red_local(ip):
    """
    Verifica si una IP es de red local (LAN).
    Returns:
        bool: True si es IP local
    """
    if not ip or ip == 'No disponible':
        return False
    
    # Rangos de IPs privadas
    return (
        ip.startswith('192.168.') or
        ip.startswith('10.') or
        ip.startswith('172.16.') or
        ip.startswith('172.17.') or
        ip.startswith('172.18.') or
        ip.startswith('172.19.') or
        ip.startswith('172.2') or
        ip.startswith('172.30.') or
        ip.startswith('172.31.')
    )

def obtener_informacion_red():
    """
    Obtiene informacion completa de la red.
    Returns:
        dict: Informacion de red
    """
    ip_local = obtener_ip_local()
    
    return {
        'hostname': obtener_nombre_host(),
        'ip_local': ip_local,
        'es_red_local': es_red_local(ip_local),
        'conexion_internet': monitor_conexion.conectado,
        'modo': 'offline' if not monitor_conexion.conectado else 'online'
    }
