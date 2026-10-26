"""Rotas de salas: cadastro, consulta e salas livres."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app import banco
from app.banco import obter_conexao
from app.dominio import reservas as regras_reservas
from app.dominio import salas as regras_salas
from app.erros import nao_encontrado
from app.repositorio import reservas as repo_reservas
from app.repositorio import salas as repo_salas
from app.rotas.modelos import ID_MAXIMO, DataHora, Local, SalaEntrada, SalaSaida

router = APIRouter(prefix="/api/salas", tags=["salas"])


@router.get("", response_model=list[SalaSaida])
def listar(conn: sqlite3.Connection = Depends(obter_conexao)):
    return repo_salas.listar(conn)


# Declarada antes de /{sala_id} para não colidir.
@router.get("/livres", response_model=list[SalaSaida])
def livres(
    inicio: Annotated[DataHora, Query()],
    fim: Annotated[DataHora, Query()],
    local: Local | None = Query(None),
    capacidade_minima: int | None = Query(None, ge=1, le=500),
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    regras_reservas.validar_intervalo(inicio, fim)  # RN-09
    ocupadas = {
        r["sala_id"]
        for r in repo_reservas.no_intervalo(conn, inicio, fim)
        if regras_reservas.bloqueia_horario(r["status"])  # RN-06
    }
    return regras_salas.filtrar_livres(repo_salas.listar(conn), ocupadas, local, capacidade_minima)  # RN-07


@router.get("/{sala_id}", response_model=SalaSaida)
def obter(sala_id: int = Path(ge=1, le=ID_MAXIMO), conn: sqlite3.Connection = Depends(obter_conexao)):
    sala = repo_salas.obter(conn, sala_id)
    if sala is None:
        raise nao_encontrado("SALA_NAO_ENCONTRADA", "Sala não encontrada.")
    return sala


@router.post("", response_model=SalaSaida, status_code=201)
def criar(entrada: SalaEntrada, conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        regras_salas.validar_nome_unico(repo_salas.nome_existe(conn, entrada.nome), entrada.nome)  # RN-10
        sala_id = repo_salas.inserir(conn, entrada.nome, entrada.local, entrada.capacidade, entrada.recursos)
    return repo_salas.obter(conn, sala_id)
