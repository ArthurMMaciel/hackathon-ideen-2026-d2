"""SQL de empréstimos. Só consultas parametrizadas.

Datas de empréstimo são datas civis (YYYY-MM-DD), gravadas como texto; o carimbo criado_em vai em UTC.
"""

import sqlite3
from datetime import date, datetime

from app.relogio import para_banco

_SELECT = (
    "SELECT e.id, e.equipamento_id, q.patrimonio, q.tipo, e.nome, e.email, e.data_retirada, e.data_prevista,"
    " e.data_devolucao, e.defeito, e.status, q.situacao AS situacao_equipamento"
    " FROM emprestimos e JOIN equipamentos q ON q.id = e.equipamento_id"
)
# Consultas como constantes: nenhum SQL é montado na hora da chamada.
_POR_ID = _SELECT + " WHERE e.id = ?"
_LISTAR = _SELECT + " WHERE (? IS NULL OR e.status = ?) ORDER BY e.data_retirada, e.id"
# Comparação de texto YYYY-MM-DD equivale à comparação de datas.
_VENCIDOS = _SELECT + " WHERE e.status = 'ABERTO' AND e.data_prevista < ? ORDER BY e.data_prevista, e.id"


def _dict(linha: sqlite3.Row) -> dict:
    d = dict(linha)
    d["defeito"] = None if d["defeito"] is None else bool(d["defeito"])
    return d


def buscar(conn: sqlite3.Connection, emprestimo_id: int) -> dict | None:
    linha = conn.execute(_POR_ID, (emprestimo_id,)).fetchone()
    return _dict(linha) if linha else None


def contar_abertos_por_email(conn: sqlite3.Connection, email: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM emprestimos WHERE email = ? AND status = 'ABERTO'", (email,)
    ).fetchone()[0]


def inserir(
    conn: sqlite3.Connection,
    equipamento_id: int,
    nome: str,
    email: str,
    retirada: date,
    prevista: date,
    agora: datetime,
) -> int:
    cursor = conn.execute(
        "INSERT INTO emprestimos (equipamento_id, nome, email, data_retirada, data_prevista, status, criado_em)"
        " VALUES (?, ?, ?, ?, ?, 'ABERTO', ?)",
        (equipamento_id, nome, email, retirada.isoformat(), prevista.isoformat(), para_banco(agora)),
    )
    return cursor.lastrowid


def registrar_devolucao(conn: sqlite3.Connection, emprestimo_id: int, dia: date, defeito: bool) -> None:
    conn.execute(
        "UPDATE emprestimos SET status = 'DEVOLVIDO', data_devolucao = ?, defeito = ? WHERE id = ? AND status = 'ABERTO'",
        (dia.isoformat(), int(defeito), emprestimo_id),
    )


def listar(conn: sqlite3.Connection, status: str | None = None) -> list[dict]:
    linhas = conn.execute(_LISTAR, (status, status)).fetchall()
    return [_dict(linha) for linha in linhas]


def listar_abertos_vencidos(conn: sqlite3.Connection, dia: date) -> list[dict]:
    linhas = conn.execute(_VENCIDOS, (dia.isoformat(),)).fetchall()
    return [_dict(linha) for linha in linhas]


def contar_por_tipo(conn: sqlite3.Connection, inicio: date, fim: date) -> dict[str, int]:
    linhas = conn.execute(
        "SELECT q.tipo, COUNT(*) AS quantidade FROM emprestimos e JOIN equipamentos q ON q.id = e.equipamento_id"
        " WHERE e.data_retirada >= ? AND e.data_retirada < ? GROUP BY q.tipo",
        (inicio.isoformat(), fim.isoformat()),
    ).fetchall()
    return {linha["tipo"]: linha["quantidade"] for linha in linhas}
