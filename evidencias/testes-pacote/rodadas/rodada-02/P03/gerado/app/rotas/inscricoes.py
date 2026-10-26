"""Rotas de inscrições: inscrever, cancelar (com promoção da espera) e marcar presença."""

import sqlite3
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app import banco
from app.banco import obter_conexao
from app.dominio import inscricoes as regras
from app.dominio.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import inscricoes as repo_inscricoes
from app.rotas.modelos import CancelamentoSaida, InscricaoEntrada, InscricaoSaida, PresencaEntrada
from app.rotas.turmas import obter_turma, saida_inscricoes
from app.tipos import Id

router = APIRouter(prefix="/api/inscricoes", tags=["inscricoes"])

Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]
Agora = Annotated[datetime, Depends(obter_agora)]


def obter_inscricao(conn: sqlite3.Connection, inscricao_id: int) -> dict:
    inscricao = repo_inscricoes.buscar(conn, inscricao_id)
    if inscricao is None:
        raise nao_encontrado("INSCRICAO_NAO_ENCONTRADA", "Inscrição não encontrada.")
    return inscricao


def saida_por_id(conn: sqlite3.Connection, turma_id: int, inscricao_id: int) -> InscricaoSaida:
    """Monta a saída com a posição na espera, que depende das outras inscrições da turma."""
    for item in saida_inscricoes(repo_inscricoes.listar_da_turma(conn, turma_id)):
        if item.id == inscricao_id:
            return item
    raise nao_encontrado("INSCRICAO_NAO_ENCONTRADA", "Inscrição não encontrada.")


@router.post("", status_code=201, response_model=InscricaoSaida)
def inscrever(dados: InscricaoEntrada, conn: Conexao, agora: Agora):
    email = regras.normalizar_email(dados.email)
    with banco.transacao(conn):
        turma = obter_turma(conn, dados.turma_id)
        regras.validar_janela_inscricao(turma["inicio"], agora)  # RN-06
        regras.validar_email_unico(repo_inscricoes.existe_ativa(conn, turma["id"], email))  # RN-05
        situacao = regras.situacao_inicial(turma["vagas"], turma["ocupadas"])  # RN-03
        inscricao_id = repo_inscricoes.inserir(conn, turma["id"], dados.nome, email, situacao, agora)
    return saida_por_id(conn, turma["id"], inscricao_id)


@router.post("/{id}/cancelar", response_model=CancelamentoSaida)
def cancelar(id: Annotated[Id, Path()], conn: Conexao, agora: Agora):
    with banco.transacao(conn):
        inscricao = obter_inscricao(conn, id)
        turma = obter_turma(conn, inscricao["turma_id"])
        regras.validar_cancelamento(inscricao["situacao"], turma["inicio"], agora)  # RN-07, RN-08
        repo_inscricoes.atualizar_situacao(conn, id, "CANCELADA", agora)
        promovida = None
        if regras.deve_promover(inscricao["situacao"]):  # RN-09
            promovida = regras.primeira_da_espera(repo_inscricoes.listar_da_turma(conn, turma["id"]))  # RN-04
            if promovida is not None:
                repo_inscricoes.atualizar_situacao(conn, promovida["id"], "CONFIRMADA", agora)
    return CancelamentoSaida(
        inscricao=saida_por_id(conn, turma["id"], id),
        promovida=saida_por_id(conn, turma["id"], promovida["id"]) if promovida else None,
    )


@router.post("/{id}/presenca", response_model=InscricaoSaida)
def marcar_presenca(id: Annotated[Id, Path()], dados: PresencaEntrada, conn: Conexao, agora: Agora):
    with banco.transacao(conn):
        inscricao = obter_inscricao(conn, id)
        turma = obter_turma(conn, inscricao["turma_id"])
        regras.validar_presenca(inscricao["situacao"], turma["inicio"], agora)  # RN-10, RN-11
        repo_inscricoes.atualizar_situacao(conn, id, dados.situacao, agora)
    return saida_por_id(conn, turma["id"], id)
