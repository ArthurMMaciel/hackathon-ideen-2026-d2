"""Rotas de solicitações de férias (RF-04..RF-08) e calendário (RF-09)."""

import re
import sqlite3
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field, field_validator

from app import banco
from app.banco import obter_conexao
from app.dominio import ferias
from app.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import ferias as repo
from app.rotas.colaboradores import ID_MAXIMO, Equipe, buscar_colaborador

router = APIRouter(tags=["solicitacoes"])

Situacao = Literal["SOLICITADA", "APROVADA", "REPROVADA", "CANCELADA"]


class SolicitacaoEntrada(BaseModel):
    colaborador_id: int = Field(ge=1, le=ID_MAXIMO)
    inicio: date
    fim: date

    @field_validator("inicio", "fim", mode="before")
    @classmethod
    def so_data(cls, valor):
        # PR-02: só aceita "AAAA-MM-DD"; recusa data com hora ou outro formato.
        if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
            raise ValueError("use o formato AAAA-MM-DD")
        return valor


class SolicitacaoSaida(BaseModel):
    id: int
    colaborador_id: int
    colaborador_nome: str
    equipe: Equipe
    inicio: date
    fim: date
    dias: int
    situacao: Situacao
    criado_em: datetime


class PessoaNoDia(BaseModel):
    colaborador_id: int
    nome: str
    solicitacao_id: int


class DiaCalendario(BaseModel):
    data: date
    equipes: dict[Equipe, list[PessoaNoDia]]


class Calendario(BaseModel):
    mes: str
    dias: list[DiaCalendario]


def _buscar(conn: sqlite3.Connection, solicitacao_id: int) -> dict:
    s = repo.obter_solicitacao(conn, solicitacao_id)
    if s is None:
        raise nao_encontrado("SOLICITACAO_NAO_ENCONTRADA", f"Solicitação {solicitacao_id} não encontrada.")
    return s


def _periodo(s: dict) -> ferias.Periodo:
    return ferias.Periodo(date.fromisoformat(s["inicio"]), date.fromisoformat(s["fim"]))


@router.get("/api/solicitacoes", response_model=list[SolicitacaoSaida])
def listar(
    situacao: Situacao | None = None,
    colaborador_id: int | None = Query(default=None, ge=1, le=ID_MAXIMO),
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    return repo.listar_solicitacoes(conn, situacao, colaborador_id)


@router.post("/api/solicitacoes", response_model=SolicitacaoSaida, status_code=201)
def solicitar(
    entrada: SolicitacaoEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    periodo = ferias.Periodo(entrada.inicio, entrada.fim)
    dias = ferias.contar_dias(periodo)
    ferias.validar_duracao(dias)
    ferias.validar_antecedencia(periodo.inicio, agora.date())
    with banco.transacao(conn):
        colaborador = buscar_colaborador(conn, entrada.colaborador_id)
        ferias.validar_saldo(dias, colaborador["saldo_disponivel"])
        ferias.validar_sem_sobreposicao_colaborador(
            periodo, repo.periodos_ativos_do_colaborador(conn, entrada.colaborador_id)
        )
        novo_id = repo.inserir_solicitacao(conn, entrada.colaborador_id, periodo, dias, agora)
    return _buscar(conn, novo_id)


@router.post("/api/solicitacoes/{solicitacao_id}/aprovar", response_model=SolicitacaoSaida)
def aprovar(solicitacao_id: int = Path(ge=1, le=ID_MAXIMO), conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        s = _buscar(conn, solicitacao_id)
        ferias.validar_pode_decidir(s["situacao"])
        ferias.validar_limite_equipe(_periodo(s), repo.periodos_aprovados_da_equipe(conn, s["equipe"], s["id"]))
        colaborador = buscar_colaborador(conn, s["colaborador_id"])
        repo.atualizar_saldo(conn, s["colaborador_id"], ferias.saldo_apos_aprovar(colaborador["saldo"], s["dias"]))
        repo.atualizar_situacao(conn, s["id"], "APROVADA")
    return _buscar(conn, solicitacao_id)


@router.post("/api/solicitacoes/{solicitacao_id}/reprovar", response_model=SolicitacaoSaida)
def reprovar(solicitacao_id: int = Path(ge=1, le=ID_MAXIMO), conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        s = _buscar(conn, solicitacao_id)
        ferias.validar_pode_decidir(s["situacao"])
        repo.atualizar_situacao(conn, s["id"], "REPROVADA")
    return _buscar(conn, solicitacao_id)


@router.post("/api/solicitacoes/{solicitacao_id}/cancelar", response_model=SolicitacaoSaida)
def cancelar(
    solicitacao_id: int = Path(ge=1, le=ID_MAXIMO),
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        s = _buscar(conn, solicitacao_id)
        ferias.validar_cancelamento(s["situacao"], date.fromisoformat(s["inicio"]), agora.date())
        colaborador = buscar_colaborador(conn, s["colaborador_id"])
        repo.atualizar_saldo(
            conn, s["colaborador_id"], ferias.saldo_apos_cancelar(colaborador["saldo"], s["situacao"], s["dias"])
        )
        repo.atualizar_situacao(conn, s["id"], "CANCELADA")
    return _buscar(conn, solicitacao_id)


@router.get("/api/calendario", response_model=Calendario)
def calendario(mes: str = Query(max_length=7), conn: sqlite3.Connection = Depends(obter_conexao)):
    primeiro, ultimo = ferias.interpretar_mes(mes)
    aprovadas = repo.aprovadas_no_intervalo(conn, primeiro, ultimo)
    return {"mes": mes, "dias": ferias.montar_calendario(primeiro, ultimo, aprovadas)}
