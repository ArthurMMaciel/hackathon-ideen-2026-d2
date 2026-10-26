"""Rotas de chamados, fila e relatório."""

import sqlite3
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import BaseModel, StringConstraints

from app import banco
from app.banco import obter_conexao
from app.dominio import chamados as dominio
from app.dominio import relatorio as dominio_relatorio
from app.dominio.erros import nao_encontrado
from app.relogio import FUSO, obter_agora
from app.repositorio import chamados as repo
from app.tipos import Data, Email, Id, Texto, TextoLongo

router = APIRouter(prefix="/api")

Categoria = Literal["ACESSO", "HARDWARE", "SOFTWARE"]
Prioridade = Literal["BAIXA", "MEDIA", "ALTA", "CRITICA"]
Situacao = Literal["ABERTO", "EM_ATENDIMENTO", "RESOLVIDO", "FECHADO"]

# Opcionais no modelo e conferidos no domínio, para a recusa sair com código de negócio (RN-04, RN-05).
NomeOpcional = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
SolucaoOpcional = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class ChamadoEntrada(BaseModel):
    titulo: Texto
    descricao: TextoLongo
    solicitante_nome: Texto
    solicitante_email: Email
    categoria: Categoria
    prioridade: Prioridade


class AssumirEntrada(BaseModel):
    responsavel: NomeOpcional | None = None


class ResolverEntrada(BaseModel):
    solucao: SolucaoOpcional | None = None


class ChamadoSaida(BaseModel):
    id: int
    titulo: str
    descricao: str
    solicitante_nome: str
    solicitante_email: str
    categoria: Categoria
    prioridade: Prioridade
    situacao: Situacao
    aberto_em: datetime
    prazo_em: datetime
    responsavel: str | None
    solucao: str | None
    resolvido_em: datetime | None


class ItemFila(ChamadoSaida):
    indicacao: Literal["ATRASADO", "NO_PRAZO"]


class LinhaRelatorio(BaseModel):
    prioridade: Prioridade
    resolvidos: int
    dentro_do_prazo: int
    percentual_dentro_do_prazo: float | None


class RelatorioSaida(BaseModel):
    data_inicial: str
    data_final: str
    prioridades: list[LinhaRelatorio]


Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]
Agora = Annotated[datetime, Depends(obter_agora)]
IdChamado = Annotated[Id, Path()]


def _buscar_ou_404(conn: sqlite3.Connection, id_: int) -> dict:
    chamado = repo.buscar(conn, id_)
    if chamado is None:
        raise nao_encontrado("CHAMADO_NAO_ENCONTRADO", f"Chamado {id_} não encontrado.")
    return chamado


def _mudar_situacao(conn: sqlite3.Connection, id_: int, transicao) -> dict:
    # Conferir a situação e gravar na mesma transação (BEGIN IMMEDIATE).
    with banco.transacao(conn):
        chamado = _buscar_ou_404(conn, id_)
        novo = transicao(chamado)
        repo.atualizar_situacao(conn, novo)
    return repo.buscar(conn, id_)


@router.post("/chamados", status_code=201, response_model=ChamadoSaida)
def abrir_chamado(dados: ChamadoEntrada, conn: Conexao, agora: Agora):
    chamado = {
        **dados.model_dump(),
        "situacao": "ABERTO",
        "aberto_em": agora,
        "prazo_em": dominio.calcular_prazo(dados.prioridade, agora),  # RN-01
    }
    with banco.transacao(conn):
        id_ = repo.inserir(conn, chamado)
    return repo.buscar(conn, id_)


@router.get("/chamados", response_model=list[ChamadoSaida])
def listar_chamados(conn: Conexao):
    return repo.listar(conn)


@router.get("/chamados/{id}", response_model=ChamadoSaida)
def consultar_chamado(id: IdChamado, conn: Conexao):
    return _buscar_ou_404(conn, id)


@router.post("/chamados/{id}/assumir", response_model=ChamadoSaida)
def assumir_chamado(id: IdChamado, conn: Conexao, dados: Annotated[AssumirEntrada | None, Body()] = None):
    responsavel = dados.responsavel if dados else None
    return _mudar_situacao(conn, id, lambda c: dominio.assumir(c, responsavel))


@router.post("/chamados/{id}/resolver", response_model=ChamadoSaida)
def resolver_chamado(
    id: IdChamado, conn: Conexao, agora: Agora, dados: Annotated[ResolverEntrada | None, Body()] = None
):
    solucao = dados.solucao if dados else None
    return _mudar_situacao(conn, id, lambda c: dominio.resolver(c, solucao, agora))


@router.post("/chamados/{id}/fechar", response_model=ChamadoSaida)
def fechar_chamado(id: IdChamado, conn: Conexao):
    return _mudar_situacao(conn, id, dominio.fechar)


@router.post("/chamados/{id}/reabrir", response_model=ChamadoSaida)
def reabrir_chamado(id: IdChamado, conn: Conexao, agora: Agora):
    return _mudar_situacao(conn, id, lambda c: dominio.reabrir(c, agora))


@router.get("/fila", response_model=list[ItemFila])
def consultar_fila(conn: Conexao, agora: Agora):
    return [{**c, "indicacao": dominio.indicacao_fila(c["prazo_em"], agora)} for c in repo.fila(conn)]


@router.get("/relatorio", response_model=RelatorioSaida)
def emitir_relatorio(
    data_inicial: Annotated[Data, Query()], data_final: Annotated[Data, Query()], conn: Conexao
):
    dominio_relatorio.validar_periodo(data_inicial, data_final)
    inicio, fim = dominio_relatorio.limites_periodo(data_inicial, data_final, FUSO)
    resolvidos = repo.resolvidos_no_periodo(conn, inicio, fim)
    return {
        "data_inicial": data_inicial.isoformat(),
        "data_final": data_final.isoformat(),
        "prioridades": dominio_relatorio.montar_relatorio(resolvidos),
    }
