import sqlite3
import os

# Define o caminho do banco de dados
CAMINHO_BANCO = os.environ.get(
    "DATABASE_PATH",
    "lava_rapido.db"
)

conexao = sqlite3.connect(CAMINHO_BANCO)

cursor = conexao.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        categoria TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor INTEGER NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
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