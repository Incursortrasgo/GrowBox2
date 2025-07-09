import network
import socket
import ure
import time
import machine

pin_wifi_ok = machine.Pin(2, machine.Pin.OUT, machine.Pin.PULL_DOWN)

ap_ssid = "GrowBox WiFi"
ap_password = "growbox0001"
ap_authmode = 3  # WPA2

NETWORK_PROFILES = "wifi.dat"

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None


def get_connection():
    """return a working WLAN(STA_IF) instance or None"""

    # First check if there already is any connection:
    if wlan_sta.isconnected():
        return wlan_sta
    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta
        # Read known network profiles from file
        profiles = read_profiles()

        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        for ssid, bssid, channel, rssi, authmode, hidden in sorted(
            networks, key=lambda x: x[3], reverse=True
        ):
            ssid = ssid.decode("utf-8")
            encrypted = authmode > 0
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print("skipping unknown encrypted network")
            else:  # open
                connected = do_connect(ssid, None)
            if connected:
                break
    except OSError as e:
        print("exception", str(e))
    # start web server for connection manager:
    if not connected:
        connected = start()
    return wlan_sta if connected else None


def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles


def write_profiles(profiles):
    lines = []
    for ssid, password in profiles.items():
        lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write("".join(lines))


def do_connect(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None
    print("Intendando conectar a %s..." % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(200):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.3)
        pin_wifi_ok.value(not pin_wifi_ok.value())
        print(".", end="")
    if connected:
        print("\nConectado. Configuracion de red: ", wlan_sta.ifconfig())
    else:
        print("\nFallo. No se pudo conectar a: " + ssid)
    pin_wifi_ok.value(0)
    return connected


def send_header(client, status_code=200, content_length=None):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
        client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


def handle_root(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode("utf-8") for ssid, *_ in wlan_sta.scan())
    send_header(client)
    client.sendall(
        """\
        <html>
            <h1 style="text-align: center;">
                Configuracion inicial WiFi
            </h1>
            <h3 style="text-align: center;">
                Seleccione su red WiFi e ingrese la contrasena
            </h3>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)
    while len(ssids):
        ssid = ssids.pop(0)
        client.sendall(
            """\
                        <tr>
                            <td colspan="2">
                                <input type="radio" name="ssid" value="{0}" />{0}
                            </td>
                        </tr>
        """.format(ssid))
    client.sendall(
            """\
                        <td>&nbsp;</td>
                        <tr>
                            <td>Password:</td>
                            <td><input name="password" type="password" /></td>
                        </tr>
                    </tbody>
                </table>
                    <p style="text-align: center;">
                        <input type="submit" value="Conectar" />
                    </p>
                </form>
            </html>
        """)
    client.close()


def handle_configure(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = (match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!"))
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")
    if len(ssid) == 0:
        send_response(client, "Debes elegir una red", status_code=400)
        return False
    if do_connect(ssid, password):
        response = """\
            <html>
                <center>
                    <br><br>
                    <h3 style="text-align: center;">
                        GrowBox se conecto con exito a la red WiFi %(ssid)s.
                    </h3>
                    <h3 style="text-align: center;">
                        Espera que la luz azul de tu GrowBox quede fija.
                    </h3>
                    <h3 style="text-align: center;">
                        Espera que tu dispositivo vuelva a conectarse a internet.
                    </h3>
                    <h3 style="text-align: center;">
                        <a href="http://%(ip)s">Ingresa a %(ip)s desde tu navegador</a>
                    </h3>
                    <br><br>
                </center>
            </html>
        """ % dict(ssid=ssid, ip=wlan_sta.ifconfig()[0])
        send_response(client, response)
        time.sleep(1)
        wlan_ap.active(False)
        try:
            profiles = read_profiles()
        except OSError:
            profiles = {}
        profiles[ssid] = password
        write_profiles(profiles)

        time.sleep(5)

        return True
    else:
        response = """\
            <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            GrowBox no se pudo conectar a la red WiFi %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input
                        type="button"
                        value="Volver!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket

    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]

    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)

    print("Conectate a WiFi ssid " + ap_ssid + ", password: " + ap_password)
    print("Accede a GrowBox desde tu navegador en: 192.168.4.1.")
    print("Escuchando en:", addr)

    while True:
        if wlan_sta.isconnected():
            wlan_ap.active(False)
            return True
        client, addr = server_socket.accept()
        print("cliente conectado desde:", addr)
        try:
            client.settimeout(5.0)
            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass
            try:
                request += client.recv(1024)
            except OSError:
                pass
            if "HTTP" not in request:  # skip invalid requests
                continue
            # version 1.9 compatibility
            try:
                url = (
                    ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request)
                    .group(1)
                    .decode("utf-8")
                    .rstrip("/")
                )
            except Exception:
                url = (
                    ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request)
                    .group(1)
                    .rstrip("/")
                )
            if url == "":
                handle_root(client)
            elif url == "configure":
                handle_configure(client, request)
            else:
                handle_not_found(client, url)
        finally:
            client.close()
