"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, time, timedelta
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS turmas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
      inicio TEXT NOT NULL,
      duracao_minutos INTEGER NOT NULL CHECK (duracao_minutos BETWEEN 1 AND 1440),
      modalidade TEXT NOT NULL CHECK (modalidade IN ('PRESENCIAL', 'ONLINE')),
      vagas INTEGER NOT NULL CHECK (vagas BETWEEN 1 AND 50)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inscricoes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      turma_id INTEGER NOT NULL REFERENCES turmas(id),
      nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
      email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 254),
      situacao TEXT NOT NULL CHECK (situacao IN ('CONFIRMADA', 'ESPERA', 'CANCELADA', 'PRESENTE', 'AUSENTE')),
      criada_em TEXT NOT NULL
    )
    """,
    # RN-07: no máximo uma inscrição ativa por e-mail e turma (defesa no banco)
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inscricao_ativa
      ON inscricoes (turma_id, email) WHERE situacao IN ('CONFIRMADA', 'ESPERA')
    """,
    "CREATE INDEX IF NOT EXISTS ix_inscricoes_turma ON inscricoes (turma_id, situacao)",
]

# PR-11: 3 turmas fictícias a 7, 14 e 21 dias da primeira inicialização, às 09:00.
TURMAS_INICIAIS = [
    ("Boas práticas de segurança da informação", 7, 120, "PRESENCIAL", 20),
    ("Introdução à análise de dados", 14, 180, "ONLINE", 30),
    ("Comunicação não violenta", 21, 90, "PRESENCIAL", 10),
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
    """Dados iniciais fictícios. Idempotente: só insere quando a tabela está vazia."""
    from app.repositorio import turmas as repo_turmas

    if repo_turmas.contar(conn) > 0:
        return
    for titulo, dias, duracao, modalidade, vagas in TURMAS_INICIAIS:
        dia = (agora + timedelta(days=dias)).date()
        inicio = datetime.combine(dia, time(9, 0), tzinfo=agora.tzinfo)
        repo_turmas.inserir(conn, titulo, inicio, duracao, modalidade, vagas)


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
