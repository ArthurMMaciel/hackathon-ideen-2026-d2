"""Relatório mensal de empréstimos por tipo."""

import re
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import AfterValidator, BaseModel

from app.banco import obter_conexao
from app.dominio import relatorio as regras
from app.repositorio import emprestimos as repo
from app.tipos import ANO_MAXIMO, ANO_MINIMO

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])

_FORMATO_MES = re.compile(r"^([0-9]{4})-(0[1-9]|1[0-2])$")


def _mes_valido(valor: str) -> str:
    achado = _FORMATO_MES.match(valor)
    if not achado:
        raise ValueError("o mês precisa estar no formato AAAA-MM")
    if not ANO_MINIMO <= int(achado.group(1)) <= ANO_MAXIMO:
        raise ValueError(f"o ano precisa estar entre {ANO_MINIMO} e {ANO_MAXIMO}")
    return valor


Mes = Annotated[str, AfterValidator(_mes_valido)]
Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]


class ItemRelatorio(BaseModel):
    tipo: str
    quantidade: int


class RelatorioSaida(BaseModel):
    mes: str
    itens: list[ItemRelatorio]


@router.get("/emprestimos-por-tipo", response_model=RelatorioSaida)
def emprestimos_por_tipo(mes: Annotated[Mes, Query()], conn: Conexao):
    ano, numero = int(mes[:4]), int(mes[5:])
    inicio, fim = regras.periodo_do_mes(ano, numero)  # RN-10
    return regras.montar_relatorio(ano, numero, repo.contar_por_tipo(conn, inicio, fim))
