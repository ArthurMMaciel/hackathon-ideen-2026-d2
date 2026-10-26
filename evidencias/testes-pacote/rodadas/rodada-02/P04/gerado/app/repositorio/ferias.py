"""SQL parametrizado de colaboradores e solicitações. Datas de férias como texto AAAA-MM-DD."""

import sqlite3
from datetime import date, datetime

from app.relogio import para_banco

_COLABORADOR_COLUNAS = """
  c.id, c.nome, c.email, c.equipe, c.saldo,
  c.saldo - COALESCE((SELECT SUM(s.dias) FROM solicitacoes s
                      WHERE s.colaborador_id = c.id AND s.situacao = 'SOLICITADA'), 0) AS saldo_disponivel
"""

SQL_LISTAR_COLABORADORES = f"SELECT {_COLABORADOR_COLUNAS} FROM colaboradores c ORDER BY c.equipe, c.nome, c.id"
SQL_OBTER_COLABORADOR = f"SELECT {_COLABORADOR_COLUNAS} FROM colaboradores c WHERE c.id = ?"
SQL_EMAIL_EXISTE = "SELECT 1 FROM colaboradores WHERE email = ? COLLATE NOCASE"
SQL_INSERIR_COLABORADOR = "INSERT INTO colaboradores (nome, email, equipe, saldo) VALUES (?, ?, ?, ?)"
SQL_ATUALIZAR_SALDO = "UPDATE colaboradores SET saldo = ? WHERE id = ?"
SQL_DIAS_PENDENTES = (
    "SELECT COALESCE(SUM(dias), 0) FROM solicitacoes WHERE colaborador_id = ? AND situacao = 'SOLICITADA'"
)

_SOLICITACAO_COLUNAS = """
  s.id, s.colaborador_id, c.nome AS colaborador_nome, c.equipe, s.inicio, s.fim, s.dias, s.situacao
"""
SQL_LISTAR_SOLICITACOES = (
    f"SELECT {_SOLICITACAO_COLUNAS} FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id "
    "ORDER BY s.inicio, s.id"
)
SQL_OBTER_SOLICITACAO = (
    f"SELECT {_SOLICITACAO_COLUNAS} FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id "
    "WHERE s.id = ?"
)
SQL_INSERIR_SOLICITACAO = (
    "INSERT INTO solicitacoes (colaborador_id, inicio, fim, dias, situacao, criada_em) "
    "VALUES (?, ?, ?, ?, 'SOLICITADA', ?)"
)
SQL_ATUALIZAR_SITUACAO = "UPDATE solicitacoes SET situacao = ? WHERE id = ?"
SQL_PERIODOS_ATIVOS_DO_COLABORADOR = (
    "SELECT inicio, fim FROM solicitacoes "
    "WHERE colaborador_id = ? AND situacao IN ('SOLICITADA', 'APROVADA') ORDER BY inicio"
)
SQL_APROVADAS_DA_EQUIPE = (
    "SELECT s.inicio, s.fim, c.nome FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id "
    "WHERE c.equipe = ? AND s.situacao = 'APROVADA' AND s.id <> ? "
    "ORDER BY s.inicio"
)
SQL_APROVADAS_NO_PERIODO = (
    "SELECT s.id AS solicitacao_id, s.colaborador_id, c.nome, c.equipe, s.inicio, s.fim "
    "FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id "
    "WHERE s.situacao = 'APROVADA' AND s.inicio <= ? AND s.fim >= ?"
)


def _d(texto: str) -> date:
    return date.fromisoformat(texto)


# ---------- Colaboradores ----------

def listar_colaboradores(conn: sqlite3.Connection) -> list[dict]:
    return [dict(linha) for linha in conn.execute(SQL_LISTAR_COLABORADORES)]


def obter_colaborador(conn: sqlite3.Connection, colaborador_id: int) -> dict | None:
    linha = conn.execute(SQL_OBTER_COLABORADOR, (colaborador_id,)).fetchone()
    return dict(linha) if linha else None


def email_existe(conn: sqlite3.Connection, email: str) -> bool:
    return conn.execute(SQL_EMAIL_EXISTE, (email,)).fetchone() is not None


def inserir_colaborador(conn: sqlite3.Connection, nome: str, email: str, equipe: str, saldo: int) -> int:
    return conn.execute(SQL_INSERIR_COLABORADOR, (nome, email, equipe, saldo)).lastrowid


def atualizar_saldo(conn: sqlite3.Connection, colaborador_id: int, saldo: int) -> None:
    conn.execute(SQL_ATUALIZAR_SALDO, (saldo, colaborador_id))


def dias_pendentes(conn: sqlite3.Connection, colaborador_id: int) -> int:
    return conn.execute(SQL_DIAS_PENDENTES, (colaborador_id,)).fetchone()[0]


# ---------- Solicitações ----------

def _solicitacao(linha: sqlite3.Row) -> dict:
    return dict(linha)


def listar_solicitacoes(conn: sqlite3.Connection) -> list[dict]:
    return [_solicitacao(linha) for linha in conn.execute(SQL_LISTAR_SOLICITACOES)]


def obter_solicitacao(conn: sqlite3.Connection, solicitacao_id: int) -> dict | None:
    linha = conn.execute(SQL_OBTER_SOLICITACAO, (solicitacao_id,)).fetchone()
    return _solicitacao(linha) if linha else None


def inserir_solicitacao(
    conn: sqlite3.Connection, colaborador_id: int, inicio: date, fim: date, dias: int, agora: datetime
) -> int:
    return conn.execute(
        SQL_INSERIR_SOLICITACAO, (colaborador_id, inicio.isoformat(), fim.isoformat(), dias, para_banco(agora))
    ).lastrowid


def atualizar_situacao(conn: sqlite3.Connection, solicitacao_id: int, situacao: str) -> None:
    conn.execute(SQL_ATUALIZAR_SITUACAO, (situacao, solicitacao_id))


def periodos_ativos_do_colaborador(conn: sqlite3.Connection, colaborador_id: int) -> list[tuple[date, date]]:
    linhas = conn.execute(SQL_PERIODOS_ATIVOS_DO_COLABORADOR, (colaborador_id,))
    return [(_d(l["inicio"]), _d(l["fim"])) for l in linhas]


def aprovadas_da_equipe(conn: sqlite3.Connection, equipe: str, ignorar_id: int) -> list[tuple[date, date, str]]:
    linhas = conn.execute(SQL_APROVADAS_DA_EQUIPE, (equipe, ignorar_id))
    return [(_d(l["inicio"]), _d(l["fim"]), l["nome"]) for l in linhas]


def aprovadas_no_periodo(conn: sqlite3.Connection, inicio: date, fim: date) -> list[dict]:
    linhas = conn.execute(SQL_APROVADAS_NO_PERIODO, (fim.isoformat(), inicio.isoformat()))
    return [{**dict(l), "inicio": _d(l["inicio"]), "fim": _d(l["fim"])} for l in linhas]
