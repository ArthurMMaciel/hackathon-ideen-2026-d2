"""Rotas de turmas: cadastro, consulta, turmas futuras, inscritos e relatório de presença."""

import sqlite3
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app import banco
from app.banco import obter_conexao
from app.dominio import inscricoes as regras_inscricao
from app.dominio import relatorio as regras_relatorio
from app.dominio import turmas as regras_turma
from app.dominio.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import inscricoes as repo_inscricoes
from app.repositorio import turmas as repo_turmas
from app.rotas.modelos import InscricaoSaida, RelatorioPresencaSaida, TurmaEntrada, TurmaSaida
from app.tipos import Id

router = APIRouter(prefix="/api/turmas", tags=["turmas"])

Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]
Agora = Annotated[datetime, Depends(obter_agora)]


def saida_turma(turma: dict) -> TurmaSaida:
    return TurmaSaida(
        id=turma["id"], titulo=turma["titulo"], inicio=turma["inicio"],
        duracao_minutos=turma["duracao_minutos"], modalidade=turma["modalidade"], vagas=turma["vagas"],
        vagas_restantes=regras_turma.vagas_restantes(turma["vagas"], turma["ocupadas"]),
    )


def saida_inscricoes(lista: list[dict]) -> list[InscricaoSaida]:
    posicoes = regras_inscricao.posicoes_espera(lista)
    return [InscricaoSaida(**i, posicao_espera=posicoes.get(i["id"])) for i in lista]


def obter_turma(conn: sqlite3.Connection, turma_id: int) -> dict:
    turma = repo_turmas.buscar(conn, turma_id)
    if turma is None:
        raise nao_encontrado("TURMA_NAO_ENCONTRADA", "Turma não encontrada.")
    return turma


@router.post("", status_code=201, response_model=TurmaSaida)
def criar_turma(dados: TurmaEntrada, conn: Conexao, agora: Agora):
    regras_turma.validar_nova_turma(dados.inicio, dados.duracao_minutos, dados.vagas, agora)  # RN-01, RN-02
    with banco.transacao(conn):
        turma_id = repo_turmas.inserir(conn, dados.titulo, dados.inicio, dados.duracao_minutos,
                                       dados.modalidade, dados.vagas)
    return saida_turma(obter_turma(conn, turma_id))


@router.get("", response_model=list[TurmaSaida])
def listar_turmas_futuras(conn: Conexao, agora: Agora):
    # RF-09 / RN-14: só turmas com início depois de agora.
    return [saida_turma(t) for t in repo_turmas.listar_futuras(conn, agora)
            if regras_turma.eh_futura(t["inicio"], agora)]


@router.get("/{id}", response_model=TurmaSaida)
def consultar_turma(id: Annotated[Id, Path()], conn: Conexao):
    return saida_turma(obter_turma(conn, id))


@router.get("/{id}/inscricoes", response_model=list[InscricaoSaida])
def listar_inscritos(id: Annotated[Id, Path()], conn: Conexao):
    obter_turma(conn, id)
    return saida_inscricoes(repo_inscricoes.listar_da_turma(conn, id))


@router.get("/{id}/relatorio-presenca", response_model=RelatorioPresencaSaida)
def relatorio_presenca(id: Annotated[Id, Path()], conn: Conexao):
    obter_turma(conn, id)
    presentes, ausentes = repo_turmas.contar_presenca(conn, id)
    return RelatorioPresencaSaida(turma_id=id, presentes=presentes, ausentes=ausentes,
                                  taxa_presenca_percentual=regras_relatorio.taxa_presenca(presentes, ausentes))
