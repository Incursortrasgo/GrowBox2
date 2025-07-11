
import ujson
import machine
from utils import hora_a_segundos, guardar_config
from guev import pagina_guev

led = machine.Pin(16, machine.Pin.OUT, machine.Pin.PULL_DOWN)
ventilador = machine.Pin(17, machine.Pin.OUT, machine.Pin.PULL_DOWN)

def enviar_respuesta(conn, tipo, contenido, codigo="200 OK"):
    conn.send("HTTP/1.1 {}\r\n".format(codigo))
    headers = {
        "json": "Content-Type: application/json\r\n",
        "html": "Content-Type: text/html\r\n",
        "text": "Content-Type: text/plain\r\n"
    }
    conn.send(headers.get(tipo, "") + "Connection: close\r\n\r\n")
    if tipo == "json":
        conn.sendall(ujson.dumps(contenido))
    elif tipo == "html":
        conn.sendall(contenido)
    elif tipo == "text":
        conn.sendall(contenido if isinstance(contenido, str) else str(contenido))
    else:
        conn.send("Error")

def manejar_peticion(conn, addr, temperatura, humedad, hora_on, hora_off, nombre, temp_on, temp_off):
    try:
        request = conn.recv(1024)
        request_str = request.decode()

        if 'POST /horas' in request_str:
            cuerpo = request_str.split("\r\n\r\n", 1)[1]
            try:
                datos = ujson.loads(cuerpo)
                nueva_on = hora_a_segundos(datos.get("encender", "00:00"))
                nueva_off = hora_a_segundos(datos.get("apagar", "00:00"))
                if nueva_on is not None and nueva_off is not None:
                    guardar_config(nueva_on, nueva_off, nombre, temp_on, temp_off)
                    enviar_respuesta(conn, "text", "OK")
                    return nueva_on, nueva_off, nombre, temp_on, temp_off
                else:
                    enviar_respuesta(conn, "text", "Horas inválidas", "400 Bad Request")
            except:
                enviar_respuesta(conn, "text", "JSON inválido", "400 Bad Request")
            return hora_on, hora_off, nombre, temp_on, temp_off

        elif 'POST /nombre' in request_str:
            cuerpo = request_str.split("\r\n\r\n", 1)[1]
            try:
                datos = ujson.loads(cuerpo)
                nuevo_nombre = datos.get("nombre", nombre)
                guardar_config(hora_on, hora_off, nuevo_nombre, temp_on, temp_off)
                enviar_respuesta(conn, "text", "Nombre actualizado")
                return hora_on, hora_off, nuevo_nombre, temp_on, temp_off
            except:
                enviar_respuesta(conn, "text", "Error en nombre", "400 Bad Request")
            return hora_on, hora_off, nombre, temp_on, temp_off

        elif 'POST /umbral' in request_str:
            cuerpo = request_str.split("\r\n\r\n", 1)[1]
            try:
                datos = ujson.loads(cuerpo)
                nueva_temp_on = float(datos.get("temp_on", temp_on))
                nueva_temp_off = float(datos.get("temp_off", temp_off))
                if 0 <= nueva_temp_off < nueva_temp_on <= 100:
                    guardar_config(hora_on, hora_off, nombre, nueva_temp_on, nueva_temp_off)
                    enviar_respuesta(conn, "text", "Umbrales actualizados")
                    return hora_on, hora_off, nombre, nueva_temp_on, nueva_temp_off
                else:
                    enviar_respuesta(conn, "text", "Valores inválidos", "400 Bad Request")
            except:
                enviar_respuesta(conn, "text", "JSON inválido", "400 Bad Request")
            return hora_on, hora_off, nombre, temp_on, temp_off

        elif 'GET /datos' in request_str:
            estado_led = led.value()
            estado_ventilador = ventilador.value()
            datos = {
                "temp": temperatura,
                "hume": humedad,
                "estado": "Encendido" if estado_led else "Apagado",
                "estado_ventilador": "Encendido" if estado_ventilador else "Apagado"
            }
            enviar_respuesta(conn, "json", datos)

        elif 'GET /config' in request_str:
            datos = {
                "hora_on": "{:02d}:{:02d}".format(hora_on // 3600, (hora_on % 3600) // 60) if hora_on else "",
                "hora_off": "{:02d}:{:02d}".format(hora_off // 3600, (hora_off % 3600) // 60) if hora_off else "",
                "nombre": nombre,
                "temp_on": temp_on,
                "temp_off": temp_off
            }
            enviar_respuesta(conn, "json", datos)

        elif 'GET' in request_str:
            html = pagina_guev(nombre)
            enviar_respuesta(conn, "html", html)

        else:
            enviar_respuesta(conn, "text", "Ruta no encontrada", "404 Not Found")

    except Exception as e:
        print("Error en manejar_peticion:", e)
        enviar_respuesta(conn, "text", "Error interno", "500 Internal Server Error")
    finally:
        conn.close()

    return hora_on, hora_off, nombre, temp_on, temp_off
