"""SQL parametrizado das despesas. Datas de calendário como texto AAAA-MM-DD."""

import sqlite3

_COLUNAS = (
    "id, colaborador_nome, colaborador_email, data, categoria, valor_centavos, descricao, "
    "comprovante, situacao, motivo_recusa"
)

_INSERIR = (
    "INSERT INTO despesas (colaborador_nome, colaborador_email, data, categoria, valor_centavos, "
    "descricao, comprovante, situacao, motivo_recusa) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_CONTAR = "SELECT COUNT(*) FROM despesas"
_BUSCAR = f"SELECT {_COLUNAS} FROM despesas WHERE id = ?"
_EXISTE_COMPROVANTE = "SELECT 1 FROM despesas WHERE colaborador_email = ? AND comprovante = ?"
_LISTAR = (
    f"SELECT {_COLUNAS} FROM despesas "
    "WHERE (? IS NULL OR colaborador_email = ?) AND (? IS NULL OR situacao = ?) "
    "ORDER BY data DESC, id DESC"
)
_MUDAR_SITUACAO = "UPDATE despesas SET situacao = ?, motivo_recusa = ? WHERE id = ?"
_EXCLUIR = "DELETE FROM despesas WHERE id = ?"
_SOMAR_MES = (
    "SELECT categoria, SUM(valor_centavos) AS total FROM despesas "
    "WHERE data >= ? AND data <= ? AND situacao IN (?, ?) GROUP BY categoria"
)


def _para_dict(linha: sqlite3.Row | None) -> dict | None:
    return dict(linha) if linha is not None else None


def inserir(conn: sqlite3.Connection, dados: dict) -> int:
    cursor = conn.execute(
        _INSERIR,
        (
            dados["colaborador_nome"],
            dados["colaborador_email"],
            dados["data"],
            dados["categoria"],
            dados["valor_centavos"],
            dados["descricao"],
            dados["comprovante"],
            dados["situacao"],
            dados.get("motivo_recusa"),
        ),
    )
    return cursor.lastrowid


def contar(conn: sqlite3.Connection) -> int:
    return conn.execute(_CONTAR).fetchone()[0]


def buscar(conn: sqlite3.Connection, id_: int) -> dict | None:
    return _para_dict(conn.execute(_BUSCAR, (id_,)).fetchone())


def existe_comprovante(conn: sqlite3.Connection, email: str, comprovante: str) -> bool:
    return conn.execute(_EXISTE_COMPROVANTE, (email, comprovante)).fetchone() is not None


def listar(conn: sqlite3.Connection, email: str | None, situacao: str | None) -> list[dict]:
    return [dict(l) for l in conn.execute(_LISTAR, (email, email, situacao, situacao)).fetchall()]


def mudar_situacao(conn: sqlite3.Connection, id_: int, situacao: str, motivo: str | None) -> None:
    conn.execute(_MUDAR_SITUACAO, (situacao, motivo, id_))


def excluir(conn: sqlite3.Connection, id_: int) -> None:
    conn.execute(_EXCLUIR, (id_,))


def somar_mes(conn: sqlite3.Connection, inicio: str, fim: str, situacoes: tuple[str, str]) -> dict[str, int]:
    linhas = conn.execute(_SOMAR_MES, (inicio, fim, *situacoes)).fetchall()
    return {linha["categoria"]: linha["total"] for linha in linhas}
