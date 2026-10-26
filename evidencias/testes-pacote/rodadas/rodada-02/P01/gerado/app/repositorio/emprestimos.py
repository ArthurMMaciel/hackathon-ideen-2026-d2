"""SQL de empréstimos. Só parâmetros `?`. Datas de calendário gravadas como texto AAAA-MM-DD."""

import sqlite3
from datetime import date

_SELECT = """SELECT e.id, e.equipamento_id, q.patrimonio, q.tipo, e.nome, e.email, e.data_retirada,
       e.data_prevista, e.data_devolucao, e.defeito, e.status
  FROM emprestimos e JOIN equipamentos q ON q.id = e.equipamento_id"""

SQL_INSERIR = """INSERT INTO emprestimos (equipamento_id, nome, email, data_retirada, data_prevista, status)
VALUES (?, ?, ?, ?, ?, 'ABERTO')"""
SQL_POR_ID = _SELECT + " WHERE e.id = ?"
SQL_LISTAR = _SELECT + " ORDER BY e.id"
SQL_LISTAR_STATUS = _SELECT + " WHERE e.status = ? ORDER BY e.id"
SQL_ATRASADOS = _SELECT + " WHERE e.status = 'ABERTO' AND e.data_prevista < ? ORDER BY e.data_prevista, e.id"
SQL_ABERTOS_DA_PESSOA = "SELECT COUNT(*) FROM emprestimos WHERE email = ? AND status = 'ABERTO'"
SQL_DEVOLVER = "UPDATE emprestimos SET status = 'DEVOLVIDO', data_devolucao = ?, defeito = ? WHERE id = ?"
SQL_CONTAR_POR_TIPO = """SELECT q.tipo, COUNT(*) AS quantidade
  FROM emprestimos e JOIN equipamentos q ON q.id = e.equipamento_id
 WHERE e.data_retirada BETWEEN ? AND ?
 GROUP BY q.tipo"""


def _converter(linha: sqlite3.Row) -> dict:
    d = dict(linha)
    d["defeito"] = None if d["defeito"] is None else bool(d["defeito"])
    return d


def inserir(conn, equipamento_id: int, nome: str, email: str, retirada: date, prevista: date) -> int:
    return conn.execute(
        SQL_INSERIR, (equipamento_id, nome, email, retirada.isoformat(), prevista.isoformat())
    ).lastrowid


def obter(conn, emprestimo_id: int) -> dict | None:
    linha = conn.execute(SQL_POR_ID, (emprestimo_id,)).fetchone()
    return _converter(linha) if linha else None


def listar(conn, status: str | None) -> list[dict]:
    if status is None:
        return [_converter(l) for l in conn.execute(SQL_LISTAR)]
    return [_converter(l) for l in conn.execute(SQL_LISTAR_STATUS, (status,))]


def listar_atrasados(conn, hoje: date) -> list[dict]:
    return [_converter(l) for l in conn.execute(SQL_ATRASADOS, (hoje.isoformat(),))]


def contar_abertos_da_pessoa(conn, email: str) -> int:
    return conn.execute(SQL_ABERTOS_DA_PESSOA, (email,)).fetchone()[0]


def registrar_devolucao(conn, emprestimo_id: int, devolucao: date, defeito: bool) -> None:
    conn.execute(SQL_DEVOLVER, (devolucao.isoformat(), int(defeito), emprestimo_id))


def contar_por_tipo(conn, inicio: date, fim: date) -> dict[str, int]:
    return {l["tipo"]: l["quantidade"] for l in conn.execute(SQL_CONTAR_POR_TIPO, (inicio.isoformat(), fim.isoformat()))}
