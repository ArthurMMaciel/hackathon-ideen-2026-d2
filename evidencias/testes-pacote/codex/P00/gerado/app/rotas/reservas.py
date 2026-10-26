from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel

from app.banco import obter_conexao, transacao
from app.dominio import reservas as regras
from app.dominio.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import reservas as repo, salas as repo_salas
from app.tipos import Data, DataHora, Email, Id, Texto

router = APIRouter(prefix="/api/reservas", tags=["reservas"])


class ReservaEntrada(BaseModel):
    sala_id: Id
    responsavel_nome: Texto
    responsavel_email: Email
    titulo: Texto
    participantes: Id
    inicio: DataHora
    fim: DataHora


@router.get("")
def listar(sala_id: Annotated[Id | None, Query()] = None,
           dia: Annotated[Data | None, Query()] = None,
           conn=Depends(obter_conexao)):
    return repo.listar(conn, sala_id, dia)


@router.get("/{id}")
def obter(id: Annotated[Id, Path()], conn=Depends(obter_conexao)):
    reserva = repo.obter(conn, id)
    if reserva is None:
        raise nao_encontrado("RESERVA_NAO_ENCONTRADA", "Reserva não encontrada.")
    return reserva


@router.post("", status_code=201)
def criar(dados: ReservaEntrada, conn=Depends(obter_conexao), agora=Depends(obter_agora)):
    regras.validar_duracao(dados.inicio, dados.fim)
    regras.validar_inicio(dados.inicio, agora)
    with transacao(conn):
        sala = repo_salas.obter(conn, dados.sala_id)
        if sala is None:
            raise nao_encontrado("SALA_NAO_ENCONTRADA", "Sala não encontrada.")
        regras.validar_participantes(dados.participantes, sala["capacidade"])
        regras.verificar_conflito(repo.tem_conflito(conn, dados.sala_id, dados.inicio, dados.fim))
        return repo.inserir(conn, dados)


@router.post("/{id}/cancelar")
def cancelar(id: Annotated[Id, Path()], conn=Depends(obter_conexao), agora=Depends(obter_agora)):
    with transacao(conn):
        reserva = repo.obter(conn, id)
        if reserva is None:
            raise nao_encontrado("RESERVA_NAO_ENCONTRADA", "Reserva não encontrada.")
        from datetime import datetime
        regras.validar_cancelamento(reserva["status"], datetime.fromisoformat(reserva["inicio"]), agora)
        return repo.cancelar(conn, id)
