
import unittest
import app
import tempfile
import sqlite3
import os
from contextlib import closing


class TestAplicacao(unittest.TestCase):

    def setUp(self):
        # Cria um diretório temporário para os testes
        self.temp_dir = tempfile.TemporaryDirectory()

        # Define o caminho do banco de dados de teste
        self.db_path = os.path.join(self.temp_dir.name, "teste.db")

        # Cria as tabelas no banco temporário
        conexao = sqlite3.connect(self.db_path)

        conexao.execute("""
            CREATE TABLE despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor INTEGER NOT NULL
            )
        """)

        conexao.execute("""
            CREATE TABLE servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                veiculo TEXT NOT NULL,
                placa TEXT,
                valor INTEGER NOT NULL,
                pagamento TEXT NOT NULL,
                caixinha INTEGER NOT NULL DEFAULT 0
            )
        """)

        conexao.commit()
        conexao.close()

        # Redireciona a conexão da aplicação para o banco de teste
        self.conexao_original = app.conectar_banco

        app.conectar_banco = lambda: closing(
            sqlite3.connect(self.db_path)
        )

        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    def tearDown(self):
        # Restaura a conexão original
        app.conectar_banco = self.conexao_original

        # Remove o banco temporário
        self.temp_dir.cleanup()

    def test_pagina_inicial(self):
        resposta = self.client.get("/")

        self.assertEqual(resposta.status_code, 200)

    def test_pagina_registrar_servico(self):
        resposta = self.client.get("/registrar-servico")

        self.assertEqual(resposta.status_code, 200)

    def test_pagina_registrar_despesas(self):
        resposta = self.client.get("/registrar-despesas")

        self.assertEqual(resposta.status_code, 200)

    def test_registrar_despesa(self):
        resposta = self.client.post("/registrar-despesas", data={
            "data": "2026-10-30",
            "categoria": "Café",
            "descricao": "Compra de teste",
            "valor": "15,00"
        })

        self.assertEqual(resposta.status_code, 302)

        with app.conectar_banco() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM despesas")
            despesa = cursor.fetchone()

        self.assertIsNotNone(despesa)
        self.assertEqual(despesa[2], "Café")
        self.assertEqual(despesa[3], "Compra de teste")
        self.assertEqual(despesa[4], 1500)

    def test_rejeitar_despesa_com_valor_zero(self):
        resposta = self.client.post("/registrar-despesas", data={
            "data": "2026-10-30",
            "categoria": "Café",
            "descricao": "Teste de valor inválido",
            "valor": "0,00"
        })

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(
            b"Informe um valor v\xc3\xa1lido e maior que zero.",
            resposta.data
        )

        # Verifica se a despesa inválida não foi salva
        with app.conectar_banco() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM despesas")
            quantidade = cursor.fetchone()[0]

        self.assertEqual(quantidade, 0)

    def test_converter_valor_centavos(self):
        resultado = app.converter_valor_centavos("15,00")

        self.assertEqual(resultado, 1500)