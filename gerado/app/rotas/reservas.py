"""Rotas de reservas: criar, agenda do dia e cancelar."""

import sqlite3
from datetime import datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app import banco
from app.banco import obter_conexao
from app.dominio import reservas as regras
from app.dominio.erros import nao_encontrado
from app.relogio import FUSO, obter_agora
from app.repositorio import reservas as repo
from app.repositorio import salas as repo_salas
from app.rotas.modelos import Reserva, ReservaEntrada
from app.tipos import Data, Id

router = APIRouter(prefix="/api/reservas", tags=["reservas"])


def _sala_ou_404(conn: sqlite3.Connection, sala_id: int) -> dict:
    sala = repo_salas.obter(conn, sala_id)
    if sala is None:
        raise nao_encontrado("SALA_NAO_ENCONTRADA", "Sala não encontrada.")
    return sala


@router.post("", response_model=Reserva, status_code=201)
def criar(
    dados: ReservaEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        sala = _sala_ou_404(conn, dados.sala_id)
        regras.validar_duracao(dados.inicio, dados.fim)  # RN-02
        regras.validar_inicio(dados.inicio, agora)  # RN-03
        regras.validar_participantes(dados.participantes, sala["capacidade"])  # RN-04
        existentes = repo.ativas_sobrepostas(conn, sala["id"], dados.inicio, dados.fim)
        regras.verificar_conflito(dados.inicio, dados.fim, existentes)  # RN-01
        reserva_id = repo.inserir(conn, dados.model_dump(), agora)
    return repo.obter(conn, reserva_id)


@router.get("", response_model=list[Reserva])
def agenda_do_dia(
    dia: Annotated[Data, Query()],
    sala_id: Annotated[Id | None, Query()] = None,
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    # PR-06: reservas (ATIVAS e CANCELADAS) que tocam o dia de calendário no fuso padrão.
    if sala_id is not None:
        _sala_ou_404(conn, sala_id)
    inicio = datetime.combine(dia, time(0, 0), FUSO)
    fim = datetime.combine(dia + timedelta(days=1), time(0, 0), FUSO)
    return repo.no_intervalo(conn, inicio, fim, sala_id)


@router.post("/{id}/cancelar", response_model=Reserva)
def cancelar(
    id: Annotated[Id, Path()],
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        reserva = repo.obter(conn, id)
        if reserva is None:
            raise nao_encontrado("RESERVA_NAO_ENCONTRADA", "Reserva não encontrada.")
        regras.validar_cancelamento(reserva["status"], reserva["inicio"], agora)  # RN-05
        repo.cancelar(conn, id, agora)  # RN-06: muda o status, não apaga
    return repo.obter(conn, id)
