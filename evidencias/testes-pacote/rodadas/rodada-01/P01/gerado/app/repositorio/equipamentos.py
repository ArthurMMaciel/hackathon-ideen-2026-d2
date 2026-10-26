"""SQL de equipamentos. Só consultas parametrizadas."""

import sqlite3

# Consultas como constantes: nenhum SQL é montado na hora da chamada.
_SELECT = "SELECT id, patrimonio, tipo, descricao, situacao FROM equipamentos"
_POR_ID = _SELECT + " WHERE id = ?"
# Filtros opcionais com parâmetros: "? IS NULL" desliga o filtro quando o valor não vem.
_LISTAR = _SELECT + " WHERE (? IS NULL OR tipo = ?) AND (? IS NULL OR situacao = ?) ORDER BY patrimonio"


def _dict(linha: sqlite3.Row | None) -> dict | None:
    return dict(linha) if linha else None


def buscar(conn: sqlite3.Connection, equipamento_id: int) -> dict | None:
    return _dict(conn.execute(_POR_ID, (equipamento_id,)).fetchone())


def existe_patrimonio(conn: sqlite3.Connection, patrimonio: str) -> bool:
    return conn.execute("SELECT 1 FROM equipamentos WHERE patrimonio = ?", (patrimonio,)).fetchone() is not None


def listar(conn: sqlite3.Connection, tipo: str | None = None, situacao: str | None = None) -> list[dict]:
    linhas = conn.execute(_LISTAR, (tipo, tipo, situacao, situacao)).fetchall()
    return [dict(linha) for linha in linhas]


def inserir(conn: sqlite3.Connection, patrimonio: str, tipo: str, descricao: str) -> int:
    cursor = conn.execute(
        "INSERT INTO equipamentos (patrimonio, tipo, descricao, situacao) VALUES (?, ?, ?, 'DISPONIVEL')",
        (patrimonio, tipo, descricao),
    )
    return cursor.lastrowid


def atualizar_situacao(conn: sqlite3.Connection, equipamento_id: int, situacao: str) -> None:
    conn.execute("UPDATE equipamentos SET situacao = ? WHERE id = ?", (situacao, equipamento_id))
