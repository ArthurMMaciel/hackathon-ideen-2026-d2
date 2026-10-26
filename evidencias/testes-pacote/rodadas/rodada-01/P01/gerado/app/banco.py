"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS equipamentos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patrimonio TEXT NOT NULL UNIQUE CHECK (patrimonio GLOB 'EQ-[0-9][0-9][0-9][0-9]'),
      tipo TEXT NOT NULL CHECK (tipo IN ('NOTEBOOK', 'PROJETOR', 'HEADSET')),
      descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 200),
      situacao TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK (situacao IN ('DISPONIVEL', 'EMPRESTADO', 'MANUTENCAO'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS emprestimos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      equipamento_id INTEGER NOT NULL REFERENCES equipamentos(id),
      nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
      email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 200),
      data_retirada TEXT NOT NULL,
      data_prevista TEXT NOT NULL CHECK (data_prevista >= data_retirada),
      data_devolucao TEXT,
      defeito INTEGER CHECK (defeito IN (0, 1)),
      status TEXT NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO', 'DEVOLVIDO')),
      criado_em TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_emprestimo_aberto_por_equipamento
      ON emprestimos(equipamento_id) WHERE status = 'ABERTO'
    """,
    "CREATE INDEX IF NOT EXISTS ix_emprestimos_email_status ON emprestimos(email, status)",
]

# RF-12: 3 notebooks, 2 projetores e 3 headsets, um headset em manutenção. Dados fictícios.
EQUIPAMENTOS_INICIAIS: list[tuple[str, str, str, str]] = [
    ("EQ-0001", "NOTEBOOK", "Notebook 14 polegadas - unidade 1", "DISPONIVEL"),
    ("EQ-0002", "NOTEBOOK", "Notebook 14 polegadas - unidade 2", "DISPONIVEL"),
    ("EQ-0003", "NOTEBOOK", "Notebook 15 polegadas - unidade 3", "DISPONIVEL"),
    ("EQ-0004", "PROJETOR", "Projetor multimídia - sala A", "DISPONIVEL"),
    ("EQ-0005", "PROJETOR", "Projetor portátil - sala B", "DISPONIVEL"),
    ("EQ-0006", "HEADSET", "Headset USB - unidade 1", "DISPONIVEL"),
    ("EQ-0007", "HEADSET", "Headset USB - unidade 2", "DISPONIVEL"),
    ("EQ-0008", "HEADSET", "Headset sem fio - unidade 3", "MANUTENCAO"),
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


def carga_inicial(conn: sqlite3.Connection) -> None:
    """Dados iniciais fictícios. Idempotente: só insere quando a tabela está vazia."""
    if conn.execute("SELECT COUNT(*) FROM equipamentos").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO equipamentos (patrimonio, tipo, descricao, situacao) VALUES (?, ?, ?, ?)",
        EQUIPAMENTOS_INICIAIS,
    )


def iniciar(caminho: str) -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conn = conectar(caminho)
    try:
        with transacao(conn):
            for ddl in ESQUEMA:
                conn.execute(ddl)
            carga_inicial(conn)
    finally:
        conn.close()


def obter_conexao(request: Request):
    """Dependência do FastAPI: uma conexão por requisição."""
    conn = conectar(request.app.state.caminho_db)
    try:
        yield conn
    finally:
        conn.close()
