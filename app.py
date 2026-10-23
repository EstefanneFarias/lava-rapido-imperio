
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/registrar-servico")
def registrar_servico():
    return render_template("registrar_servico.html")


@app.route("/registrar-despesas")
def registrar_despesas():
    return render_template("registrar_despesas.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

