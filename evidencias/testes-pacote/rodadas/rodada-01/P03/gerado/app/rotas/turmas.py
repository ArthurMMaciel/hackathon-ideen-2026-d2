"""Rotas de turmas: cadastro, consulta, inscrição, inscritos e taxa de presença."""

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends

from app import banco
from app.banco import obter_conexao
from app.dominio import inscricoes as regras_inscricao
from app.dominio import relatorios
from app.dominio import turmas as regras_turma
from app.erros import nao_encontrado
from app.relogio import do_banco, obter_agora
from app.repositorio import inscricoes as repo_inscricoes
from app.repositorio import turmas as repo_turmas
from app.rotas.modelos import (
    Id,
    InscricaoEntrada,
    InscricaoSaida,
    TaxaPresencaSaida,
    TurmaEntrada,
    TurmaSaida,
    inscricao_saida,
    turma_saida,
)

router = APIRouter(prefix="/api/turmas", tags=["turmas"])


def _turma_ou_404(conn: sqlite3.Connection, turma_id: int) -> sqlite3.Row:
    linha = repo_turmas.buscar(conn, turma_id)
    if linha is None:
        raise nao_encontrado("TURMA_NAO_ENCONTRADA", f"Turma {turma_id} não encontrada.")
    return linha


@router.post("", status_code=201, response_model=TurmaSaida)
def criar_turma(
    entrada: TurmaEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    regras_turma.validar_inicio_futuro(entrada.inicio, agora)
    with banco.transacao(conn):
        turma_id = repo_turmas.inserir(
            conn, entrada.titulo, entrada.inicio, entrada.duracao_minutos, entrada.modalidade, entrada.vagas
        )
    return turma_saida(repo_turmas.buscar(conn, turma_id))


@router.get("", response_model=list[TurmaSaida])
def listar_turmas_futuras(
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    return [turma_saida(linha) for linha in repo_turmas.listar_futuras(conn, agora)]


@router.get("/{turma_id}", response_model=TurmaSaida)
def consultar_turma(turma_id: Id, conn: sqlite3.Connection = Depends(obter_conexao)):
    return turma_saida(_turma_ou_404(conn, turma_id))


@router.post("/{turma_id}/inscricoes", status_code=201, response_model=InscricaoSaida)
def inscrever(
    turma_id: Id,
    entrada: InscricaoEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        turma = _turma_ou_404(conn, turma_id)
        regras_inscricao.validar_prazo_inscricao(do_banco(turma["inicio"]), agora)
        regras_inscricao.validar_nao_duplicada(repo_inscricoes.existe_ativa(conn, turma_id, entrada.email))
        situacao = regras_inscricao.situacao_inicial(turma["vagas"], turma["ocupadas"])
        inscricao_id = repo_inscricoes.inserir(conn, turma_id, entrada.nome, entrada.email, situacao, agora)
    return inscricao_saida(repo_inscricoes.buscar(conn, inscricao_id), repo_inscricoes.ids_em_espera(conn, turma_id))


@router.get("/{turma_id}/inscricoes", response_model=list[InscricaoSaida])
def listar_inscritos(turma_id: Id, conn: sqlite3.Connection = Depends(obter_conexao)):
    _turma_ou_404(conn, turma_id)
    ids_espera = repo_inscricoes.ids_em_espera(conn, turma_id)
    return [inscricao_saida(linha, ids_espera) for linha in repo_inscricoes.listar_da_turma(conn, turma_id)]


@router.get("/{turma_id}/taxa-presenca", response_model=TaxaPresencaSaida)
def taxa_presenca(turma_id: Id, conn: sqlite3.Connection = Depends(obter_conexao)):
    _turma_ou_404(conn, turma_id)
    presentes, ausentes = repo_inscricoes.contar_presenca(conn, turma_id)
    return TaxaPresencaSaida(
        turma_id=turma_id,
        presentes=presentes,
        ausentes=ausentes,
        taxa_presenca=relatorios.taxa_presenca(presentes, ausentes),
    )
