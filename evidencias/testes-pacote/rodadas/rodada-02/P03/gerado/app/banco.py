"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Request

from app.relogio import FUSO, para_banco

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS turmas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  inicio TEXT NOT NULL,
  duracao_minutos INTEGER NOT NULL CHECK (duracao_minutos BETWEEN 1 AND 1440),
  modalidade TEXT NOT NULL CHECK (modalidade IN ('PRESENCIAL', 'ONLINE')),
  vagas INTEGER NOT NULL CHECK (vagas BETWEEN 1 AND 50)
)""",
    """CREATE TABLE IF NOT EXISTS inscricoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  turma_id INTEGER NOT NULL REFERENCES turmas(id),
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 254),
  situacao TEXT NOT NULL CHECK (situacao IN ('CONFIRMADA', 'ESPERA', 'CANCELADA', 'PRESENTE', 'AUSENTE')),
  criada_em TEXT NOT NULL,
  atualizada_em TEXT NOT NULL
)""",
    "CREATE INDEX IF NOT EXISTS ix_inscricoes_turma ON inscricoes (turma_id, id)",
    # RN-05: no máximo uma inscrição ativa por e-mail e turma (defesa no banco, além do domínio).
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_inscricao_ativa ON inscricoes (turma_id, email)
  WHERE situacao IN ('CONFIRMADA', 'ESPERA')""",
]

# RF-03: três turmas futuras, (título, dias a partir de agora, hora local, duração, modalidade, vagas).
TURMAS_INICIAIS = [
    ("Integração de novos colaboradores", 7, 9, 120, "PRESENCIAL", 20),
    ("Segurança da informação no dia a dia", 14, 14, 90, "ONLINE", 50),
    ("Planilhas: fórmulas e tabelas dinâmicas", 21, 10, 240, "PRESENCIAL", 12),
]

SQL_CONTAR_TURMAS = "SELECT COUNT(*) FROM turmas"
SQL_INSERIR_TURMA_INICIAL = (
    "INSERT INTO turmas (titulo, inicio, duracao_minutos, modalidade, vagas) VALUES (?, ?, ?, ?, ?)"
)


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
    if conn.execute(SQL_CONTAR_TURMAS).fetchone()[0] > 0:
        return
    local = agora.astimezone(FUSO)
    for titulo, dias, hora, duracao, modalidade, vagas in TURMAS_INICIAIS:
        dia = (local + timedelta(days=dias)).date()
        inicio = datetime(dia.year, dia.month, dia.day, hora, 0, tzinfo=FUSO)
        conn.execute(SQL_INSERIR_TURMA_INICIAL, (titulo, para_banco(inicio), duracao, modalidade, vagas))


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
