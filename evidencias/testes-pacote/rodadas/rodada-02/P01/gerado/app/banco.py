"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS equipamentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patrimonio TEXT NOT NULL UNIQUE CHECK (patrimonio GLOB 'EQ-[0-9][0-9][0-9][0-9]'),
  tipo TEXT NOT NULL CHECK (tipo IN ('NOTEBOOK', 'PROJETOR', 'HEADSET')),
  descricao TEXT NOT NULL,
  situacao TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK (situacao IN ('DISPONIVEL', 'EMPRESTADO', 'MANUTENCAO'))
)""",
    """CREATE TABLE IF NOT EXISTS emprestimos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  equipamento_id INTEGER NOT NULL REFERENCES equipamentos(id),
  nome TEXT NOT NULL,
  email TEXT NOT NULL,
  data_retirada TEXT NOT NULL,
  data_prevista TEXT NOT NULL,
  data_devolucao TEXT,
  defeito INTEGER CHECK (defeito IN (0, 1)),
  status TEXT NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO', 'DEVOLVIDO')),
  CHECK (data_prevista >= data_retirada)
)""",
    "CREATE INDEX IF NOT EXISTS ix_emprestimos_email_status ON emprestimos (email, status)",
    "CREATE INDEX IF NOT EXISTS ix_emprestimos_retirada ON emprestimos (data_retirada)",
]

# RF-03: 3 notebooks, 2 projetores e 3 headsets, um headset em manutenção (PR-09). Dados fictícios.
EQUIPAMENTOS_INICIAIS = [
    ("EQ-0001", "NOTEBOOK", "Notebook 14 polegadas (unidade 1)", "DISPONIVEL"),
    ("EQ-0002", "NOTEBOOK", "Notebook 14 polegadas (unidade 2)", "DISPONIVEL"),
    ("EQ-0003", "NOTEBOOK", "Notebook 15 polegadas", "DISPONIVEL"),
    ("EQ-0004", "PROJETOR", "Projetor sala de reunião", "DISPONIVEL"),
    ("EQ-0005", "PROJETOR", "Projetor portátil", "DISPONIVEL"),
    ("EQ-0006", "HEADSET", "Headset com microfone (unidade 1)", "DISPONIVEL"),
    ("EQ-0007", "HEADSET", "Headset com microfone (unidade 2)", "DISPONIVEL"),
    ("EQ-0008", "HEADSET", "Headset sem fio", "MANUTENCAO"),
]


def caminho_padrao() -> str:
    return os.environ.get("APP_DB", "dados/app.db")


def conectar(caminho: str) -> sqlite3.Connection:
    # isolation_level=None: sem transação implícita; escritas usam transacao().
    conn = sqlite3.connect(caminho, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transacao(conn: sqlite3.Connection):
    """BEGIN IMMEDIATE trava a escrita: verificar e gravar acontecem sem corrida."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def carga_inicial(conn: sqlite3.Connection, agora: datetime) -> None:
    """Dados iniciais fictícios. Idempotente: só insere quando a tabela está vazia.

    Datas relativas ("futura", "atrasado", "há 3 dias") são calculadas a partir de `agora`,
    que é o relógio de teste nos testes e APP_AGORA ou a hora real no servidor.
    Os equipamentos iniciais não têm datas, então `agora` não é usado.
    """
    if conn.execute("SELECT COUNT(*) FROM equipamentos").fetchone()[0]:
        return
    conn.executemany(
        "INSERT INTO equipamentos (patrimonio, tipo, descricao, situacao) VALUES (?, ?, ?, ?)",
        EQUIPAMENTOS_INICIAIS,
    )


def iniciar(caminho: str, agora: datetime) -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conn = conectar(caminho)
    try:
        with transacao(conn):
            for ddl in ESQUEMA:
                conn.execute(ddl)
            carga_inicial(conn, agora)
    finally:
        conn.close()


def obter_conexao(request: Request):
    """Dependência do FastAPI: uma conexão por requisição."""
    conn = conectar(request.app.state.caminho_db)
    try:
        yield conn
    finally:
        conn.close()
