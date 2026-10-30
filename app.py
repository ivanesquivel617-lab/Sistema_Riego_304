
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Datos principales del sistema
sistema = {
    "humedad": 35,
    "bomba": False,
    "modo": "Automatico",
    "humedad_minima": 30,
    "duracion": 10,
    "historial": []
}


# Registrar los movimientos del sistema
def registrar_evento(mensaje):
    hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    sistema["historial"].insert(
        0, f"{hora} - {mensaje}"
    )


# Control automático de la bomba
def controlar_bomba():
    if sistema["modo"] == "Automatico":
        if sistema["humedad"] < sistema["humedad_minima"]:
            sistema["bomba"] = True
        else:
            sistema["bomba"] = False


# Página principal
@app.route("/")
def index():
    controlar_bomba()

    return render_template(
        "index.html",
        sistema=sistema
    )


# Página de humedad
@app.route("/humedad", methods=["GET", "POST"])
def humedad():

    if request.method == "POST":
        try:
            valor = int(request.form.get("humedad", -1))

            if 0 <= valor <= 100:
                sistema["humedad"] = valor

                registrar_evento(
                    f"Humedad actualizada a {valor}%"
                )

                controlar_bomba()

        except ValueError:
            pass

        return redirect(url_for("humedad"))

    return render_template(
        "humedad.html",
        sistema=sistema
    )


# Control de la bomba
@app.route("/bomba", methods=["GET", "POST"])
def bomba():

    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "encender":
            sistema["modo"] = "Manual"
            sistema["bomba"] = True
            registrar_evento("Bomba encendida manualmente")

        elif accion == "apagar":
            sistema["modo"] = "Manual"
            sistema["bomba"] = False
            registrar_evento("Bomba apagada manualmente")

        elif accion == "automatico":
            sistema["modo"] = "Automatico"
            controlar_bomba()
            registrar_evento("Modo automático activado")

        return redirect(url_for("bomba"))

    return render_template(
        "bomba.html",
        sistema=sistema
    )


# Configuración del sistema
@app.route("/configuracion", methods=["GET", "POST"])
def configuracion():

    if request.method == "POST":
        try:
            minima = int(request.form.get("humedad_minima", -1))
            duracion = int(request.form.get("duracion", 0))

            if 0 <= minima <= 100 and 1 <= duracion <= 60:
                sistema["humedad_minima"] = minima
                sistema["duracion"] = duracion

                controlar_bomba()

                registrar_evento(
                    f"Configuración modificada: humedad mínima {minima}%"
                )

        except ValueError:
            pass

        return redirect(url_for("configuracion"))

    return render_template(
        "configuracion.html",
        sistema=sistema
    )


# Historial de actividades
@app.route("/historial")
def historial():

    return render_template(
        "historial.html",
        sistema=sistema
    )


# Borrar historial
@app.route("/limpiar_historial", methods=["POST"])
def limpiar_historial():

    sistema["historial"].clear()

    registrar_evento("Historial limpiado")

    return redirect(url_for("historial"))


if __name__ == "__main__":
    app.run(debug=True)
