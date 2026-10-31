
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

    # Define a data de hoje no formato usado pelo banco de dados
    hoje = date.today().isoformat()

    # Consulta a quantidade de serviços e o total recebido no dia
    with conectar_banco() as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(valor), 0)
            FROM servicos
            WHERE data = ?
        """, (hoje,))

        quantidade_servicos, total_recebido = cursor.fetchone()

    # Envia os resultados para a página inicial
    return render_template(
        "index.html",
        quantidade_servicos=quantidade_servicos,
        total_recebido=total_recebido
    )


@app.route("/historico-servicos")
def historico_servicos():

    # Define a data consultada; se nenhuma for informada, usa hoje
    data_consulta = request.args.get("data", date.today().isoformat())

    # Consulta somente os serviços registrados na data escolhida
    with conectar_banco() as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT data, veiculo, placa, valor, pagamento, caixinha, id
            FROM servicos
            WHERE data = ?
            ORDER BY id DESC
        """, (data_consulta,))

        servicos = cursor.fetchall()

    return render_template(
        "historico_servicos.html",
        servicos=servicos,
        data_consulta=data_consulta
    )


@app.route("/editar-servico/<int:id>", methods=["GET", "POST"])
def editar_servico(id):

    # Busca o serviço pelo ID recebido na URL
    with conectar_banco() as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, data, veiculo, placa, valor, pagamento, caixinha
            FROM servicos
            WHERE id = ?
        """, (id,))

        servico = cursor.fetchone()

    # Verifica se o serviço existe
    if servico is None:
        return "Serviço não encontrado."

    if request.method == "POST":

        # Recebe as informações alteradas no formulário
        veiculo = request.form["veiculo"].strip()
        placa = request.form["placa"].strip()
        pagamento = request.form["pagamento"]

        try:
            # Verifica se o nome do veículo foi preenchido
            if not veiculo:
                raise ValueError

            # Converte o valor do serviço para centavos
            valor_centavos = converter_valor_centavos(
                request.form["valor"]
            )

            # A caixinha pode ficar vazia; nesse caso, considera zero
            valor_caixinha = request.form["caixinha"].strip() or "0"

            valor_caixinha = Decimal(
                valor_caixinha.replace(",", ".")
            )

            # Verifica se a caixinha é válida e não negativa
            if not valor_caixinha.is_finite() or valor_caixinha < 0:
                raise InvalidOperation

            caixinha_centavos = int(valor_caixinha * 100)

        except (InvalidOperation, ValueError):
            return render_template(
                "editar_servico.html",
                servico=servico,
                erro="Preencha o veículo e informe valores válidos."
            )

        # Atualiza as informações do serviço no banco de dados
        with conectar_banco() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                UPDATE servicos
                SET veiculo = ?, placa = ?, valor = ?,
                    pagamento = ?, caixinha = ?
                WHERE id = ?
            """, (
                veiculo,
                placa,
                valor_centavos,
                pagamento,
                caixinha_centavos,
                id
            ))

            conexao.commit()

        # Retorna ao histórico da mesma data do serviço
        return redirect(
            url_for("historico_servicos", data=servico[1])
        )

    return render_template(
        "editar_servico.html",
        servico=servico
    )


@app.route("/registrar-servico", methods=["GET", "POST"])
def registrar_servico():
    if request.method == "POST":

        # Define a data atual no formato ISO para salvar no banco de dados
        data = date.today().isoformat()

        # Recebe os dados enviados pelo formulário
        veiculo = request.form["veiculo"]
        placa = request.form["placa"]
        pagamento = request.form["pagamento"]

        try:
            valor_centavos = converter_valor_centavos(
                request.form["valor"]
            )

            # A caixinha pode ser zero
            valor_caixinha = request.form["caixinha"].strip() or "0"
            caixinha_centavos = int(
                Decimal(valor_caixinha.replace(",", ".")) * 100
            )

            if caixinha_centavos < 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            return render_template(
                "registrar_servico.html",
                erro="Informe valores válidos para o serviço e a caixinha."
            )

        # Salva o serviço no banco de dados
        with conectar_banco() as conexao:
            cursor = conexao.cursor()

            cursor.execute("""
                INSERT INTO servicos
                (data, veiculo, placa, valor, pagamento, caixinha)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data,
                veiculo,
                placa,
                valor_centavos,
                pagamento,
                caixinha_centavos
            ))

            conexao.commit()

        return redirect(url_for("registrar_servico", salvo=1))

    return render_template(
        "registrar_servico.html",
        salvo=request.args.get("salvo")
    )


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

        # Recebe os dados enviados pelo formulário de despesas
        data = request.form["data"]
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]

        try:
            valor_centavos = converter_valor_centavos(
                request.form["valor"]
            )
        except InvalidOperation:

            # Define a data atual no formato ISO para o formulário
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

        # Converte as datas para o formato brasileiro antes de exibir
        despesas = [
            (
                date.fromisoformat(data).strftime("%d/%m/%Y"),
                categoria,
                descricao,
                valor
            )
            for data, categoria, descricao, valor in despesas
        ]

        cursor.execute("""
            SELECT SUM(valor)
            FROM despesas
            WHERE data = ?
        """, (data_consulta,))

        total_despesas = cursor.fetchone()[0] or 0

    # Define a data atual no formato ISO para o formulário
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
