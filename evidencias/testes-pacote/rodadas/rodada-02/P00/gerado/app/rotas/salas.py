"""Rotas de salas: cadastro, listagem, consulta e salas livres."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app import banco
from app.banco import obter_conexao
from app.dominio import salas as regras
from app.dominio.erros import nao_encontrado
from app.repositorio import reservas as repo_reservas
from app.repositorio import salas as repo
from app.rotas.modelos import Capacidade, HorarioReserva, Local, Sala, SalaEntrada
from app.tipos import Id

router = APIRouter(prefix="/api/salas", tags=["salas"])


@router.get("", response_model=list[Sala])
def listar(conn: sqlite3.Connection = Depends(obter_conexao)):
    return repo.listar(conn)


@router.get("/livres", response_model=list[Sala])
def livres(
    inicio: Annotated[HorarioReserva, Query()],
    fim: Annotated[HorarioReserva, Query()],
    local: Annotated[Local | None, Query()] = None,
    capacidade_minima: Annotated[Capacidade | None, Query()] = None,
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    regras.validar_intervalo_consulta(inicio, fim)  # RN-07
    ocupadas = repo_reservas.salas_ocupadas(conn, inicio, fim)
    return regras.filtrar_livres(repo.listar(conn), ocupadas, local, capacidade_minima)


@router.get("/{id}", response_model=Sala)
def obter(id: Annotated[Id, Path()], conn: sqlite3.Connection = Depends(obter_conexao)):
    sala = repo.obter(conn, id)
    if sala is None:
        raise nao_encontrado("SALA_NAO_ENCONTRADA", "Sala não encontrada.")
    return sala


@router.post("", response_model=Sala, status_code=201)
def cadastrar(dados: SalaEntrada, conn: sqlite3.Connection = Depends(obter_conexao)):
    recursos = regras.normalizar_recursos(list(dados.recursos))  # RN-09
    with banco.transacao(conn):
        regras.verificar_nome_unico(dados.nome, dados.local, repo.nomes_do_local(conn, dados.local))  # RN-10
        sala_id = repo.inserir(conn, dados.nome, dados.local, dados.capacidade, recursos)
    return repo.obter(conn, sala_id)
