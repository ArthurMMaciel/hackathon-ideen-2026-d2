"""SQL parametrizado da tabela chamados. Datas entram e saem como datetime com fuso."""

import sqlite3
from datetime import datetime

from app.relogio import do_banco, para_banco

COLUNAS = (
    "id, titulo, descricao, solicitante_nome, solicitante_email, categoria, prioridade, situacao, "
    "aberto_em, prazo_em, responsavel, solucao, resolvido_em"
)

SQL_CONTAR = "SELECT COUNT(*) FROM chamados"
SQL_INSERIR = (
    "INSERT INTO chamados (titulo, descricao, solicitante_nome, solicitante_email, categoria, prioridade, "
    "situacao, aberto_em, prazo_em, responsavel, solucao, resolvido_em) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
SQL_BUSCAR = "SELECT " + COLUNAS + " FROM chamados WHERE id = ?"
SQL_LISTAR = "SELECT " + COLUNAS + " FROM chamados ORDER BY id DESC"
SQL_FILA = (
    "SELECT " + COLUNAS + " FROM chamados WHERE situacao IN ('ABERTO', 'EM_ATENDIMENTO') "
    "ORDER BY prazo_em, id"
)
SQL_RESOLVIDOS_NO_PERIODO = (
    "SELECT " + COLUNAS + " FROM chamados WHERE situacao IN ('RESOLVIDO', 'FECHADO') "
    "AND resolvido_em >= ? AND resolvido_em < ?"
)
# prazo_em e aberto_em não são atualizados (RN-02).
SQL_ATUALIZAR_SITUACAO = (
    "UPDATE chamados SET situacao = ?, responsavel = ?, solucao = ?, resolvido_em = ? WHERE id = ?"
)


def _de_linha(linha: sqlite3.Row) -> dict:
    chamado = dict(linha)
    for campo in ("aberto_em", "prazo_em", "resolvido_em"):
        if chamado[campo] is not None:
            chamado[campo] = do_banco(chamado[campo])
    return chamado


def _para_banco_ou_nulo(momento: datetime | None) -> str | None:
    return para_banco(momento) if momento is not None else None


def contar(conn: sqlite3.Connection) -> int:
    return conn.execute(SQL_CONTAR).fetchone()[0]


def inserir(conn: sqlite3.Connection, c: dict) -> int:
    cursor = conn.execute(
        SQL_INSERIR,
        (
            c["titulo"], c["descricao"], c["solicitante_nome"], c["solicitante_email"], c["categoria"],
            c["prioridade"], c["situacao"], para_banco(c["aberto_em"]), para_banco(c["prazo_em"]),
            c.get("responsavel"), c.get("solucao"), _para_banco_ou_nulo(c.get("resolvido_em")),
        ),
    )
    return cursor.lastrowid


def buscar(conn: sqlite3.Connection, id_: int) -> dict | None:
    linha = conn.execute(SQL_BUSCAR, (id_,)).fetchone()
    return _de_linha(linha) if linha else None


def listar(conn: sqlite3.Connection) -> list[dict]:
    return [_de_linha(linha) for linha in conn.execute(SQL_LISTAR).fetchall()]


def fila(conn: sqlite3.Connection) -> list[dict]:
    return [_de_linha(linha) for linha in conn.execute(SQL_FILA).fetchall()]


def resolvidos_no_periodo(conn: sqlite3.Connection, inicio: datetime, fim: datetime) -> list[dict]:
    linhas = conn.execute(SQL_RESOLVIDOS_NO_PERIODO, (para_banco(inicio), para_banco(fim))).fetchall()
    return [_de_linha(linha) for linha in linhas]


def atualizar_situacao(conn: sqlite3.Connection, c: dict) -> None:
    conn.execute(
        SQL_ATUALIZAR_SITUACAO,
        (c["situacao"], c.get("responsavel"), c.get("solucao"), _para_banco_ou_nulo(c.get("resolvido_em")), c["id"]),
    )
