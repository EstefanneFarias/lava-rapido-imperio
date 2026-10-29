
from flask import Flask, render_template, request, redirect, url_for
from datetime import date
import sqlite3
from decimal import Decimal

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/registrar-servico")
def registrar_servico():
    return render_template("registrar_servico.html")

@app.route("/registrar-despesas", methods=["GET", "POST"])
def registrar_despesas():
    if request.method == "POST":
        data = request.form["data"]
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]
        valor = request.form["valor"]

        valor = Decimal(valor.replace(",", "."))
        valor_centavos = int(valor * 100)

        conexao = sqlite3.connect("lava_rapido.db")
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO despesas (data, categoria, descricao, valor)
            VALUES (?, ?, ?, ?)
        """, (data, categoria, descricao, valor_centavos))

        conexao.commit()
        conexao.close()
        return redirect(url_for("registrar_despesas", salvo=1))

    conexao = sqlite3.connect("lava_rapido.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT data, categoria, descricao, valor
        FROM despesas
        ORDER BY data DESC, rowid DESC
    """)

    despesas = cursor.fetchall()
    conexao.close()
        
    hoje = date.today().isoformat()

    return render_template("registrar_despesas.html", hoje=hoje, salvo=request.args.get("salvo"), despesas=despesas)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

