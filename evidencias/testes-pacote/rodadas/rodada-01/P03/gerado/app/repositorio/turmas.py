"""SQL de turmas. Apenas consultas parametrizadas."""

import sqlite3
from datetime import datetime

from app.relogio import para_banco

# Ocupadas = CONFIRMADA + PRESENTE + AUSENTE (RN-05). Texto fixo, sem montagem dinâmica.
SQL_TURMA_COM_OCUPADAS = """
SELECT t.*,
       (SELECT COUNT(*) FROM inscricoes i
         WHERE i.turma_id = t.id AND i.situacao IN ('CONFIRMADA', 'PRESENTE', 'AUSENTE')) AS ocupadas
  FROM turmas t
"""
SQL_BUSCAR = SQL_TURMA_COM_OCUPADAS + " WHERE t.id = ?"
SQL_FUTURAS = SQL_TURMA_COM_OCUPADAS + " WHERE t.inicio > ? ORDER BY t.inicio, t.id"


def inserir(conn: sqlite3.Connection, titulo: str, inicio: datetime, duracao: int, modalidade: str, vagas: int) -> int:
    cursor = conn.execute(
        "INSERT INTO turmas (titulo, inicio, duracao_minutos, modalidade, vagas) VALUES (?, ?, ?, ?, ?)",
        (titulo, para_banco(inicio), duracao, modalidade, vagas),
    )
    return cursor.lastrowid


def buscar(conn: sqlite3.Connection, turma_id: int) -> sqlite3.Row | None:
    return conn.execute(SQL_BUSCAR, (turma_id,)).fetchone()


def listar_futuras(conn: sqlite3.Connection, agora: datetime) -> list[sqlite3.Row]:
    return conn.execute(SQL_FUTURAS, (para_banco(agora),)).fetchall()


def contar(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM turmas").fetchone()[0]
