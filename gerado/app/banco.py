"""Conexão SQLite, criação das tabelas e carga inicial."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS salas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
      local TEXT NOT NULL CHECK (local IN ('SAO_PAULO', 'ARARAQUARA', 'COWORKING')),
      capacidade INTEGER NOT NULL CHECK (capacidade BETWEEN 1 AND 1000),
      recursos TEXT NOT NULL DEFAULT '[]',
      UNIQUE (nome COLLATE NOCASE, local)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reservas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sala_id INTEGER NOT NULL REFERENCES salas(id),
      responsavel_nome TEXT NOT NULL CHECK (length(responsavel_nome) BETWEEN 1 AND 200),
      responsavel_email TEXT NOT NULL CHECK (length(responsavel_email) BETWEEN 3 AND 254),
      titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
      participantes INTEGER NOT NULL CHECK (participantes >= 1),
      inicio TEXT NOT NULL,
      fim TEXT NOT NULL,
      status TEXT NOT NULL CHECK (status IN ('ATIVA', 'CANCELADA')),
      criada_em TEXT NOT NULL,
      cancelada_em TEXT,
      CHECK (fim > inicio)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_reservas_sala_inicio ON reservas (sala_id, inicio)",
]

# RF-03: seis salas fictícias, duas por local.
SALAS_INICIAIS = [
    ("Paulista", "SAO_PAULO", 8, ["TV", "VIDEOCONFERENCIA"]),
    ("Ibirapuera", "SAO_PAULO", 4, ["QUADRO"]),
    ("Laranjeira", "ARARAQUARA", 10, ["TV", "QUADRO"]),
    ("Morada do Sol", "ARARAQUARA", 6, ["VIDEOCONFERENCIA"]),
    ("Coworking Azul", "COWORKING", 12, ["TV", "VIDEOCONFERENCIA", "QUADRO"]),
    ("Coworking Verde", "COWORKING", 3, []),
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
    As salas iniciais não têm datas; `agora` não é usado.
    """
    if conn.execute("SELECT COUNT(*) FROM salas").fetchone()[0] > 0:
        return
    for nome, local, capacidade, recursos in SALAS_INICIAIS:
        conn.execute(
            "INSERT INTO salas (nome, local, capacidade, recursos) VALUES (?, ?, ?, ?)",
            (nome, local, capacidade, json.dumps(recursos)),
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
