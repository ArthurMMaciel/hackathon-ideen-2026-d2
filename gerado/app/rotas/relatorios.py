"""Relatório de ocupação por sala num dia."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.banco import obter_conexao
from app.dominio import ocupacao
from app.relogio import FUSO
from app.repositorio import reservas as repo
from app.repositorio import salas as repo_salas
from app.rotas.modelos import Ocupacao
from app.tipos import Data

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


@router.get("/ocupacao", response_model=Ocupacao)
def ocupacao_do_dia(dia: Annotated[Data, Query()], conn: sqlite3.Connection = Depends(obter_conexao)):
    inicio, fim = ocupacao.janela(dia, FUSO)
    ativas = repo.ativas_no_intervalo(conn, inicio, fim)  # RN-06: só ATIVAS
    return ocupacao.calcular(dia, FUSO, repo_salas.listar(conn), ativas)  # RN-08
