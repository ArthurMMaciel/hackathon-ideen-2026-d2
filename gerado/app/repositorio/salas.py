"""SQL das salas. Só parâmetros `?`."""

import json
import sqlite3

LISTAR = "SELECT id, nome, local, capacidade, recursos FROM salas ORDER BY local, nome COLLATE NOCASE, id"
OBTER = "SELECT id, nome, local, capacidade, recursos FROM salas WHERE id = ?"
NOMES_DO_LOCAL = "SELECT nome, local FROM salas WHERE local = ?"
INSERIR = "INSERT INTO salas (nome, local, capacidade, recursos) VALUES (?, ?, ?, ?)"


def _para_dict(linha: sqlite3.Row) -> dict:
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "local": linha["local"],
        "capacidade": linha["capacidade"],
        "recursos": json.loads(linha["recursos"]),
    }


def listar(conn: sqlite3.Connection) -> list[dict]:
    return [_para_dict(linha) for linha in conn.execute(LISTAR)]


def obter(conn: sqlite3.Connection, sala_id: int) -> dict | None:
    linha = conn.execute(OBTER, (sala_id,)).fetchone()
    return _para_dict(linha) if linha else None


def nomes_do_local(conn: sqlite3.Connection, local: str) -> list[tuple[str, str]]:
    return [(linha["nome"], linha["local"]) for linha in conn.execute(NOMES_DO_LOCAL, (local,))]


def inserir(conn: sqlite3.Connection, nome: str, local: str, capacidade: int, recursos: list[str]) -> int:
    return conn.execute(INSERIR, (nome, local, capacidade, json.dumps(recursos))).lastrowid
