"""Rotas de inscrições: cancelamento e presença."""

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends

from app import banco
from app.banco import obter_conexao
from app.dominio import inscricoes as regras
from app.erros import nao_encontrado
from app.relogio import do_banco, obter_agora
from app.repositorio import inscricoes as repo_inscricoes
from app.repositorio import turmas as repo_turmas
from app.rotas.modelos import CancelamentoSaida, Id, InscricaoSaida, PresencaEntrada, inscricao_saida

router = APIRouter(prefix="/api/inscricoes", tags=["inscricoes"])


def _inscricao_ou_404(conn: sqlite3.Connection, inscricao_id: int) -> sqlite3.Row:
    linha = repo_inscricoes.buscar(conn, inscricao_id)
    if linha is None:
        raise nao_encontrado("INSCRICAO_NAO_ENCONTRADA", f"Inscrição {inscricao_id} não encontrada.")
    return linha


@router.post("/{inscricao_id}/cancelar", response_model=CancelamentoSaida)
def cancelar(
    inscricao_id: Id,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    promovida_id = None
    with banco.transacao(conn):
        inscricao = _inscricao_ou_404(conn, inscricao_id)
        turma = repo_turmas.buscar(conn, inscricao["turma_id"])
        regras.validar_cancelamento(inscricao["situacao"], do_banco(turma["inicio"]), agora)
        repo_inscricoes.atualizar_situacao(conn, inscricao_id, regras.CANCELADA)
        if regras.promove_espera(inscricao["situacao"]):
            fila = repo_inscricoes.ids_em_espera(conn, inscricao["turma_id"])
            if fila:
                # RN-10: a primeira da espera passa a CONFIRMADA
                promovida_id = fila[0]
                repo_inscricoes.atualizar_situacao(conn, promovida_id, regras.CONFIRMADA)
    ids_espera = repo_inscricoes.ids_em_espera(conn, inscricao["turma_id"])
    promovida = None
    if promovida_id is not None:
        promovida = inscricao_saida(repo_inscricoes.buscar(conn, promovida_id), ids_espera)
    return CancelamentoSaida(
        cancelada=inscricao_saida(repo_inscricoes.buscar(conn, inscricao_id), ids_espera),
        promovida=promovida,
    )


@router.post("/{inscricao_id}/presenca", response_model=InscricaoSaida)
def marcar_presenca(
    inscricao_id: Id,
    entrada: PresencaEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        inscricao = _inscricao_ou_404(conn, inscricao_id)
        turma = repo_turmas.buscar(conn, inscricao["turma_id"])
        regras.validar_presenca(inscricao["situacao"], do_banco(turma["inicio"]), agora)
        repo_inscricoes.atualizar_situacao(conn, inscricao_id, entrada.situacao)
    return inscricao_saida(repo_inscricoes.buscar(conn, inscricao_id), [])
