import time
import ujson
import ahtx0
import machine
from machine import I2C, Pin

# Inicialización I2C y hardware
i2c = I2C(1, scl=Pin(19), sda=Pin(18), freq=400000)
sensor = ahtx0.AHT10(i2c)
led = machine.Pin(16, machine.Pin.OUT, machine.Pin.PULL_DOWN)
ventilador = machine.Pin(17, machine.Pin.OUT, machine.Pin.PULL_DOWN)

def hora_a_segundos(hora_str):
    try:
        h, m = map(int, hora_str.split(":"))
        if 0 <= h < 24 and 0 <= m < 60:
            return h * 3600 + m * 60
    except:
        pass
    return None

def hora_actual_segundos():
    t = time.localtime(time.time() - 3 * 3600)
    return t[3] * 3600 + t[4] * 60

def guardar_config(hora_on, hora_off, nombre, temp_on=29.0, temp_off=27.0):
    config = {
        "hora_on": hora_on,
        "hora_off": hora_off,
        "nombre": nombre,
        "temp_on": temp_on,
        "temp_off": temp_off
    }
    with open("config.json", "w") as f:
        ujson.dump(config, f)

def cargar_config():
    try:
        with open("config.json", "r") as f:
            config = ujson.load(f)
            hora_on = config.get("hora_on")
            hora_off = config.get("hora_off")
            nombre = config.get("nombre", "GrowBox")
            temp_on = config.get("temp_on", 29.0)
            temp_off = config.get("temp_off", 27.0)
            print("Configuración cargada:", hora_on, hora_off, nombre, temp_on, temp_off)
            return hora_on, hora_off, nombre, temp_on, temp_off
    except:
        print("No se encontró configuración previa.")
        return None, None, "GrowBox", 29.0, 27.0

def leer_sensor():
    try:
        return sensor.temperature, sensor.relative_humidity
    except OSError as e:
        print("error sensor:", e)
        return None, None

def controlar_rele(ahora, hora_on, hora_off):
    if hora_on is not None and hora_off is not None:
        if hora_on < hora_off:
            encender = hora_on <= ahora < hora_off
        else:
            encender = ahora >= hora_on or ahora < hora_off
        led.value(1 if encender else 0)

def controlar_ventilador(temperatura, umbral_on=29.0, umbral_off=27.0):
    if temperatura is None:
        return
    estado_actual = ventilador.value()
    if estado_actual == 0 and temperatura >= umbral_on:
        ventilador.value(1)
    elif estado_actual == 1 and temperatura <= umbral_off:
        ventilador.value(0)
