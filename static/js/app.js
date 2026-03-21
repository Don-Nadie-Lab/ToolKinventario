/**
 * ToolKinventario - Scripts principales
 * Sistema de inventario para Raspberry Pi
 */

// Esperar a que el DOM esté completamente cargado
document.addEventListener("DOMContentLoaded", () => {
  // Importar Bootstrap
  var bootstrap = window.bootstrap

  // Inicializar tooltips de Bootstrap
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Inicializar popovers de Bootstrap
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  var popoverList = popoverTriggerList.map((popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl))

  // Configurar mensajes flash para que se cierren automáticamente
  var alertList = document.querySelectorAll(".alert")
  alertList.forEach((alert) => {
    // Cerrar automáticamente después de 5 segundos
    setTimeout(() => {
      var bsAlert = new bootstrap.Alert(alert)
      bsAlert.close()
    }, 5000)
  })

  // Manejar el evento de escaneo de código de barras con lectores USB
  // Los lectores USB funcionan como teclados, enviando caracteres rápidamente
  var barcodeBuffer = ""
  var lastKeyTime = 0
  var barcodeTimeoutMs = 50 // Tiempo máximo entre teclas para considerar parte del mismo código

  document.addEventListener("keydown", (e) => {
    // Ignorar teclas de control
    if (e.ctrlKey || e.altKey || e.metaKey) return

    var currentTime = new Date().getTime()

    // Si ha pasado mucho tiempo desde la última tecla, reiniciar el buffer
    if (currentTime - lastKeyTime > barcodeTimeoutMs && barcodeBuffer.length > 0) {
      barcodeBuffer = ""
    }

    // Actualizar el tiempo de la última tecla
    lastKeyTime = currentTime

    // Enter o Tab indican el final del código de barras
    if (e.key === "Enter" || e.key === "Tab") {
      if (barcodeBuffer.length > 3) {
        procesarCodigoBarras(barcodeBuffer)
      }
      barcodeBuffer = ""
      e.preventDefault()
    }
    // Agregar el carácter al buffer
    else if (e.key.length === 1) {
      barcodeBuffer += e.key
    }
  })

  // Función para procesar el código de barras escaneado
  function procesarCodigoBarras(codigo) {
    console.log("Código de barras escaneado:", codigo)

    // Verificar si estamos en la página de movimientos
    var productoSelect = document.getElementById("producto_id")
    if (productoSelect) {
      // Buscar el producto por código
      var encontrado = false
      for (var i = 0; i < productoSelect.options.length; i++) {
        var option = productoSelect.options[i]
        if (option.text.includes(codigo)) {
          productoSelect.value = option.value
          productoSelect.dispatchEvent(new Event("change"))
          encontrado = true
          break
        }
      }

      if (!encontrado) {
        // Mostrar mensaje si no se encontró el producto
        alert("No se encontró ningún producto con el código: " + codigo)
      }
    } else {
      // Si no estamos en la página de movimientos, redirigir
      window.location.href = "/movimientos/nuevo?codigo=" + encodeURIComponent(codigo)
    }
  }

  // Función para formatear moneda
  window.formatearMoneda = (valor) =>
    "$" +
    Number.parseFloat(valor)
      .toFixed(2)
      .replace(/\d(?=(\d{3})+\.)/g, "$&,")

  // Función para formatear fecha
  window.formatearFecha = (fecha) => {
    if (!fecha) return ""
    var d = new Date(fecha)
    return (
      d.getDate().toString().padStart(2, "0") +
      "/" +
      (d.getMonth() + 1).toString().padStart(2, "0") +
      "/" +
      d.getFullYear()
    )
  }

  // Detectar si es un dispositivo móvil o táctil
  var isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0
  if (isTouchDevice) {
    document.body.classList.add("touch-device")
  }

  // Ajustes para pantallas pequeñas (Raspberry Pi)
  function ajustarInterfazPantallaPequena() {
    var width = window.innerWidth
    if (width < 800) {
      // Reducir padding en tablas
      var tablas = document.querySelectorAll(".table")
      tablas.forEach((tabla) => {
        tabla.classList.add("table-sm")
      })

      // Hacer botones más grandes para táctil
      var botones = document.querySelectorAll(".btn")
      botones.forEach((boton) => {
        if (!boton.classList.contains("btn-sm") && !boton.classList.contains("btn-lg")) {
          boton.classList.add("btn-lg")
        }
      })
    }
  }

  // Ejecutar ajustes iniciales
  ajustarInterfazPantallaPequena()

  // Volver a ajustar cuando cambie el tamaño de la ventana
  window.addEventListener("resize", ajustarInterfazPantallaPequena)

  // Manejar el modo oscuro (opcional)
  var darkModeToggle = document.getElementById("darkModeToggle")
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode")
      var isDarkMode = document.body.classList.contains("dark-mode")
      localStorage.setItem("darkMode", isDarkMode ? "enabled" : "disabled")
    })

    // Verificar preferencia guardada
    if (localStorage.getItem("darkMode") === "enabled") {
      document.body.classList.add("dark-mode")
    }
  }
})
