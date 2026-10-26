"""Rotas de reservas: criar, consultar, agenda do dia e cancelar."""

import sqlite3
from typing import Annotated
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, Path, Query

from app import banco
from app.banco import obter_conexao
from app.dominio import reservas as regras
from app.erros import nao_encontrado
from app.relogio import FUSO, obter_agora
from app.repositorio import reservas as repo
from app.repositorio import salas as repo_salas
from app.rotas.modelos import ID_MAXIMO, Data, ReservaEntrada, ReservaSaida

router = APIRouter(prefix="/api/reservas", tags=["reservas"])


def _obter_ou_404(conn: sqlite3.Connection, reserva_id: int) -> dict:
    reserva = repo.obter(conn, reserva_id)
    if reserva is None:
        raise nao_encontrado("RESERVA_NAO_ENCONTRADA", "Reserva não encontrada.")
    return reserva


@router.post("", response_model=ReservaSaida, status_code=201)
def criar(
    entrada: ReservaEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    regras.validar_intervalo(entrada.inicio, entrada.fim)  # RN-09
    regras.validar_duracao(entrada.inicio, entrada.fim)  # RN-02
    regras.validar_inicio_futuro(entrada.inicio, agora)  # RN-03
    with banco.transacao(conn):
        sala = repo_salas.obter(conn, entrada.sala_id)
        if sala is None:
            raise nao_encontrado("SALA_NAO_ENCONTRADA", "Sala não encontrada.")
        regras.validar_participantes(entrada.participantes, sala["capacidade"])  # RN-04
        existentes = repo.da_sala_no_intervalo(conn, entrada.sala_id, entrada.inicio, entrada.fim)
        regras.verificar_conflito(existentes, entrada.inicio, entrada.fim)  # RN-01
        reserva_id = repo.inserir(conn, entrada.model_dump(), agora)
    return repo.obter(conn, reserva_id)


@router.get("", response_model=list[ReservaSaida])
def agenda_do_dia(
    data: Annotated[Data, Query()],
    sala_id: int | None = Query(None, ge=1, le=ID_MAXIMO),
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    # RF-08 e PR-04: dia civil no fuso padrão; inclui canceladas.
    inicio_dia = datetime.combine(data, time(0, 0), FUSO)
    fim_dia = datetime.combine(data + timedelta(days=1), time(0, 0), FUSO)
    return repo.no_intervalo(conn, inicio_dia, fim_dia, sala_id)


@router.get("/{reserva_id}", response_model=ReservaSaida)
def obter(reserva_id: int = Path(ge=1, le=ID_MAXIMO), conn: sqlite3.Connection = Depends(obter_conexao)):
    return _obter_ou_404(conn, reserva_id)


@router.post("/{reserva_id}/cancelar", response_model=ReservaSaida)
def cancelar(
    reserva_id: int = Path(ge=1, le=ID_MAXIMO),
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        reserva = _obter_ou_404(conn, reserva_id)
        regras.validar_cancelamento(reserva["status"], reserva["inicio"], agora)  # RN-05
        repo.cancelar(conn, reserva_id, agora)
    return repo.obter(conn, reserva_id)
