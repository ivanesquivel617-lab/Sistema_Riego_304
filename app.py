
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_sistema_riego"

# Estado inicial
sistema = {
    "humedad": 30,
    "bomba": False,
    "modo": "Automatico",
    "humedad_minima": 40,
    "duracion": 10
}


# Conectar con SQLite
def conectar():
    conexion = sqlite3.connect("riego.db")
    conexion.row_factory = sqlite3.Row
    return conexion


# Crear tabla del historial
def crear_tabla():
    conexion = conectar()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            humedad INTEGER NOT NULL,
            evento TEXT NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()


# Registrar eventos
def registrar_evento(evento):
    conexion = conectar()
    conexion.execute(
        "INSERT INTO historial (fecha, humedad, evento) VALUES (?, ?, ?)",
        (
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            sistema["humedad"],
            evento
        )
    )
    conexion.commit()
    conexion.close()


# Control automático de la bomba
def controlar_bomba():
    if sistema["modo"] == "Automatico":

        if sistema["humedad"] < sistema["humedad_minima"]:
            if not sistema["bomba"]:
                sistema["bomba"] = True
                registrar_evento("Bomba encendida automáticamente")

        else:
            if sistema["bomba"]:
                sistema["bomba"] = False
                registrar_evento("Bomba apagada automáticamente")


# Página principal
@app.route("/")
def inicio():
    controlar_bomba()
    return render_template("index.html", sistema=sistema)


# Página de humedad
@app.route("/humedad", methods=["GET", "POST"])
def humedad():

    if request.method == "POST":
        try:
            nueva_humedad = int(request.form["humedad"])

            if 0 <= nueva_humedad <= 100:
                sistema["humedad"] = nueva_humedad
                registrar_evento("Humedad modificada manualmente")
                controlar_bomba()
            else:
                flash("La humedad debe estar entre 0 y 100.")

        except (ValueError, KeyError):
            flash("Introduce un valor válido.")

        return redirect(url_for("humedad"))

    controlar_bomba()
    return render_template("humedad.html", sistema=sistema)


# Subir o bajar humedad
@app.route("/cambiar_humedad", methods=["POST"])
def cambiar_humedad():

    try:
        cambio = int(request.form["cambio"])

        if cambio in (-1, 1):
            nueva_humedad = sistema["humedad"] + cambio
            nueva_humedad = max(0, min(100, nueva_humedad))

            if nueva_humedad != sistema["humedad"]:
                sistema["humedad"] = nueva_humedad
                registrar_evento(
                    "Humedad modificada a {}%".format(nueva_humedad)
                )
                controlar_bomba()

    except (ValueError, KeyError):
        flash("No se pudo modificar la humedad.")

    return redirect(url_for("humedad"))


# Simulación del riego
@app.route("/simular_riego", methods=["POST"])
def simular_riego():

    controlar_bomba()

    if sistema["bomba"]:

        aumento = max(1, sistema["duracion"] // 2)

        sistema["humedad"] = min(
            100,
            sistema["humedad"] + aumento
        )

        registrar_evento(
            "Simulación de riego: humedad aumentó a {}%".format(
                sistema["humedad"]
            )
        )

        controlar_bomba()
        flash("La simulación de riego se realizó correctamente.")

    else:
        flash("La bomba está apagada. No se puede simular el riego.")

    return redirect(url_for("humedad"))


# Control manual y automático de la bomba
@app.route("/bomba", methods=["GET", "POST"])
def bomba():

    if request.method == "POST":

        accion = request.form.get("accion")

        if accion == "encender":
            sistema["modo"] = "Manual"

            if not sistema["bomba"]:
                sistema["bomba"] = True
                registrar_evento("Bomba encendida manualmente")

        elif accion == "apagar":
            sistema["modo"] = "Manual"

            if sistema["bomba"]:
                sistema["bomba"] = False
                registrar_evento("Bomba apagada manualmente")

        elif accion == "automatico":
            sistema["modo"] = "Automatico"
            registrar_evento("Modo automático activado")
            controlar_bomba()

        return redirect(url_for("bomba"))

    controlar_bomba()
    return render_template("bomba.html", sistema=sistema)


# Configuración
@app.route("/configuracion", methods=["GET", "POST"])
def configuracion():

    if request.method == "POST":

        try:
            minimo = int(request.form["humedad_minima"])
            duracion = int(request.form["duracion"])

            if 0 <= minimo <= 100 and 1 <= duracion <= 60:

                sistema["humedad_minima"] = minimo
                sistema["duracion"] = duracion

                registrar_evento("Configuración actualizada")
                controlar_bomba()

                flash("Configuración guardada correctamente.")

            else:
                flash("Revisa los valores permitidos.")

        except (ValueError, KeyError):
            flash("Introduce valores numéricos válidos.")

        return redirect(url_for("configuracion"))

    return render_template("configuracion.html", sistema=sistema)


# Historial
@app.route("/historial")
def historial():

    conexion = conectar()

    registros = conexion.execute(
        "SELECT * FROM historial ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    return render_template("historial.html", registros=registros)


# Limpiar historial
@app.route("/limpiar_historial", methods=["POST"])
def limpiar_historial():

    conexion = conectar()
    conexion.execute("DELETE FROM historial")
    conexion.commit()
    conexion.close()

    registrar_evento("Historial limpiado")

    return redirect(url_for("historial"))


# Crear la tabla al iniciar
crear_tabla()


if __name__ == "__main__":
    app.run(debug=True)
