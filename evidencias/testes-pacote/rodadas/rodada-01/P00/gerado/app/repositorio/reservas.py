"""SQL de reservas. Somente consultas parametrizadas; datas gravadas em UTC."""

import sqlite3
from datetime import datetime

from app.relogio import do_banco, para_banco

_SELECT = (
    "SELECT id, sala_id, responsavel_nome, responsavel_email, titulo, participantes, "
    "inicio, fim, status, criada_em, cancelada_em FROM reservas "
)
SQL_OBTER = _SELECT + "WHERE id = ?"
SQL_NO_INTERVALO = _SELECT + "WHERE inicio < ? AND fim > ? AND (? IS NULL OR sala_id = ?) ORDER BY inicio, id"


def _reserva(linha: sqlite3.Row) -> dict:
    r = dict(linha)
    for campo in ("inicio", "fim", "criada_em", "cancelada_em"):
        if r[campo] is not None:
            r[campo] = do_banco(r[campo])
    return r


def obter(conn: sqlite3.Connection, reserva_id: int) -> dict | None:
    linha = conn.execute(SQL_OBTER, (reserva_id,)).fetchone()
    return _reserva(linha) if linha else None


def da_sala_no_intervalo(conn: sqlite3.Connection, sala_id: int, inicio: datetime, fim: datetime) -> list[dict]:
    """Reservas (qualquer status) da sala que tocam o intervalo; o domínio decide o que bloqueia."""
    return no_intervalo(conn, inicio, fim, sala_id)


def no_intervalo(conn: sqlite3.Connection, inicio: datetime, fim: datetime, sala_id: int | None = None) -> list[dict]:
    """Reservas (qualquer status) que tocam o intervalo, por início."""
    parametros = (para_banco(fim), para_banco(inicio), sala_id, sala_id)
    return [_reserva(l) for l in conn.execute(SQL_NO_INTERVALO, parametros)]


def inserir(conn: sqlite3.Connection, dados: dict, agora: datetime) -> int:
    cursor = conn.execute(
        "INSERT INTO reservas (sala_id, responsavel_nome, responsavel_email, titulo, participantes, "
        "inicio, fim, status, criada_em) VALUES (?, ?, ?, ?, ?, ?, ?, 'ATIVA', ?)",
        (
            dados["sala_id"],
            dados["responsavel_nome"],
            dados["responsavel_email"],
            dados["titulo"],
            dados["participantes"],
            para_banco(dados["inicio"]),
            para_banco(dados["fim"]),
            para_banco(agora),
        ),
    )
    return cursor.lastrowid


def cancelar(conn: sqlite3.Connection, reserva_id: int, agora: datetime) -> None:
    conn.execute(
        "UPDATE reservas SET status = 'CANCELADA', cancelada_em = ? WHERE id = ?",
        (para_banco(agora), reserva_id),
    )
