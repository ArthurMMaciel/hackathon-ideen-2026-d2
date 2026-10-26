"""SQL de salas. Somente consultas parametrizadas."""

import json
import sqlite3

# PR-06: por local (na ordem do pedido) e nome.
SQL_LISTAR = (
    "SELECT id, nome, local, capacidade, recursos FROM salas "
    "ORDER BY CASE local WHEN 'SAO_PAULO' THEN 1 WHEN 'ARARAQUARA' THEN 2 ELSE 3 END, nome COLLATE NOCASE, id"
)
SQL_OBTER = "SELECT id, nome, local, capacidade, recursos FROM salas WHERE id = ?"


def _sala(linha: sqlite3.Row) -> dict:
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "local": linha["local"],
        "capacidade": linha["capacidade"],
        "recursos": json.loads(linha["recursos"]),
    }


def listar(conn: sqlite3.Connection) -> list[dict]:
    return [_sala(l) for l in conn.execute(SQL_LISTAR)]


def obter(conn: sqlite3.Connection, sala_id: int) -> dict | None:
    linha = conn.execute(SQL_OBTER, (sala_id,)).fetchone()
    return _sala(linha) if linha else None


def nome_existe(conn: sqlite3.Connection, nome: str) -> bool:
    return conn.execute("SELECT 1 FROM salas WHERE nome = ? COLLATE NOCASE", (nome,)).fetchone() is not None


def inserir(conn: sqlite3.Connection, nome: str, local: str, capacidade: int, recursos: list[str]) -> int:
    cursor = conn.execute(
        "INSERT INTO salas (nome, local, capacidade, recursos) VALUES (?, ?, ?, ?)",
        (nome, local, capacidade, json.dumps(recursos)),
    )
    return cursor.lastrowid
