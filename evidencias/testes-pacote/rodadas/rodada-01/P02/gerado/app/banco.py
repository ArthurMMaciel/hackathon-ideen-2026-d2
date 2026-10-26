"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import Request

from app import relogio

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS despesas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      colaborador_nome TEXT NOT NULL CHECK (length(colaborador_nome) BETWEEN 1 AND 200),
      colaborador_email TEXT NOT NULL CHECK (length(colaborador_email) BETWEEN 3 AND 200),
      data_despesa TEXT NOT NULL,
      categoria TEXT NOT NULL CHECK (categoria IN ('TRANSPORTE','HOSPEDAGEM','ALIMENTACAO','OUTROS')),
      valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
      descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 200),
      numero_comprovante TEXT NOT NULL CHECK (length(numero_comprovante) BETWEEN 1 AND 200),
      situacao TEXT NOT NULL DEFAULT 'PENDENTE'
        CHECK (situacao IN ('PENDENTE','APROVADA','RECUSADA','PAGA')),
      motivo_recusa TEXT,
      criada_em TEXT NOT NULL,
      atualizada_em TEXT NOT NULL,
      UNIQUE (colaborador_email, numero_comprovante)
    )
    """,
]

# RF-11: 5 despesas de exemplo, fictícias, em situações diferentes.
# (nome, e-mail, dias atrás, categoria, centavos, descrição, comprovante, situação, motivo)
DESPESAS_EXEMPLO = [
    ("Ana Ficticia", "ana.ficticia@empresa.example", 2, "ALIMENTACAO", 4590,
     "Almoço com cliente", "NF-1001", "PENDENTE", None),
    ("Bruno Exemplo", "bruno.exemplo@empresa.example", 5, "TRANSPORTE", 23000,
     "Passagem de ônibus", "NF-2001", "PENDENTE", None),
    ("Ana Ficticia", "ana.ficticia@empresa.example", 10, "HOSPEDAGEM", 38000,
     "Hotel, uma diária", "NF-1002", "APROVADA", None),
    ("Carla Modelo", "carla.modelo@empresa.example", 12, "OUTROS", 7550,
     "Material de apresentação", "NF-3001", "RECUSADA", "Despesa sem relação com a viagem"),
    ("Bruno Exemplo", "bruno.exemplo@empresa.example", 20, "ALIMENTACAO", 9800,
     "Jantar", "NF-2002", "PAGA", None),
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
    from app.repositorio import despesas as repo  # import local: repositorio não depende de banco

    if conn.execute("SELECT COUNT(*) FROM despesas").fetchone()[0] > 0:
        return
    agora = relogio.agora()  # PR-11: datas relativas ao dia de início (respeita APP_AGORA)
    for nome, email, dias, categoria, centavos, descricao, comprovante, situacao, motivo in DESPESAS_EXEMPLO:
        repo.inserir(
            conn,
            {
                "colaborador_nome": nome,
                "colaborador_email": email,
                "data_despesa": agora.date() - timedelta(days=dias),
                "categoria": categoria,
                "valor_centavos": centavos,
                "descricao": descricao,
                "numero_comprovante": comprovante,
                "situacao": situacao,
                "motivo_recusa": motivo,
            },
            agora,
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
