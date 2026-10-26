"""SQL parametrizado da tabela despesas."""

import sqlite3
from datetime import date, datetime

from app import relogio

COLUNAS = (
    "id, colaborador_nome, colaborador_email, data_despesa, categoria, valor_centavos, "
    "descricao, numero_comprovante, situacao, motivo_recusa, criada_em, atualizada_em"
)
# Consultas fixas, montadas uma vez com texto constante (sem dado do usuário).
SQL_OBTER = "SELECT " + COLUNAS + " FROM despesas WHERE id = ?"
SQL_LISTAR = (
    "SELECT " + COLUNAS + " FROM despesas "
    "WHERE (? IS NULL OR colaborador_email = ?) AND (? IS NULL OR situacao = ?) "
    "ORDER BY data_despesa DESC, id DESC"
)


def _para_dict(linha: sqlite3.Row) -> dict:
    return {
        "id": linha["id"],
        "colaborador_nome": linha["colaborador_nome"],
        "colaborador_email": linha["colaborador_email"],
        "data_despesa": date.fromisoformat(linha["data_despesa"]),
        "categoria": linha["categoria"],
        "valor_centavos": linha["valor_centavos"],
        "descricao": linha["descricao"],
        "numero_comprovante": linha["numero_comprovante"],
        "situacao": linha["situacao"],
        "motivo_recusa": linha["motivo_recusa"],
        "criada_em": relogio.do_banco(linha["criada_em"]),
        "atualizada_em": relogio.do_banco(linha["atualizada_em"]),
    }


def existe_comprovante(conn: sqlite3.Connection, email: str, numero_comprovante: str) -> bool:
    linha = conn.execute(
        "SELECT 1 FROM despesas WHERE colaborador_email = ? AND numero_comprovante = ?",
        (email, numero_comprovante),
    ).fetchone()
    return linha is not None


def inserir(conn: sqlite3.Connection, dados: dict, agora: datetime) -> int:
    momento = relogio.para_banco(agora)
    cursor = conn.execute(
        "INSERT INTO despesas (colaborador_nome, colaborador_email, data_despesa, categoria, "
        "valor_centavos, descricao, numero_comprovante, situacao, motivo_recusa, criada_em, atualizada_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            dados["colaborador_nome"],
            dados["colaborador_email"],
            dados["data_despesa"].isoformat(),
            dados["categoria"],
            dados["valor_centavos"],
            dados["descricao"],
            dados["numero_comprovante"],
            dados["situacao"],
            dados.get("motivo_recusa"),
            momento,
            momento,
        ),
    )
    return cursor.lastrowid


def obter(conn: sqlite3.Connection, despesa_id: int) -> dict | None:
    linha = conn.execute(SQL_OBTER, (despesa_id,)).fetchone()
    return _para_dict(linha) if linha else None


def listar(conn: sqlite3.Connection, email: str | None, situacao: str | None) -> list[dict]:
    # Filtros opcionais com parâmetros: "? IS NULL" desliga o filtro sem montar SQL dinâmico.
    linhas = conn.execute(
        SQL_LISTAR,
        (email, email, situacao, situacao),
    ).fetchall()
    return [_para_dict(linha) for linha in linhas]


def mudar_situacao(
    conn: sqlite3.Connection, despesa_id: int, situacao: str, motivo: str | None, agora: datetime
) -> None:
    conn.execute(
        "UPDATE despesas SET situacao = ?, motivo_recusa = COALESCE(?, motivo_recusa), atualizada_em = ? "
        "WHERE id = ?",
        (situacao, motivo, relogio.para_banco(agora), despesa_id),
    )


def excluir(conn: sqlite3.Connection, despesa_id: int) -> None:
    conn.execute("DELETE FROM despesas WHERE id = ?", (despesa_id,))


def do_periodo(conn: sqlite3.Connection, inicio: date, fim: date) -> list[tuple[str, str, int]]:
    """Despesas com data em [inicio, fim)."""
    linhas = conn.execute(
        "SELECT categoria, situacao, valor_centavos FROM despesas "
        "WHERE data_despesa >= ? AND data_despesa < ?",
        (inicio.isoformat(), fim.isoformat()),
    ).fetchall()
    return [(l["categoria"], l["situacao"], l["valor_centavos"]) for l in linhas]
