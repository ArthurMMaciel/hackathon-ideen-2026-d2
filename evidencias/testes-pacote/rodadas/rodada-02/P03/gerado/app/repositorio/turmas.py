"""SQL de turmas. Só parâmetros `?`; datas gravadas em UTC."""

import sqlite3
from datetime import datetime

from app.relogio import do_banco, para_banco

_COLUNAS = """t.id, t.titulo, t.inicio, t.duracao_minutos, t.modalidade, t.vagas,
  (SELECT COUNT(*) FROM inscricoes i
    WHERE i.turma_id = t.id AND i.situacao IN ('CONFIRMADA', 'PRESENTE', 'AUSENTE')) AS ocupadas"""

SQL_INSERIR = "INSERT INTO turmas (titulo, inicio, duracao_minutos, modalidade, vagas) VALUES (?, ?, ?, ?, ?)"
SQL_BUSCAR = "SELECT " + _COLUNAS + " FROM turmas t WHERE t.id = ?"
SQL_FUTURAS = "SELECT " + _COLUNAS + " FROM turmas t WHERE t.inicio > ? ORDER BY t.inicio, t.id"
SQL_PRESENCA = """SELECT
  COALESCE(SUM(CASE WHEN situacao = 'PRESENTE' THEN 1 ELSE 0 END), 0) AS presentes,
  COALESCE(SUM(CASE WHEN situacao = 'AUSENTE' THEN 1 ELSE 0 END), 0) AS ausentes
FROM inscricoes WHERE turma_id = ?"""


def _para_dict(linha: sqlite3.Row) -> dict:
    turma = dict(linha)
    turma["inicio"] = do_banco(turma["inicio"])
    return turma


def inserir(conn: sqlite3.Connection, titulo: str, inicio: datetime, duracao_minutos: int,
            modalidade: str, vagas: int) -> int:
    cursor = conn.execute(SQL_INSERIR, (titulo, para_banco(inicio), duracao_minutos, modalidade, vagas))
    return cursor.lastrowid


def buscar(conn: sqlite3.Connection, turma_id: int) -> dict | None:
    linha = conn.execute(SQL_BUSCAR, (turma_id,)).fetchone()
    return _para_dict(linha) if linha else None


def listar_futuras(conn: sqlite3.Connection, agora: datetime) -> list[dict]:
    return [_para_dict(linha) for linha in conn.execute(SQL_FUTURAS, (para_banco(agora),))]


def contar_presenca(conn: sqlite3.Connection, turma_id: int) -> tuple[int, int]:
    linha = conn.execute(SQL_PRESENCA, (turma_id,)).fetchone()
    return linha["presentes"], linha["ausentes"]
