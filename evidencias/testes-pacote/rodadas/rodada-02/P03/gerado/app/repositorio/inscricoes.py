"""SQL de inscrições. Só parâmetros `?`; datas gravadas em UTC."""

import sqlite3
from datetime import datetime

from app.relogio import do_banco, para_banco

_COLUNAS = "id, turma_id, nome, email, situacao, criada_em"

SQL_INSERIR = """INSERT INTO inscricoes (turma_id, nome, email, situacao, criada_em, atualizada_em)
VALUES (?, ?, ?, ?, ?, ?)"""
SQL_BUSCAR = "SELECT " + _COLUNAS + " FROM inscricoes WHERE id = ?"
SQL_LISTAR_DA_TURMA = "SELECT " + _COLUNAS + " FROM inscricoes WHERE turma_id = ? ORDER BY id"
SQL_EXISTE_ATIVA = """SELECT 1 FROM inscricoes
WHERE turma_id = ? AND email = ? AND situacao IN ('CONFIRMADA', 'ESPERA') LIMIT 1"""
SQL_ATUALIZAR_SITUACAO = "UPDATE inscricoes SET situacao = ?, atualizada_em = ? WHERE id = ?"


def _para_dict(linha: sqlite3.Row) -> dict:
    inscricao = dict(linha)
    inscricao["criada_em"] = do_banco(inscricao["criada_em"])
    return inscricao


def inserir(conn: sqlite3.Connection, turma_id: int, nome: str, email: str, situacao: str,
            agora: datetime) -> int:
    momento = para_banco(agora)
    cursor = conn.execute(SQL_INSERIR, (turma_id, nome, email, situacao, momento, momento))
    return cursor.lastrowid


def buscar(conn: sqlite3.Connection, inscricao_id: int) -> dict | None:
    linha = conn.execute(SQL_BUSCAR, (inscricao_id,)).fetchone()
    return _para_dict(linha) if linha else None


def listar_da_turma(conn: sqlite3.Connection, turma_id: int) -> list[dict]:
    return [_para_dict(linha) for linha in conn.execute(SQL_LISTAR_DA_TURMA, (turma_id,))]


def existe_ativa(conn: sqlite3.Connection, turma_id: int, email: str) -> bool:
    return conn.execute(SQL_EXISTE_ATIVA, (turma_id, email)).fetchone() is not None


def atualizar_situacao(conn: sqlite3.Connection, inscricao_id: int, situacao: str, agora: datetime) -> None:
    conn.execute(SQL_ATUALIZAR_SITUACAO, (situacao, para_banco(agora), inscricao_id))
