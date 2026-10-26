"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS colaboradores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  email TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(email) BETWEEN 3 AND 254),
  equipe TEXT NOT NULL CHECK (equipe IN ('DADOS', 'PRODUTO', 'SUPORTE')),
  saldo INTEGER NOT NULL DEFAULT 30 CHECK (saldo BETWEEN 0 AND 365)
)""",
    """CREATE TABLE IF NOT EXISTS solicitacoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colaborador_id INTEGER NOT NULL REFERENCES colaboradores(id),
  inicio TEXT NOT NULL,
  fim TEXT NOT NULL,
  dias INTEGER NOT NULL CHECK (dias BETWEEN 5 AND 30),
  situacao TEXT NOT NULL CHECK (situacao IN ('SOLICITADA', 'APROVADA', 'REPROVADA', 'CANCELADA')),
  criada_em TEXT NOT NULL,
  CHECK (fim >= inicio)
)""",
    "CREATE INDEX IF NOT EXISTS ix_solicitacoes_colaborador ON solicitacoes (colaborador_id, situacao)",
    "CREATE INDEX IF NOT EXISTS ix_solicitacoes_periodo ON solicitacoes (situacao, inicio, fim)",
]

# RF-03: 9 colaboradores fictícios, 3 por equipe, saldo 30.
COLABORADORES_INICIAIS = [
    ("Ana Ribeiro", "ana.ribeiro@exemplo.com", "DADOS"),
    ("Bruno Carvalho", "bruno.carvalho@exemplo.com", "DADOS"),
    ("Carla Mendes", "carla.mendes@exemplo.com", "DADOS"),
    ("Diego Fontes", "diego.fontes@exemplo.com", "PRODUTO"),
    ("Elisa Moraes", "elisa.moraes@exemplo.com", "PRODUTO"),
    ("Fábio Teixeira", "fabio.teixeira@exemplo.com", "PRODUTO"),
    ("Gabriela Nunes", "gabriela.nunes@exemplo.com", "SUPORTE"),
    ("Hugo Pacheco", "hugo.pacheco@exemplo.com", "SUPORTE"),
    ("Isabela Prado", "isabela.prado@exemplo.com", "SUPORTE"),
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
    Aqui não há datas: só colaboradores com saldo padrão.
    """
    if conn.execute("SELECT COUNT(*) FROM colaboradores").fetchone()[0]:
        return
    conn.executemany(
        "INSERT INTO colaboradores (nome, email, equipe, saldo) VALUES (?, ?, ?, 30)",
        COLABORADORES_INICIAIS,
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
