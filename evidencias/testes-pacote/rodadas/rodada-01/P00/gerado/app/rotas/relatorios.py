"""Relatório de ocupação por sala num dia."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.banco import obter_conexao
from app.dominio import ocupacao
from app.repositorio import reservas as repo_reservas
from app.repositorio import salas as repo_salas
from app.rotas.modelos import Data, RelatorioOcupacao

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


@router.get("/ocupacao", response_model=RelatorioOcupacao)
def relatorio_ocupacao(data: Annotated[Data, Query()], conn: sqlite3.Connection = Depends(obter_conexao)):
    abre, fecha = ocupacao.janela(data)
    reservas = repo_reservas.no_intervalo(conn, abre, fecha)
    return {
        "data": data,
        "janela_inicio": abre.strftime("%H:%M"),
        "janela_fim": fecha.strftime("%H:%M"),
        "minutos_janela": int((fecha - abre).total_seconds() // 60),
        "salas": ocupacao.calcular(repo_salas.listar(conn), reservas, data),  # RN-08
    }
