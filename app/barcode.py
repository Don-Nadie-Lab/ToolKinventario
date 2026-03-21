# -*- coding: utf-8 -*-
"""
==========================================================
MODULO DE CODIGO DE BARRAS
==========================================================
Funcionalidades:
- Escaneo con camara (Raspberry Pi, webcam)
- Soporte para lectores USB (modo HID keyboard)
- Deteccion de multiples tipos de codigos
- Mejora de imagen para mejor precision

Tipos soportados: EAN-13, EAN-8, UPC-A, Code-128, QR
"""

import cv2
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# Importar pyzbar de forma opcional
try:
    from pyzbar import pyzbar
    PYZBAR_DISPONIBLE = True
except ImportError:
    PYZBAR_DISPONIBLE = False
    logger.warning("pyzbar no esta disponible. El escaneo de codigos de barras estara deshabilitado.")

def procesar_codigo_barras(imagen_file):
    """
    Procesa una imagen para detectar códigos de barras
    
    Args:
        imagen_file: Archivo de imagen subido desde el formulario
        
    Returns:
        str: Código de barras detectado o None si no se encuentra
    """
    if not PYZBAR_DISPONIBLE:
        logger.warning("pyzbar no esta disponible")
        return None
        
    try:
        # Leer la imagen desde el archivo
        imagen_bytes = imagen_file.read()
        imagen_file.seek(0)  # Resetear el puntero del archivo
        
        # Convertir bytes a imagen PIL
        imagen_pil = Image.open(io.BytesIO(imagen_bytes))
        
        # Convertir PIL a array numpy para OpenCV
        imagen_array = np.array(imagen_pil)
        
        # Si la imagen está en RGB, convertir a BGR para OpenCV
        if len(imagen_array.shape) == 3 and imagen_array.shape[2] == 3:
            imagen_cv = cv2.cvtColor(imagen_array, cv2.COLOR_RGB2BGR)
        else:
            imagen_cv = imagen_array
        
        # Detectar códigos de barras
        codigos = pyzbar.decode(imagen_cv)
        
        if codigos:
            # Retornar el primer código encontrado
            codigo = codigos[0].data.decode('utf-8')
            logger.info(f"Codigo de barras detectado: {codigo}")
            return codigo
        else:
            logger.warning("No se detecto ningun codigo de barras en la imagen")
            return None
            
    except Exception as e:
        logger.error(f"Error al procesar codigo de barras: {str(e)}")
        return None

def mejorar_imagen_para_deteccion(imagen_cv):
    """
    Mejora la imagen para facilitar la detección de códigos de barras
    
    Args:
        imagen_cv: Imagen en formato OpenCV
        
    Returns:
        Imagen mejorada
    """
    try:
        # Convertir a escala de grises
        if len(imagen_cv.shape) == 3:
            gris = cv2.cvtColor(imagen_cv, cv2.COLOR_BGR2GRAY)
        else:
            gris = imagen_cv
        
        # Aplicar filtro gaussiano para reducir ruido
        gris = cv2.GaussianBlur(gris, (5, 5), 0)
        
        # Mejorar contraste usando CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gris = clahe.apply(gris)
        
        # Aplicar umbralización adaptativa
        umbral = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        return umbral
        
    except Exception as e:
        logger.error(f"Error al mejorar imagen: {str(e)}")
        return imagen_cv

