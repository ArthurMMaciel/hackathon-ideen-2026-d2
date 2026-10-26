"""SQL das reservas. Datas gravadas em UTC (relogio.para_banco). Só parâmetros `?`."""

import sqlite3
from datetime import datetime

from app.relogio import do_banco, para_banco

_COLUNAS = """r.id, r.sala_id, s.nome AS sala_nome, r.responsavel_nome, r.responsavel_email, r.titulo,
              r.participantes, r.inicio, r.fim, r.status"""

INSERIR = """INSERT INTO reservas (sala_id, responsavel_nome, responsavel_email, titulo, participantes,
                                   inicio, fim, status, criada_em)
             VALUES (?, ?, ?, ?, ?, ?, ?, 'ATIVA', ?)"""
OBTER = f"SELECT {_COLUNAS} FROM reservas r JOIN salas s ON s.id = r.sala_id WHERE r.id = ?"
# RN-01 e RN-06: só ATIVAS contam para conflito.
ATIVAS_SOBREPOSTAS_DA_SALA = """SELECT inicio, fim FROM reservas
                                WHERE sala_id = ? AND status = 'ATIVA' AND inicio < ? AND fim > ?"""
# RN-07 e RN-06: salas com reserva ATIVA sobreposta ao intervalo.
SALAS_OCUPADAS = "SELECT DISTINCT sala_id FROM reservas WHERE status = 'ATIVA' AND inicio < ? AND fim > ?"
NO_INTERVALO = f"""SELECT {_COLUNAS} FROM reservas r JOIN salas s ON s.id = r.sala_id
                   WHERE r.inicio < ? AND r.fim > ? ORDER BY r.inicio, s.local, s.nome, r.id"""
NO_INTERVALO_DA_SALA = f"""SELECT {_COLUNAS} FROM reservas r JOIN salas s ON s.id = r.sala_id
                           WHERE r.inicio < ? AND r.fim > ? AND r.sala_id = ? ORDER BY r.inicio, r.id"""
# RN-08 e RN-06: só ATIVAS entram na ocupação.
ATIVAS_NO_INTERVALO = f"""SELECT {_COLUNAS} FROM reservas r JOIN salas s ON s.id = r.sala_id
                          WHERE r.status = 'ATIVA' AND r.inicio < ? AND r.fim > ?"""
CANCELAR = "UPDATE reservas SET status = 'CANCELADA', cancelada_em = ? WHERE id = ? AND status = 'ATIVA'"


def _para_dict(linha: sqlite3.Row) -> dict:
    dados = dict(linha)
    dados["inicio"] = do_banco(dados["inicio"])
    dados["fim"] = do_banco(dados["fim"])
    return dados


def inserir(conn: sqlite3.Connection, dados: dict, agora: datetime) -> int:
    return conn.execute(
        INSERIR,
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
    ).lastrowid


def obter(conn: sqlite3.Connection, reserva_id: int) -> dict | None:
    linha = conn.execute(OBTER, (reserva_id,)).fetchone()
    return _para_dict(linha) if linha else None


def ativas_sobrepostas(conn: sqlite3.Connection, sala_id: int, inicio: datetime, fim: datetime):
    linhas = conn.execute(ATIVAS_SOBREPOSTAS_DA_SALA, (sala_id, para_banco(fim), para_banco(inicio)))
    return [(do_banco(l["inicio"]), do_banco(l["fim"])) for l in linhas]


def salas_ocupadas(conn: sqlite3.Connection, inicio: datetime, fim: datetime) -> set[int]:
    return {l["sala_id"] for l in conn.execute(SALAS_OCUPADAS, (para_banco(fim), para_banco(inicio)))}


def no_intervalo(conn: sqlite3.Connection, inicio: datetime, fim: datetime, sala_id: int | None = None):
    if sala_id is None:
        linhas = conn.execute(NO_INTERVALO, (para_banco(fim), para_banco(inicio)))
    else:
        linhas = conn.execute(NO_INTERVALO_DA_SALA, (para_banco(fim), para_banco(inicio), sala_id))
    return [_para_dict(l) for l in linhas]


def ativas_no_intervalo(conn: sqlite3.Connection, inicio: datetime, fim: datetime) -> list[dict]:
    return [_para_dict(l) for l in conn.execute(ATIVAS_NO_INTERVALO, (para_banco(fim), para_banco(inicio)))]


def cancelar(conn: sqlite3.Connection, reserva_id: int, agora: datetime) -> None:
    conn.execute(CANCELAR, (para_banco(agora), reserva_id))
