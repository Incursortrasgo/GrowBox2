import time
import machine
import socket
import wifimgr
import reloj
from htmlhand import manejar_peticion
from utils import (
    cargar_config,
    leer_sensor,
    controlar_rele,
    controlar_ventilador
)

# Pines
pin_wifi_ok = machine.Pin(2, machine.Pin.OUT, machine.Pin.PULL_DOWN)
gpio0 = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)

# Variables globales
hora_on = None
hora_off = None
nombre = "GrowBox"
temp_on = 29.0
temp_off = 27.0

def iniciar_servidor():
    global hora_on, hora_off, nombre, temp_on, temp_off

    print("Iniciando WiFi...")
    wlan = wifimgr.get_connection()

    pin_wifi_ok.value(1)
    time.sleep(1)

    print("Cargando hora local...")
    reloj.cargar_hora_local()
    print("Intentando sincronizar con NTP...")
    sincronizada = reloj.sincronizar_ntp()  # primer intento

    # Cargar configuración del sistema
    hora_on, hora_off, nombre, temp_on, temp_off = cargar_config()

    # Iniciar servidor web
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 80))
    sock.listen(5)
    print("Servidor escuchando en puerto 80")

    # Variables para control de guardado/reintento NTP
    ultimo_guardado = time.time()
    ultimo_ntp = time.time()

    try:
        while True:
            temperatura, humedad = leer_sensor()
            temperatura = round(temperatura, 1) if temperatura is not None else "--"
            humedad = round(humedad, 1) if humedad is not None else "--"

            # Obtener hora actual del módulo reloj (offline si es necesario)
            ahora = reloj.hora_actual_segundos()

            # Controlar relé y ventilador
            controlar_rele(ahora, hora_on, hora_off)
            controlar_ventilador(temperatura, temp_on, temp_off)

            # Guardar hora una vez por hora
            if time.time() - ultimo_guardado >= 3600:
                reloj.guardar_hora_actual()
                print("Hora guardada localmente")
                ultimo_guardado = time.time()

            # Reintentar sincronización NTP si antes falló
            if not sincronizada and time.time() - ultimo_ntp >= 600:
                print("Reintentando sincronizar NTP...")
                sincronizada = reloj.sincronizar_ntp()
                ultimo_ntp = time.time()

            # Manejo de cliente web
            conn, addr = sock.accept()
            hora_on, hora_off, nombre, temp_on, temp_off = manejar_peticion(
                conn, addr, temperatura, humedad, hora_on, hora_off, nombre, temp_on, temp_off
            )

    except Exception as e:
        print("Error general:", e)

    finally:
        sock.close()
        print("Socket cerrado correctamente")

# Iniciar todo
iniciar_servidor()
