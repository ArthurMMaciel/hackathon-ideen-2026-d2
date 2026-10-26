"""Relatório mensal de empréstimos por tipo de equipamento."""

import sqlite3

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.banco import obter_conexao
from app.dominio import emprestimos as dominio
from app.dominio.equipamentos import TIPOS
from app.repositorio import emprestimos as repo

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


class ItemRelatorio(BaseModel):
    tipo: str
    quantidade: int


class Relatorio(BaseModel):
    mes: str
    itens: list[ItemRelatorio]
    total: int


@router.get("/emprestimos-por-tipo", response_model=Relatorio)
def emprestimos_por_tipo(
    mes: str = Query(pattern=r"^[0-9]{4}-[0-9]{2}$", description="Mês no formato AAAA-MM"),
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    inicio, fim = dominio.intervalo_do_mes(mes)  # RN-12
    contagem = repo.contar_por_tipo(conn, inicio, fim)
    itens = [{"tipo": tipo, "quantidade": contagem.get(tipo, 0)} for tipo in TIPOS]  # PR-07
    return {"mes": mes, "itens": itens, "total": sum(i["quantidade"] for i in itens)}
