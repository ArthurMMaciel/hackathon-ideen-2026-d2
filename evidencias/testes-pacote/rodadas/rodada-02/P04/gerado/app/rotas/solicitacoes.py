"""RF-04 a RF-08: solicitar, listar, consultar, aprovar, reprovar e cancelar férias."""

import sqlite3
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from app import banco
from app.banco import obter_conexao
from app.dominio import ferias
from app.dominio.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import ferias as repo
from app.rotas.colaboradores import buscar_colaborador
from app.tipos import Data, Id

router = APIRouter(prefix="/api/solicitacoes", tags=["solicitacoes"])


class SolicitacaoEntrada(BaseModel):
    colaborador_id: Id
    inicio: Data
    fim: Data


class SolicitacaoSaida(BaseModel):
    id: int
    colaborador_id: int
    colaborador_nome: str
    equipe: str
    inicio: str
    fim: str
    dias: int
    situacao: str


def buscar_solicitacao(conn: sqlite3.Connection, solicitacao_id: int) -> dict:
    solicitacao = repo.obter_solicitacao(conn, solicitacao_id)
    if solicitacao is None:
        raise nao_encontrado("SOLICITACAO_NAO_ENCONTRADA", "Solicitação não encontrada.")
    return solicitacao


def periodo(s: dict) -> tuple[date, date]:
    return date.fromisoformat(s["inicio"]), date.fromisoformat(s["fim"])


@router.post("", status_code=201, response_model=SolicitacaoSaida)
def solicitar(
    dados: SolicitacaoEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        colaborador = buscar_colaborador(conn, dados.colaborador_id)
        dias = ferias.calcular_dias(dados.inicio, dados.fim)  # RN-01
        ferias.validar_duracao(dias)  # RN-02
        ferias.validar_antecedencia(dados.inicio, agora)  # RN-03
        ferias.validar_sem_sobreposicao(  # RN-05
            dados.inicio, dados.fim, repo.periodos_ativos_do_colaborador(conn, colaborador["id"])
        )
        ferias.validar_saldo(dias, colaborador["saldo"], repo.dias_pendentes(conn, colaborador["id"]))  # RN-04
        novo_id = repo.inserir_solicitacao(conn, colaborador["id"], dados.inicio, dados.fim, dias, agora)
    return repo.obter_solicitacao(conn, novo_id)


@router.get("", response_model=list[SolicitacaoSaida])
def listar(conn: sqlite3.Connection = Depends(obter_conexao)):
    return repo.listar_solicitacoes(conn)


@router.get("/{id}", response_model=SolicitacaoSaida)
def consultar(id: Annotated[Id, Path()], conn: sqlite3.Connection = Depends(obter_conexao)):
    return buscar_solicitacao(conn, id)


@router.post("/{id}/aprovar", response_model=SolicitacaoSaida)
def aprovar(id: Annotated[Id, Path()], conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        s = buscar_solicitacao(conn, id)
        ferias.validar_decisao(s["situacao"])  # RN-06
        inicio, fim = periodo(s)
        ferias.validar_limite_equipe(inicio, fim, repo.aprovadas_da_equipe(conn, s["equipe"], s["id"]))  # RN-07
        colaborador = buscar_colaborador(conn, s["colaborador_id"])
        repo.atualizar_saldo(conn, colaborador["id"], ferias.saldo_apos_aprovacao(colaborador["saldo"], s["dias"]))  # RN-08
        repo.atualizar_situacao(conn, s["id"], ferias.APROVADA)
    return repo.obter_solicitacao(conn, id)


@router.post("/{id}/reprovar", response_model=SolicitacaoSaida)
def reprovar(id: Annotated[Id, Path()], conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        s = buscar_solicitacao(conn, id)
        ferias.validar_decisao(s["situacao"])  # RN-06
        repo.atualizar_situacao(conn, s["id"], ferias.REPROVADA)
    return repo.obter_solicitacao(conn, id)


@router.post("/{id}/cancelar", response_model=SolicitacaoSaida)
def cancelar(
    id: Annotated[Id, Path()],
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        s = buscar_solicitacao(conn, id)
        inicio, _ = periodo(s)
        ferias.validar_cancelamento(s["situacao"], inicio, agora)  # RN-09
        colaborador = buscar_colaborador(conn, s["colaborador_id"])
        novo_saldo = ferias.saldo_apos_cancelamento(colaborador["saldo"], s["dias"], s["situacao"])  # RN-10
        repo.atualizar_saldo(conn, colaborador["id"], novo_saldo)
        repo.atualizar_situacao(conn, s["id"], ferias.CANCELADA)
    return repo.obter_solicitacao(conn, id)
