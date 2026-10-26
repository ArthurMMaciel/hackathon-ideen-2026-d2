from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.banco import obter_conexao, transacao
from app.dominio import reservas as regras_reservas, salas as regras_salas
from app.repositorio import salas as repo
from app.tipos import DataHora, Id, Texto

router = APIRouter(prefix="/api/salas", tags=["salas"])


class Local(str, Enum):
    SAO_PAULO = "SAO_PAULO"
    ARARAQUARA = "ARARAQUARA"
    COWORKING = "COWORKING"


class Recurso(str, Enum):
    TV = "TV"
    VIDEOCONFERENCIA = "VIDEOCONFERENCIA"
    QUADRO = "QUADRO"


class SalaEntrada(BaseModel):
    nome: Texto
    local: Local
    capacidade: Id
    recursos: list[Recurso]


@router.get("")
def listar(conn=Depends(obter_conexao)):
    return repo.listar(conn)


@router.get("/livres")
def livres(inicio: Annotated[DataHora, Query()], fim: Annotated[DataHora, Query()],
           local: Annotated[Local | None, Query()] = None,
           capacidade_minima: Annotated[Id | None, Query()] = None,
           conn=Depends(obter_conexao)):
    regras_reservas.validar_intervalo(inicio, fim)
    return repo.livres(conn, inicio, fim, local, capacidade_minima or 1)


@router.post("", status_code=201)
def criar(dados: SalaEntrada, conn=Depends(obter_conexao)):
    regras_salas.validar_sala(dados.capacidade, dados.recursos)
    with transacao(conn):
        return repo.inserir(conn, dados)
