"""SQL parametrizado de colaboradores e solicitações."""

import sqlite3
from datetime import date, datetime

from app import relogio
from app.dominio.ferias import Periodo

_SELECT_COLABORADOR = """
SELECT c.id, c.nome, c.email, c.equipe, c.saldo,
       c.saldo - COALESCE((SELECT SUM(s.dias) FROM solicitacoes s
                           WHERE s.colaborador_id = c.id AND s.situacao = 'SOLICITADA'), 0) AS saldo_disponivel
FROM colaboradores c
"""

_SELECT_SOLICITACAO = """
SELECT s.id, s.colaborador_id, c.nome AS colaborador_nome, c.equipe, s.inicio, s.fim, s.dias,
       s.situacao, s.criado_em
FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id
"""


# Consultas completas como constantes: nenhum SQL é montado em tempo de execução.
_LISTAR_COLABORADORES = _SELECT_COLABORADOR + " ORDER BY c.equipe, c.nome, c.id"
_OBTER_COLABORADOR = _SELECT_COLABORADOR + " WHERE c.id = ?"
_LISTAR_SOLICITACOES = _SELECT_SOLICITACAO + """
WHERE (? IS NULL OR s.situacao = ?) AND (? IS NULL OR s.colaborador_id = ?)
ORDER BY s.inicio, s.id"""
_OBTER_SOLICITACAO = _SELECT_SOLICITACAO + " WHERE s.id = ?"


def _colaborador(linha: sqlite3.Row) -> dict:
    return dict(linha)


def _solicitacao(linha: sqlite3.Row) -> dict:
    d = dict(linha)
    d["criado_em"] = relogio.do_banco(d["criado_em"]).isoformat()
    return d


# Colaboradores

def listar_colaboradores(conn: sqlite3.Connection) -> list[dict]:
    linhas = conn.execute(_LISTAR_COLABORADORES).fetchall()
    return [_colaborador(l) for l in linhas]


def obter_colaborador(conn: sqlite3.Connection, colaborador_id: int) -> dict | None:
    linha = conn.execute(_OBTER_COLABORADOR, (colaborador_id,)).fetchone()
    return _colaborador(linha) if linha else None


def email_existe(conn: sqlite3.Connection, email: str) -> bool:
    return conn.execute("SELECT 1 FROM colaboradores WHERE email = ? COLLATE NOCASE", (email,)).fetchone() is not None


def inserir_colaborador(conn: sqlite3.Connection, nome: str, email: str, equipe: str, saldo: int) -> int:
    cur = conn.execute(
        "INSERT INTO colaboradores (nome, email, equipe, saldo) VALUES (?, ?, ?, ?)", (nome, email, equipe, saldo)
    )
    return cur.lastrowid


def atualizar_saldo(conn: sqlite3.Connection, colaborador_id: int, saldo: int) -> None:
    conn.execute("UPDATE colaboradores SET saldo = ? WHERE id = ?", (saldo, colaborador_id))


# Solicitações

def listar_solicitacoes(conn: sqlite3.Connection, situacao: str | None, colaborador_id: int | None) -> list[dict]:
    linhas = conn.execute(_LISTAR_SOLICITACOES, (situacao, situacao, colaborador_id, colaborador_id)).fetchall()
    return [_solicitacao(l) for l in linhas]


def obter_solicitacao(conn: sqlite3.Connection, solicitacao_id: int) -> dict | None:
    linha = conn.execute(_OBTER_SOLICITACAO, (solicitacao_id,)).fetchone()
    return _solicitacao(linha) if linha else None


def periodos_ativos_do_colaborador(conn: sqlite3.Connection, colaborador_id: int) -> list[Periodo]:
    linhas = conn.execute(
        "SELECT inicio, fim FROM solicitacoes WHERE colaborador_id = ? AND situacao IN ('SOLICITADA', 'APROVADA')",
        (colaborador_id,),
    ).fetchall()
    return [Periodo(date.fromisoformat(l["inicio"]), date.fromisoformat(l["fim"])) for l in linhas]


def periodos_aprovados_da_equipe(conn: sqlite3.Connection, equipe: str, ignorar_id: int) -> list[Periodo]:
    linhas = conn.execute(
        """SELECT s.inicio, s.fim FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id
           WHERE c.equipe = ? AND s.situacao = 'APROVADA' AND s.id <> ?""",
        (equipe, ignorar_id),
    ).fetchall()
    return [Periodo(date.fromisoformat(l["inicio"]), date.fromisoformat(l["fim"])) for l in linhas]


def inserir_solicitacao(conn: sqlite3.Connection, colaborador_id: int, periodo: Periodo, dias: int,
                        agora: datetime) -> int:
    cur = conn.execute(
        """INSERT INTO solicitacoes (colaborador_id, inicio, fim, dias, situacao, criado_em)
           VALUES (?, ?, ?, ?, 'SOLICITADA', ?)""",
        (colaborador_id, periodo.inicio.isoformat(), periodo.fim.isoformat(), dias, relogio.para_banco(agora)),
    )
    return cur.lastrowid


def atualizar_situacao(conn: sqlite3.Connection, solicitacao_id: int, situacao: str) -> None:
    conn.execute("UPDATE solicitacoes SET situacao = ? WHERE id = ?", (situacao, solicitacao_id))


def aprovadas_no_intervalo(conn: sqlite3.Connection, primeiro: date, ultimo: date) -> list[dict]:
    linhas = conn.execute(
        """SELECT s.id, s.colaborador_id, c.nome, c.equipe, s.inicio, s.fim
           FROM solicitacoes s JOIN colaboradores c ON c.id = s.colaborador_id
           WHERE s.situacao = 'APROVADA' AND s.inicio <= ? AND s.fim >= ?
           ORDER BY c.nome, s.id""",
        (ultimo.isoformat(), primeiro.isoformat()),
    ).fetchall()
    return [
        {**dict(l), "inicio": date.fromisoformat(l["inicio"]), "fim": date.fromisoformat(l["fim"])} for l in linhas
    ]
