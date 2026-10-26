"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS despesas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colaborador_nome TEXT NOT NULL CHECK (length(colaborador_nome) BETWEEN 1 AND 200),
  colaborador_email TEXT NOT NULL CHECK (length(colaborador_email) BETWEEN 3 AND 254),
  data TEXT NOT NULL CHECK (length(data) = 10),
  categoria TEXT NOT NULL CHECK (categoria IN ('TRANSPORTE', 'HOSPEDAGEM', 'ALIMENTACAO', 'OUTROS')),
  valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 200),
  comprovante TEXT NOT NULL CHECK (length(comprovante) BETWEEN 1 AND 200),
  situacao TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (situacao IN ('PENDENTE', 'APROVADA', 'RECUSADA', 'PAGA')),
  motivo_recusa TEXT,
  UNIQUE (colaborador_email, comprovante)
)""",
    "CREATE INDEX IF NOT EXISTS ix_despesas_data ON despesas (data)",
]

# RF-08: (nome, e-mail, dias antes de hoje, categoria, centavos, descrição, comprovante, situação, motivo)
_CARGA = [
    ("Ana Souza", "ana.souza@empresa.example", 1, "TRANSPORTE", 8550, "Táxi do aeroporto ao hotel", "NF-1001", "PENDENTE", None),
    ("Bruno Lima", "bruno.lima@empresa.example", 3, "HOSPEDAGEM", 38000, "Hotel, uma diária", "NF-2001", "APROVADA", None),
    ("Carla Mendes", "carla.mendes@empresa.example", 6, "ALIMENTACAO", 9500, "Jantar fora do roteiro", "NF-3001", "RECUSADA",
     "Despesa fora do período da viagem"),
    ("Ana Souza", "ana.souza@empresa.example", 10, "OUTROS", 4500, "Estacionamento", "NF-1002", "PAGA", None),
    ("Bruno Lima", "bruno.lima@empresa.example", 20, "ALIMENTACAO", 6000, "Almoço durante a viagem", "NF-2002", "PENDENTE", None),
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
    from app.repositorio import despesas as repo  # import local: o repositório não depende de banco.py

    if repo.contar(conn):
        return
    hoje = agora.date()
    for nome, email, dias, categoria, valor, descricao, comprovante, situacao, motivo in _CARGA:
        repo.inserir(conn, {
            "colaborador_nome": nome, "colaborador_email": email,
            "data": (hoje - timedelta(days=dias)).isoformat(), "categoria": categoria,
            "valor_centavos": valor, "descricao": descricao, "comprovante": comprovante,
            "situacao": situacao, "motivo_recusa": motivo,
        })


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
