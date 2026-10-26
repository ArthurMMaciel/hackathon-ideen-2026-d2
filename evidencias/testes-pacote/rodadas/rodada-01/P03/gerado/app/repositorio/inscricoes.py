"""SQL de inscrições. Apenas consultas parametrizadas."""

import sqlite3
from datetime import datetime

from app.relogio import para_banco


def inserir(conn: sqlite3.Connection, turma_id: int, nome: str, email: str, situacao: str, agora: datetime) -> int:
    cursor = conn.execute(
        "INSERT INTO inscricoes (turma_id, nome, email, situacao, criada_em) VALUES (?, ?, ?, ?, ?)",
        (turma_id, nome, email, situacao, para_banco(agora)),
    )
    return cursor.lastrowid


def buscar(conn: sqlite3.Connection, inscricao_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM inscricoes WHERE id = ?", (inscricao_id,)).fetchone()


def existe_ativa(conn: sqlite3.Connection, turma_id: int, email: str) -> bool:
    linha = conn.execute(
        "SELECT 1 FROM inscricoes WHERE turma_id = ? AND email = ? AND situacao IN ('CONFIRMADA', 'ESPERA')",
        (turma_id, email),
    ).fetchone()
    return linha is not None


def listar_da_turma(conn: sqlite3.Connection, turma_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM inscricoes WHERE turma_id = ? ORDER BY criada_em, id", (turma_id,)
    ).fetchall()


def ids_em_espera(conn: sqlite3.Connection, turma_id: int) -> list[int]:
    linhas = conn.execute(
        "SELECT id FROM inscricoes WHERE turma_id = ? AND situacao = 'ESPERA' ORDER BY criada_em, id",
        (turma_id,),
    ).fetchall()
    return [linha["id"] for linha in linhas]


def atualizar_situacao(conn: sqlite3.Connection, inscricao_id: int, situacao: str) -> None:
    conn.execute("UPDATE inscricoes SET situacao = ? WHERE id = ?", (situacao, inscricao_id))


def contar_presenca(conn: sqlite3.Connection, turma_id: int) -> tuple[int, int]:
    linha = conn.execute(
        "SELECT SUM(situacao = 'PRESENTE') AS presentes, SUM(situacao = 'AUSENTE') AS ausentes "
        "FROM inscricoes WHERE turma_id = ?",
        (turma_id,),
    ).fetchone()
    return (linha["presentes"] or 0, linha["ausentes"] or 0)
