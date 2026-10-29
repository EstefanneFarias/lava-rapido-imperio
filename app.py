
from flask import Flask, render_template, request, redirect, url_for
from datetime import date
import sqlite3
from decimal import Decimal, InvalidOperation

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

        try:
            valor = Decimal(request.form["valor"].replace(",", "."))

            if not valor.is_finite() or valor <= 0:
                raise InvalidOperation

            valor_centavos = int(valor * 100)

        except InvalidOperation:
            hoje = date.today().isoformat()

            return render_template(
                "registrar_despesas.html",
                hoje=hoje,
                salvo=None,
                despesas=[],
                data_consulta=hoje,
                total_despesas=0,
                erro="Informe um valor válido e maior que zero."
            )

        conexao = sqlite3.connect("lava_rapido.db")
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO despesas (data, categoria, descricao, valor)
            VALUES (?, ?, ?, ?)
        """, (data, categoria, descricao, valor_centavos))

        conexao.commit()
        conexao.close()

        return redirect(url_for("registrar_despesas", salvo=1))

    # Define a data consultada; se nenhuma for informada, usa hoje
    data_consulta = request.args.get("data", date.today().isoformat())

    conexao = sqlite3.connect("lava_rapido.db")
    cursor = conexao.cursor()

    # Consulta somente as despesas da data escolhida
    cursor.execute("""
        SELECT data, categoria, descricao, valor
        FROM despesas
        WHERE data = ?
        ORDER BY rowid DESC
    """, (data_consulta,))

    despesas = cursor.fetchall()

    # Calcula o total das despesas da data escolhida
    cursor.execute("""
        SELECT SUM(valor)
        FROM despesas
        WHERE data = ?
    """, (data_consulta,))

    total_despesas = cursor.fetchone()[0] or 0

    conexao.close()

    hoje = date.today().isoformat()

    return render_template(
        "registrar_despesas.html",
        hoje=hoje,
        salvo=request.args.get("salvo"),
        despesas=despesas,
        data_consulta=data_consulta,
        total_despesas=total_despesas
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
