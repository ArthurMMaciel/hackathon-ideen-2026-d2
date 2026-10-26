"""SQL de equipamentos. Só parâmetros `?`."""

import sqlite3

_COLUNAS = "id, patrimonio, tipo, descricao, situacao"

SQL_INSERIR = "INSERT INTO equipamentos (patrimonio, tipo, descricao, situacao) VALUES (?, ?, ?, 'DISPONIVEL')"
SQL_POR_ID = f"SELECT {_COLUNAS} FROM equipamentos WHERE id = ?"
SQL_EXISTE_PATRIMONIO = "SELECT 1 FROM equipamentos WHERE patrimonio = ?"
SQL_LISTAR = f"SELECT {_COLUNAS} FROM equipamentos ORDER BY patrimonio"
SQL_DISPONIVEIS = f"SELECT {_COLUNAS} FROM equipamentos WHERE situacao = 'DISPONIVEL' ORDER BY patrimonio"
SQL_DISPONIVEIS_TIPO = (
    f"SELECT {_COLUNAS} FROM equipamentos WHERE situacao = 'DISPONIVEL' AND tipo = ? ORDER BY patrimonio"
)
SQL_MUDAR_SITUACAO = "UPDATE equipamentos SET situacao = ? WHERE id = ?"


def inserir(conn: sqlite3.Connection, patrimonio: str, tipo: str, descricao: str) -> int:
    return conn.execute(SQL_INSERIR, (patrimonio, tipo, descricao)).lastrowid


def obter(conn: sqlite3.Connection, equipamento_id: int) -> dict | None:
    linha = conn.execute(SQL_POR_ID, (equipamento_id,)).fetchone()
    return dict(linha) if linha else None


def existe_patrimonio(conn: sqlite3.Connection, patrimonio: str) -> bool:
    return conn.execute(SQL_EXISTE_PATRIMONIO, (patrimonio,)).fetchone() is not None


def listar(conn: sqlite3.Connection) -> list[dict]:
    return [dict(l) for l in conn.execute(SQL_LISTAR)]


def listar_disponiveis(conn: sqlite3.Connection, tipo: str | None) -> list[dict]:
    if tipo is None:
        return [dict(l) for l in conn.execute(SQL_DISPONIVEIS)]
    return [dict(l) for l in conn.execute(SQL_DISPONIVEIS_TIPO, (tipo,))]


def mudar_situacao(conn: sqlite3.Connection, equipamento_id: int, situacao: str) -> None:
    conn.execute(SQL_MUDAR_SITUACAO, (situacao, equipamento_id))