def detectar_codigo_barras_avanzado(imagen_file):
    """
    Detección avanzada de códigos de barras con múltiples técnicas
    
    Args:
        imagen_file: Archivo de imagen
        
    Returns:
        str: Código de barras detectado o None
    """
    if not PYZBAR_DISPONIBLE:
        return None
        
    try:
        # Leer imagen
        imagen_bytes = imagen_file.read()
        imagen_file.seek(0)
        
        imagen_pil = Image.open(io.BytesIO(imagen_bytes))
        imagen_array = np.array(imagen_pil)
        
        if len(imagen_array.shape) == 3 and imagen_array.shape[2] == 3:
            imagen_cv = cv2.cvtColor(imagen_array, cv2.COLOR_RGB2BGR)
        else:
            imagen_cv = imagen_array
        
        # Intentar detección directa primero
        codigos = pyzbar.decode(imagen_cv)
        if codigos:
            return codigos[0].data.decode('utf-8')
        
        # Si no funciona, mejorar la imagen y volver a intentar
        imagen_mejorada = mejorar_imagen_para_deteccion(imagen_cv)
        codigos = pyzbar.decode(imagen_mejorada)
        if codigos:
            return codigos[0].data.decode('utf-8')
        
        # Intentar con diferentes escalas
        escalas = [0.5, 1.5, 2.0]
        for escala in escalas:
            altura, ancho = imagen_cv.shape[:2]
            nueva_altura = int(altura * escala)
            nuevo_ancho = int(ancho * escala)
            
            imagen_escalada = cv2.resize(imagen_cv, (nuevo_ancho, nueva_altura))
            codigos = pyzbar.decode(imagen_escalada)
            if codigos:
                return codigos[0].data.decode('utf-8')
        
        # Intentar con rotaciones
        angulos = [90, 180, 270]
        for angulo in angulos:
            altura, ancho = imagen_cv.shape[:2]
            centro = (ancho // 2, altura // 2)
            matriz_rotacion = cv2.getRotationMatrix2D(centro, angulo, 1.0)
            imagen_rotada = cv2.warpAffine(imagen_cv, matriz_rotacion, (ancho, altura))
            
            codigos = pyzbar.decode(imagen_rotada)
            if codigos:
                return codigos[0].data.decode('utf-8')
        
        logger.warning("No se pudo detectar codigo de barras con tecnicas avanzadas")
        return None
        
    except Exception as e:
        logger.error(f"Error en deteccion avanzada: {str(e)}")
        return None

class LectorCodigoBarrasUSB:
    """
    Clase para manejar lectores de código de barras USB (modo HID keyboard)
    """
    
    def __init__(self):
        self.buffer_codigo = ""
        self.codigo_completo = False
    
    def procesar_entrada_teclado(self, caracter):
        """
        Procesa caracteres de entrada del lector USB
        
        Args:
            caracter: Caracter recibido del lector
            
        Returns:
            str: Código completo si se terminó de leer, None en caso contrario
        """
        if caracter == '\r' or caracter == '\n':
            # Fin del código de barras
            if self.buffer_codigo:
                codigo = self.buffer_codigo
                self.buffer_codigo = ""
                self.codigo_completo = True
                return codigo
        else:
            # Agregar caracter al buffer
            self.buffer_codigo += caracter
            self.codigo_completo = False
        
        return None
    
    def limpiar_buffer(self):
        """Limpia el buffer de código"""
        self.buffer_codigo = ""
        self.codigo_completo = False

def validar_codigo_barras(codigo):
    """
    Valida si un código de barras tiene un formato válido
    
    Args:
        codigo: Código de barras a validar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not codigo:
        return False
    
    # Eliminar espacios en blanco
    codigo = codigo.strip()
    
    # Verificar longitud mínima
    if len(codigo) < 4:
        return False
    
    # Verificar que contenga solo caracteres alfanuméricos y algunos símbolos permitidos
    caracteres_permitidos = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_.')
    if not all(c in caracteres_permitidos for c in codigo):
        return False
    
    return True

def formatear_codigo_barras(codigo):
    """
    Formatea un código de barras para almacenamiento consistente
    
    Args:
        codigo: Código de barras sin formatear
        
    Returns:
        str: Código formateado
    """
    if not codigo:
        return ""
    
    # Eliminar espacios y convertir a mayúsculas
    codigo_formateado = codigo.strip().upper()
    
    return codigo_formateado

def generar_codigo_barras_interno(prefijo="TK", longitud=8):
    """
    Genera un código de barras interno para productos sin código
    
    Args:
        prefijo: Prefijo para el código (por defecto "TK" para ToolKinventario)
        longitud: Longitud total del código
        
    Returns:
        str: Código de barras generado
    """
    import random
    import string
    
    # Calcular longitud del sufijo numérico
    longitud_sufijo = longitud - len(prefijo)
    
    if longitud_sufijo <= 0:
        longitud_sufijo = 6
    
    # Generar sufijo numérico aleatorio
    sufijo = ''.join(random.choices(string.digits, k=longitud_sufijo))
    
    return f"{prefijo}{sufijo}"

def detectar_tipo_codigo_barras(codigo):
    """
    Detecta el tipo de código de barras basado en su formato
    
    Args:
        codigo: Código de barras
        
    Returns:
        str: Tipo de código detectado
    """
    if not codigo:
        return "DESCONOCIDO"
    
    codigo = codigo.strip()
    longitud = len(codigo)
    
    # EAN-13 (13 dígitos)
    if longitud == 13 and codigo.isdigit():
        return "EAN-13"
    
    # EAN-8 (8 dígitos)
    elif longitud == 8 and codigo.isdigit():
        return "EAN-8"
    
    # UPC-A (12 dígitos)
    elif longitud == 12 and codigo.isdigit():
        return "UPC-A"
    
    # Code 128 (variable, alfanumérico)
    elif 1 <= longitud <= 128:
        return "CODE-128"
    
    # Código interno ToolKinventario
    elif codigo.startswith("TK"):
        return "INTERNO-TK"
    
    else:
        return "PERSONALIZADO"

# Configuración para Raspberry Pi Camera
class CamaraRaspberryPi:
    """
    Clase para manejar la cámara de Raspberry Pi para escaneo de códigos
    """
    
    def __init__(self, resolucion=(640, 480)):
        self.resolucion = resolucion
        self.camara = None
        self.inicializar_camara()
    
    def inicializar_camara(self):
        """Inicializa la cámara"""
        try:
            self.camara = cv2.VideoCapture(0)
            if self.camara.isOpened():
                self.camara.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucion[0])
                self.camara.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucion[1])
                logger.info("Cámara Raspberry Pi inicializada correctamente")
            else:
                logger.error("No se pudo inicializar la cámara")
                self.camara = None
        except Exception as e:
            logger.error(f"Error al inicializar cámara: {str(e)}")
            self.camara = None
    
    def capturar_imagen(self):
        """
        Captura una imagen desde la cámara
        
        Returns:
            numpy.array: Imagen capturada o None si hay error
        """
        if not self.camara or not self.camara.isOpened():
            return None
        
        try:
            ret, frame = self.camara.read()
            if ret:
                return frame
            else:
                logger.error("No se pudo capturar imagen de la cámara")
                return None
        except Exception as e:
            logger.error(f"Error al capturar imagen: {str(e)}")
            return None
    
    def escanear_codigo_barras_continuo(self, callback, timeout=30):
        """
        Escanea códigos de barras de forma continua
        
        Args:
            callback: Función a llamar cuando se detecte un código
            timeout: Tiempo límite en segundos
        """
        if not self.camara:
            return
        
        import time
        tiempo_inicio = time.time()
        
        while time.time() - tiempo_inicio < timeout:
            frame = self.capturar_imagen()
            if frame is not None:
                codigos = pyzbar.decode(frame)
                if codigos:
                    codigo = codigos[0].data.decode('utf-8')
                    callback(codigo)
                    break
            
            time.sleep(0.1)  # Pequeña pausa para no sobrecargar el CPU
    
    def cerrar(self):
        """Cierra la cámara"""
        if self.camara:
            self.camara.release()
            self.camara = None
            logger.info("Cámara cerrada correctamente")
