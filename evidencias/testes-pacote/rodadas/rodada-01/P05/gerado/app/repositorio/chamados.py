"""Acesso ao banco dos chamados. Só SQL parametrizado; datas convertidas com o relógio."""

import sqlite3
from datetime import datetime

from app.relogio import do_banco, para_banco

# Consultas literais completas (sem montagem de texto em tempo de execução).
SQL_OBTER = (
    "SELECT id, titulo, descricao, solicitante_nome, solicitante_email, categoria, prioridade, "
    "situacao, aberto_em, prazo, responsavel, solucao, resolvido_em FROM chamados WHERE id = ?"
)
SQL_LISTAR = (
    "SELECT id, titulo, descricao, solicitante_nome, solicitante_email, categoria, prioridade, "
    "situacao, aberto_em, prazo, responsavel, solucao, resolvido_em FROM chamados ORDER BY id"
)
SQL_FILA = (
    "SELECT id, titulo, descricao, solicitante_nome, solicitante_email, categoria, prioridade, "
    "situacao, aberto_em, prazo, responsavel, solucao, resolvido_em FROM chamados "
    "WHERE situacao IN ('ABERTO', 'EM_ATENDIMENTO') ORDER BY prazo, aberto_em, id"
)


def _para_dict(linha: sqlite3.Row) -> dict:
    d = dict(linha)
    for campo in ("aberto_em", "prazo", "resolvido_em"):
        if d[campo] is not None:
            d[campo] = do_banco(d[campo])
    return d


def inserir(conn: sqlite3.Connection, dados: dict) -> int:
    cursor = conn.execute(
        "INSERT INTO chamados (titulo, descricao, solicitante_nome, solicitante_email, categoria, "
        "prioridade, situacao, aberto_em, prazo, responsavel, solucao, resolvido_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            dados["titulo"], dados["descricao"], dados["solicitante_nome"], dados["solicitante_email"],
            dados["categoria"], dados["prioridade"], dados["situacao"],
            para_banco(dados["aberto_em"]), para_banco(dados["prazo"]),
            dados.get("responsavel"), dados.get("solucao"),
            para_banco(dados["resolvido_em"]) if dados.get("resolvido_em") else None,
        ),
    )
    return cursor.lastrowid


def obter(conn: sqlite3.Connection, chamado_id: int) -> dict | None:
    linha = conn.execute(SQL_OBTER, (chamado_id,)).fetchone()
    return _para_dict(linha) if linha else None


def listar(conn: sqlite3.Connection) -> list[dict]:
    return [_para_dict(l) for l in conn.execute(SQL_LISTAR)]


def listar_fila(conn: sqlite3.Connection) -> list[dict]:
    linhas = conn.execute(SQL_FILA)
    return [_para_dict(l) for l in linhas]


def atualizar_situacao(
    conn: sqlite3.Connection,
    chamado_id: int,
    situacao: str,
    responsavel: str | None,
    solucao: str | None,
    resolvido_em: datetime | None,
) -> None:
    conn.execute(
        "UPDATE chamados SET situacao = ?, responsavel = ?, solucao = ?, resolvido_em = ? WHERE id = ?",
        (situacao, responsavel, solucao, para_banco(resolvido_em) if resolvido_em else None, chamado_id),
    )


def resolvidos_no_periodo(conn: sqlite3.Connection, inicio: datetime, fim: datetime) -> list[tuple[str, datetime, datetime]]:
    """(prioridade, resolvido_em, prazo) dos chamados RESOLVIDO ou FECHADO com resolução em [inicio, fim)."""
    linhas = conn.execute(
        "SELECT prioridade, resolvido_em, prazo FROM chamados "
        "WHERE situacao IN ('RESOLVIDO', 'FECHADO') AND resolvido_em >= ? AND resolvido_em < ?",
        (para_banco(inicio), para_banco(fim)),
    )
    return [(l["prioridade"], do_banco(l["resolvido_em"]), do_banco(l["prazo"])) for l in linhas]


def contar(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
