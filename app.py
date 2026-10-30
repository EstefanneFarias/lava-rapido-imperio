
from flask import Flask, render_template, request, redirect, url_for
from datetime import date
import sqlite3
from decimal import Decimal, InvalidOperation
from contextlib import closing

app = Flask(__name__)


def conectar_banco():
    return closing(sqlite3.connect("lava_rapido.db"))


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/registrar-servico")
def registrar_servico():
    return render_template("registrar_servico.html")


def converter_valor_centavos(valor_digitado):
    # Converte o valor informado para número decimal
    valor = Decimal(valor_digitado.replace(",", "."))

    # Verifica se o valor é válido e maior que zero
    if not valor.is_finite() or valor <= 0:
        raise InvalidOperation

    # Converte reais para centavos
    return int(valor * 100)


@app.route("/registrar-despesas", methods=["GET", "POST"])
def registrar_despesas():
    if request.method == "POST":
        data = request.form["data"]
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]

        try:
            valor_centavos = converter_valor_centavos(
                request.form["valor"]
            )
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

        # Salva a despesa no banco de dados
        with conectar_banco() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                INSERT INTO despesas (data, categoria, descricao, valor)
                VALUES (?, ?, ?, ?)
            """, (data, categoria, descricao, valor_centavos))

            conexao.commit()

        return redirect(url_for("registrar_despesas", salvo=1))

    # Define a data consultada; se nenhuma for informada, usa hoje
    data_consulta = request.args.get("data", date.today().isoformat())

    # Consulta as despesas e calcula o total
    with conectar_banco() as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT data, categoria, descricao, valor
            FROM despesas
            WHERE data = ?
            ORDER BY rowid DESC
        """, (data_consulta,))

        despesas = cursor.fetchall()

        cursor.execute("""
            SELECT SUM(valor)
            FROM despesas
            WHERE data = ?
        """, (data_consulta,))

        total_despesas = cursor.fetchone()[0] or 0

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
