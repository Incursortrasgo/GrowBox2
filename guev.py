def pagina_guev(nombre="GrowBox"):
    html = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{nombre}</title>
    <link rel="stylesheet" href="https://unpkg.com/chota@latest" />
    <style>
      body {{
        background-image: url("https://images.unsplash.com/photo-1497250681960-ef046c08a56e?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-size: cover;
        padding: 20px;
      }}
      body.dark {{
        --bg-color: #000;
        --bg-secondary-color: #131316;
        --font-color: #f5f5f5;
      }}
      .card {{
        background: #000000b5;
        padding: 20px;
        max-width: 400px;
        margin: 20px auto;
        text-align: center;
        border-radius: 10px;
      }}
      .dato {{
        font-size: 2rem;
        margin: 10px 0;
      }}
      label {{
        display: block;
        margin: 10px 0 5px;
      }}
      input[type="time"],
      input[type="text"],
      input[type="number"] {{
        width: 60%;
        display: block;
        margin: 0 auto 10px auto;
        text-align: center;
      }}
      .mensaje {{
        color: lime;
        margin-top: 10px;
        font-size: 1rem;
        min-height: 1.2em;
      }}
    </style>
  </head>
  <body class="dark">

    <div class="card">
      <h1 id="nombre-growbox">{nombre}</h1>
    </div>

    <div class="card">
      <h2 class="dato">Datos del ambiente</h2>
      <p id="temp" class="dato">Temperatura: -- °C</p>
      <p id="hume" class="dato">Humedad: -- %</p>
      <p class="dato">Luz: <span id="estado-valor" style="color:grey">--</span></p>
      <p class="dato">Ventilador: <span id="estado-ventilador" style="color:grey">--</span></p>
    </div>

    <div class="card">
      <h2 class="dato">Control de Iluminación</h2>
      <label>Hora de encendido:</label>
      <input type="time" id="hora-on" />
      <label>Hora de apagado:</label>
      <input type="time" id="hora-off" />
      <button class="button primary" onclick="guardarHoras()">Guardar Horas</button>
      <p id="msg-horas" class="mensaje"></p>
    </div>

    <div class="card">
      <h2 class="dato">Control de Ventilacion</h2>
      <label>Encender por encima de (°C):</label>
      <input type="number" id="temp-on" step="0.1" />
      <label>Apagar por debajo de (°C):</label>
      <input type="number" id="temp-off" step="0.1" />
      <button class="button primary" onclick="guardarUmbrales()">Guardar Config</button>
      <p id="msg-umbral" class="mensaje"></p>
    </div>

    <div class="card">
      <h2 class="dato">Cambiar Nombre</h2>
      <label>Nombre del sistema:</label>
      <input type="text" id="nombre" placeholder="GrowBox" />
      <button class="button primary" onclick="guardarNombre()">Guardar Nombre</button>
      <p id="msg-nombre" class="mensaje"></p>
    </div>

    <script>
      function mostrarMensaje(id, texto, color = "lime") {{
        const msg = document.getElementById(id);
        msg.style.color = color;
        msg.innerText = texto;
        setTimeout(() => {{
          msg.innerText = "";
        }}, 3000);
      }}

      function actualizarDatos() {{
        fetch('/datos')
          .then(res => res.json())
          .then(data => {{
            document.getElementById("temp").innerText = 'Temperatura: ' + data.temp + ' °C';
            document.getElementById("hume").innerText = 'Humedad: ' + data.hume + ' %';
            document.getElementById("estado-valor").innerText = data.estado;
            document.getElementById("estado-valor").style.color = data.estado === "Encendido" ? "lime" : "tomato";
            document.getElementById("estado-ventilador").innerText = data.estado_ventilador;
            document.getElementById("estado-ventilador").style.color = data.estado_ventilador === "Encendido" ? "lime" : "tomato";
          }});
      }}

      function guardarHoras() {{
        const on = document.getElementById("hora-on").value;
        const off = document.getElementById("hora-off").value;
        if (!on || !off) {{
          mostrarMensaje("msg-horas", "Completá ambas horas", "tomato");
          return;
        }}
        fetch('/horas', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ encender: on, apagar: off }})
        }}).then(() => {{
          mostrarMensaje("msg-horas", "Horas guardadas correctamente");
        }});
      }}

      function guardarUmbrales() {{
        const on = parseFloat(document.getElementById("temp-on").value);
        const off = parseFloat(document.getElementById("temp-off").value);
        if (isNaN(on) || isNaN(off) || off >= on) {{
          mostrarMensaje("msg-umbral", "Valores inválidos", "tomato");
          return;
        }}
        fetch('/umbral', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ temp_on: on, temp_off: off }})
        }}).then(() => {{
          mostrarMensaje("msg-umbral", "Umbrales actualizados");
        }});
      }}

      function guardarNombre() {{
        const nombre = document.getElementById("nombre").value;
        fetch('/nombre', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ nombre: nombre }})
        }}).then(() => {{
          document.getElementById("nombre-growbox").innerText = nombre;
          mostrarMensaje("msg-nombre", "Nombre actualizado");
        }});
      }}

      function cargarConfiguracion() {{
        fetch('/config')
          .then(r => r.json())
          .then(data => {{
            document.getElementById("hora-on").value = data.hora_on || "";
            document.getElementById("hora-off").value = data.hora_off || "";
            document.getElementById("nombre").value = data.nombre || "GrowBox";
            document.getElementById("nombre-growbox").innerText = data.nombre || "GrowBox";
            document.getElementById("temp-on").value = data.temp_on || 29.0;
            document.getElementById("temp-off").value = data.temp_off || 27.0;
          }});
      }}

      actualizarDatos();
      cargarConfiguracion();
      setInterval(actualizarDatos, 5000);
    </script>
  </body>
</html>
""".format(nombre=nombre)
    return html
