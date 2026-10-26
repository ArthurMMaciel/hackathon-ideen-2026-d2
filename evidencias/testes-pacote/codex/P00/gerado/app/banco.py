"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS salas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL CHECK(length(trim(nome)) BETWEEN 1 AND 200),
      local TEXT NOT NULL CHECK(local IN ('SAO_PAULO','ARARAQUARA','COWORKING')),
      capacidade INTEGER NOT NULL CHECK(capacidade BETWEEN 1 AND 2147483647),
      recursos TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS reservas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sala_id INTEGER NOT NULL REFERENCES salas(id),
      responsavel_nome TEXT NOT NULL,
      responsavel_email TEXT NOT NULL,
      titulo TEXT NOT NULL,
      participantes INTEGER NOT NULL CHECK(participantes > 0),
      inicio TEXT NOT NULL,
      fim TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('ATIVA','CANCELADA')))""",
    "CREATE INDEX IF NOT EXISTS idx_reservas_sala_intervalo ON reservas(sala_id,status,inicio,fim)",
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
    """
    import json

    if conn.execute("SELECT 1 FROM salas LIMIT 1").fetchone():
        return
    salas = [
        ("Paulista", "SAO_PAULO", 8, ["TV", "VIDEOCONFERENCIA"]),
        ("Ibirapuera", "SAO_PAULO", 4, ["QUADRO"]),
        ("Centro", "ARARAQUARA", 6, ["TV", "QUADRO"]),
        ("Jardim", "ARARAQUARA", 10, ["VIDEOCONFERENCIA"]),
        ("Hub A", "COWORKING", 3, ["TV"]),
        ("Hub B", "COWORKING", 12, ["TV", "VIDEOCONFERENCIA", "QUADRO"]),
    ]
    conn.executemany(
        "INSERT INTO salas(nome,local,capacidade,recursos) VALUES (?,?,?,?)",
        [(nome, local, capacidade, json.dumps(recursos)) for nome, local, capacidade, recursos in salas],
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
