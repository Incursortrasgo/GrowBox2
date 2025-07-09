import time
import ujson
import ntptime

HORA_FILE = "hora.dat"
zona_horaria = -3  # UTC-3 para Argentina

_hora_base = None         # Tiempo epoch al momento de guardar
_tiempo_arranque = None   # Ticks del sistema cuando arrancó

def guardar_hora_actual():
    """Guarda la hora actual (según time.time) en hora.dat"""
    try:
        t = time.time()
        with open(HORA_FILE, "w") as f:
            ujson.dump({"epoch": t}, f)
        print("Hora guardada en hora.dat:", time.localtime(t))
    except Exception as e:
        print("Error guardando hora:", e)

def cargar_hora_local():
    """Carga la hora desde hora.dat y registra el tiempo de arranque"""
    global _hora_base, _tiempo_arranque
    try:
        with open(HORA_FILE, "r") as f:
            datos = ujson.load(f)
            _hora_base = datos["epoch"]
            _tiempo_arranque = time.ticks_ms()
            print("Hora local recuperada:", time.localtime(_hora_base))
    except:
        _hora_base = None
        _tiempo_arranque = None
        print("No se encontró hora local previa.")

def hora_actual_segundos():
    """Devuelve la hora actual en segundos desde medianoche (local)"""
    if _hora_base is not None:
        # Estima hora en base a ticks desde el arranque
        delta = time.ticks_diff(time.ticks_ms(), _tiempo_arranque) // 1000
        t_local = _hora_base + delta + zona_horaria * 3600
        tm = time.localtime(t_local)
        return tm[3] * 3600 + tm[4] * 60
    else:
        # Usa RTC sin ajuste si no hay base
        t = time.localtime(time.time() + zona_horaria * 3600)
        return t[3] * 3600 + t[4] * 60

def sincronizar_ntp():
    """Intenta sincronizar la hora con NTP. Devuelve True si tuvo éxito"""
    global _hora_base, _tiempo_arranque
    try:
        ntptime.settime()  # Ajusta RTC con UTC
        t = time.time()
        _hora_base = t
        _tiempo_arranque = time.ticks_ms()
        guardar_hora_actual()
        print("Hora sincronizada con NTP:", time.localtime(t))
        return True
    except Exception as e:
        print("No se pudo sincronizar con NTP:", e)
        return False
